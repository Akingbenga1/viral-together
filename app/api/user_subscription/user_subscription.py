from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload, joinedload, Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List, Optional
from datetime import datetime
import stripe
import os
from uuid import UUID
import logging

from app.api.auth import get_current_user
from app.api.user_subscription.user_subscription_models import (
    UserSubscriptionRead,
    CreateCheckoutSessionRequest, CheckoutSessionResponse,
    CreatePortalSessionRequest, PortalSessionResponse, WebhookEvent
)
from app.db.models.subscription import SubscriptionPlan
from app.db.models.user_subscription import UserSubscription
from app.db.models.user import User as UserModel
from app.db.session import get_db
from app.core.query_helpers import safe_scalar_one_or_none
from app.schemas import User
from app.schemas.user import UserRead



# Configure logging
logger = logging.getLogger(__name__)


# Set up Stripe API key

stripe.api_key = os.getenv("STRIPE_API_KEY")
stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

logger.info(f"STRIPE_API_KEY: {os.getenv('STRIPE_API_KEY')}")
logger.info(f"STRIPE_WEBHOOK_SECRET: {os.getenv('STRIPE_WEBHOOK_SECRET')}")


router = APIRouter()

# User subscription endpoints
@router.post("/checkout", response_model=dict)
async def create_checkout_session(
    request: CreateCheckoutSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get the subscription plan
    plan_query = await db.execute(
        select(SubscriptionPlan).filter(SubscriptionPlan.id == request.plan_id)
    )
    plan = plan_query.scalars().first()
    
    if not plan:
        return {"error": "Subscription plan not found", "details": "The requested subscription plan does not exist"}
    
    if not plan.is_active:
        return {"error": "This subscription plan is no longer available", "details": "Please choose a different plan"}
    
    # Get user from database to check if they already have a subscription
    user_query = await db.execute(
        select(UserModel).filter(UserModel.id == current_user.id)
    )
    user = user_query.scalars().first()

    # User found but wwe need to check that user does not already have an active subscription
    # Check if user already has an active subscription for any plan
    existing_subscription_query = await db.execute(
        select(UserSubscription).filter(
            and_(
                UserSubscription.user_id == user.id,
                # UserSubscription.plan_id == plan.id,
                UserSubscription.status == "active"
            )
        )
    )
    existing_subscription = existing_subscription_query.scalars().first()

    if existing_subscription:
        return {"error": "User already has an active subscription plan", "details": "Please manage your existing subscription instead"}
    
    try:
        # Create or retrieve Stripe customer
        if not user.stripe_customer_id:
            # Create a new customer in Stripe
            customer = stripe.Customer.create(
                email=user.email,
                name=f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else None,
                metadata={"user_id": str(user.id)}
            )
            
            # Update user with Stripe customer ID
            user.stripe_customer_id = customer.id
            await db.commit()
        
        # Create checkout session
        
        checkout_session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": plan.price_id,
                    "quantity": 1,
                },
            ],
            mode="subscription",
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            metadata={
                "user_id": str(user.id),
                "plan_id": plan.id
            }
        )

        return {"checkout_url": checkout_session.url, "status": "success", "error": None}
    except stripe.error.InvalidRequestError as e:
        logger.error(f"Stripe InvalidRequestError: {str(e)}")
        return {"error": "Invalid request, please check your input", "details": str(e)}
    except stripe.error.AuthenticationError as e:
        logger.error(f"Stripe AuthenticationError: {str(e)}")
        return {"error": "Authentication failed, please check your API keys", "details": str(e)}
    except stripe.error.CardError as e:
        logger.error(f"Stripe CardError: {str(e)}")
        return {"error": "Card error, please check your card details", "details": str(e)}
    except stripe.error.RateLimitError as e:
        logger.error(f"Stripe RateLimitError: {str(e)}")
        return {"error": "Rate limit exceeded, please try again later", "details": str(e)}
    except stripe.error.APIConnectionError as e:
        logger.error(f"Stripe APIConnectionError: {str(e)}")
        return {"error": "Failed to connect to Stripe API, please check your network connection", "details": str(e)}
    except stripe.error.APIError as e:
        logger.error(f"Stripe APIError: {str(e)}")
        return {"error": "Stripe API error, please check your API keys", "details": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in checkout session creation: {str(e)}")
        return {"error": "An unexpected error occurred", "details": str(e)}

@router.post("/portal", response_model=PortalSessionResponse)
async def create_portal_session(
    request: CreatePortalSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get user from database
    user_query = await db.execute(
        select(UserModel).filter(UserModel.id == current_user.id)
    )
    user = user_query.scalars().first()
    
    if not user.stripe_customer_id:
        raise HTTPException(
            status_code=400,
            detail="No Stripe customer found for this user"
        )
    
    # Create Stripe customer portal session
    portal_session = stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id,
        return_url=request.return_url,
    )
    
    return PortalSessionResponse(portal_url=portal_session.url)

@router.get("/my-subscription", response_model=dict)
async def get_my_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get user's active subscription
    subscription_query = await db.execute(
        select(UserSubscription)
        .options(selectinload(UserSubscription.plan))
        .filter(
            UserSubscription.user_id == current_user.id,
            UserSubscription.status.in_([
                # SubscriptionStatus.ACTIVE,
                # SubscriptionStatus.TRIALING
                "active",
            ])
        )
    )
    subscription = subscription_query.scalars().first()
    
    if not subscription:
        raise HTTPException(
            status_code=404,
            detail="No active subscription found"
        )
    
    try:
        # Manually construct the response to avoid relationship issues
        result = {
            "id": subscription.id,
            "uuid": str(subscription.uuid),
            "user_id": subscription.user_id,
            "plan_id": subscription.plan_id,
            "stripe_subscription_id": subscription.stripe_subscription_id,
            "status": subscription.status,
            "current_period_start": subscription.current_period_start.isoformat(),
            "current_period_end": subscription.current_period_end.isoformat(),
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "created_at": subscription.created_at.isoformat(),
            "updated_at": subscription.updated_at.isoformat(),
            "plan": {
                "id": subscription.plan.id,
                "uuid": str(subscription.plan.uuid),
                "name": subscription.plan.name,
                "description": subscription.plan.description,
                "price_id": subscription.plan.price_id,
                "tier": subscription.plan.tier,
                "price_per_month": subscription.plan.price_per_month,
                "features": subscription.plan.features,
                "is_active": subscription.plan.is_active,
                "created_at": subscription.plan.created_at.isoformat(),
                "updated_at": subscription.plan.updated_at.isoformat()
            }
        }
        return result
    except Exception as e:
        logger.error(f"Error returning subscription: {str(e)}")
        raise

@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Get the webhook signature from headers
    signature = request.headers.get("stripe-signature")
    
    logger.info("Signature =====> %s", signature)
    if not signature:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")
    
    # Get the raw request body
    payload = await request.body()
    
    try:
        # Verify the event using the webhook secret
        # logger.info("Verifying event using webhook secret =====> %s", stripe_webhook_secret)

        event = stripe.Webhook.construct_event(
            payload, signature, stripe_webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail=str(e))
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail=str(e))
    
    logger.info("Event =====> %s", event)
    
    # Handle the event
    if event["type"] == "checkout.session.comleted":
        # Payment was successful, provision the subscription
        session = event["data"]["object"]
        
        # Extract metadata
        user_id = session.get("metadata", {}).get("user_id")
        plan_id = session.get("metadata", {}).get("plan_id")
        logger.info("User ID =====> %s", user_id)
        logger.info("Plan ID =====> %s", plan_id)
        
        if not user_id or not plan_id:
            return {"status": "error", "message": "Missing metadata"}
        
        # Get subscription details from Stripe
        subscription_id = session.get("subscription")
        if not subscription_id:
            return {"status": "error", "message": "No subscription ID in session"}
        
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Create user subscription record
        new_subscription = UserSubscription(
            user_id=(user_id),
            plan_id=int(plan_id),
            stripe_subscription_id=subscription_id,
            # status=SubscriptionStatus(subscription.status),
            status="active",
            current_period_start=datetime.fromtimestamp(subscription.current_period_start),
            current_period_end=datetime.fromtimestamp(subscription.current_period_end),
            cancel_at_period_end=subscription.cancel_at_period_end
        )
        
        db.add(new_subscription)
        await db.commit()

    elif event["type"] == "customer.subscription.created":
        # Subscription was created, provision the subscription
        subscription_obj = event["data"]["object"]

        user_id = None
        plan_id = None
        
        # Extract values from the subscription object
        subscription_id = subscription_obj.get("id")
        plan_price_id = subscription_obj.get("plan", {}).get("id")
        plan_amount = subscription_obj.get("plan", {}).get("amount")
        plan_product = subscription_obj.get("plan", {}).get("product")
        current_period_start = subscription_obj.get("current_period_start")
        current_period_end = subscription_obj.get("current_period_end")
        metadata = subscription_obj.get("metadata", {})
        status = subscription_obj.get("status")
    
        logger.info(f"Subscription ID: {subscription_id}, Plan Price ID: {plan_price_id}, Plan Amount: {plan_amount}, Plan Product: {plan_product}, Metadata: {metadata}, Status: {status}")
        
        # Get user_id from metadata or customer lookup
        
        if True:
            customer_id = subscription_obj.get("customer")
            logger.info("Customer ID =====> %s", customer_id)
            if customer_id:
                user_query = await db.execute(
                    select(UserModel).filter(UserModel.stripe_customer_id == customer_id)
                )
                user = user_query.scalars().first()
                if user:
                    user_id = user.id
        
        if not user_id:
            # user_id = 1
            raise HTTPException(status_code=400, detail="Could not determine user for subscription")
        logger.info("User ID =====> %s", user_id)
        plan = None
        try:
            # Find the plan by price_id
            plan_query = await db.execute(
                select(SubscriptionPlan).filter(SubscriptionPlan.price_id == plan_price_id)
            )
            plan = plan_query.scalars().first()
            
            if not plan:
                logger.info("for plan_price_id =====> %s, Plan not found, creating new plan", plan_price_id )
                # raise HTTPException(status_code=400, detail="Could not determine plan for subscription")
                # Create a new subscription plan in the database
                new_plan = SubscriptionPlan(
                    name=f"Plan from Stripe - {plan_price_id}",
                    description=f"Auto-created plan for Stripe price {plan_price_id}",
                    price_id=plan_price_id,
                    price_per_month=plan_amount,  
                    is_active=True,
                    tier='1',
                    features=["feature1", "feature2", "feature3"]   
                )
                db.add(new_plan)
                await db.commit()
                plan = new_plan
        except Exception as e:
            logger.error(f"Error finding subscription plan with price_id '{plan_price_id}': {e}")
            raise HTTPException(status_code=400, detail="Could not determine plan for subscription")
           
        # User found and subscription plan found but we need to check that user does not already have any active subscription
        # Check if user already has an active subscription for any 
        # logger.info("Pre-check User ID =====> %s", user_id)
        # logger.info("Pre-check Plan ID =====> %s", plan.id)
        existing_subscription_query = await db.execute(
            select(UserSubscription).filter(
                UserSubscription.user_id == user_id,
                UserSubscription.plan_id == plan.id,
                UserSubscription.status == "active",
                # UserSubscription.current_period_end > datetime.now()
            )
        )
        existing_subscription = existing_subscription_query.scalars().first()
        logger.info("Existing subscription =====> %s", existing_subscription)
            
        if existing_subscription:
            user_name = getattr(user, 'username', f'User {user_id}')
            logger.warning(f"User '{user_name}' (ID: {user_id}) already has an active subscription")
            raise HTTPException(
                status_code=400,
                detail="User already has an active subscription"
            )
        # Create user subscription record
        new_subscription = UserSubscription(
            user_id=user_id,
            plan_id=plan.id if plan else 1,
            stripe_subscription_id=subscription_id,
            status=status,
            current_period_start=datetime.fromtimestamp(current_period_start),
             current_period_end=datetime.fromtimestamp(current_period_end),
            cancel_at_period_end=subscription_obj.get("cancel_at_period_end", False)
        )
        
        db.add(new_subscription)
        await db.commit()

    elif event["type"] == "customer.subscription.updated":
        # Subscription was updated
        subscription = event["data"]["object"]
        subscription_id = subscription.id
        
        # Update the subscription in the database
        db_subscription_query = await db.execute(
            select(UserSubscription).filter(UserSubscription.stripe_subscription_id == subscription_id)
        )
        db_subscription = db_subscription_query.scalars().first()
        
        if db_subscription:
            # db_subscription.status = SubscriptionStatus(subscription.status)
            db_subscription.status = subscription.status
            db_subscription.current_period_start = datetime.fromtimestamp(subscription.current_period_start)
            db_subscription.current_period_end = datetime.fromtimestamp(subscription.current_period_end)
            db_subscription.cancel_at_period_end = subscription.cancel_at_period_end
            
            await db.commit()
    
    elif event["type"] == "customer.subscription.deleted":
        # Subscription was canceled or has expired
        subscription = event["data"]["object"]
        subscription_id = subscription.id
        
        # Update the subscription in the database
        db_subscription_query = await db.execute(
            select(UserSubscription).filter(UserSubscription.stripe_subscription_id == subscription_id)
        )
        db_subscription = db_subscription_query.scalars().first()
        
        if db_subscription:
            # db_subscription.status = SubscriptionStatus.CANCELED
            db_subscription.status = "canceled"
            await db.commit()
    
    return {"status": "success"}

# Admin endpoint to view all subscriptions
@router.get("/subscriptions", response_model=List[UserSubscriptionRead])
async def list_all_subscriptions(
    # status: Optional[SubscriptionStatus] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if user has admin or super_admin role
    user_roles = [role.name for role in current_user.roles]
    if not any(role in ['admin', 'super_admin'] for role in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view all subscriptions"
        )
    
    # Build query with proper eager loading using selectinload for collections and joinedload for single relationships
    query = select(UserSubscription).options(
        selectinload(UserSubscription.plan),
        selectinload(UserSubscription.user).selectinload(UserModel.roles)
    )
    
    if status:
        query = query.filter(UserSubscription.status == status)
    
    # Execute query
    subscriptions_query = await db.execute(query)
    subscriptions = subscriptions_query.scalars().all()
    
    # Debug logging
    print(f"Found {len(subscriptions)} subscriptions")
    if subscriptions:
        first_sub = subscriptions[0]
        print(f"First subscription user: {first_sub.user}")
        print(f"First subscription user_id: {first_sub.user_id}")
        if first_sub.user:
            print(f"User details: {first_sub.user.first_name}, {first_sub.user.last_name}, {first_sub.user.email}")
        else:
            print("User is None - relationship not loaded properly")
    
    return subscriptions

# Admin endpoint to cancel a subscription
@router.post("/subscriptions/{subscription_id}/cancel", response_model=dict)
async def cancel_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a subscription by setting its status to 'cancelled'
    Only administrators and super administrators can perform this action
    """
    # Check if user has admin or super_admin role
    user_roles = [role.name for role in current_user.roles]
    if not any(role in ['admin', 'super_admin'] for role in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can cancel subscriptions"
        )
    
    # Find the subscription with user and plan data
    query = select(UserSubscription).options(
        selectinload(UserSubscription.user),
        selectinload(UserSubscription.plan)
    ).where(UserSubscription.id == subscription_id)
    
    result = await db.execute(query)
    subscription = await safe_scalar_one_or_none(result)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Check if subscription is already cancelled
    if subscription.status == 'cancelled':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subscription is already cancelled"
        )
    
    # Check if subscription is active (only cancel active subscriptions)
    if subscription.status != 'active':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel subscription with status: {subscription.status}"
        )
    
    try:
        # Cancel the subscription in Stripe first
        if subscription.stripe_subscription_id:
            try:
                stripe_subscription = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
                
                # Cancel the Stripe subscription immediately
                cancelled_stripe_subscription = stripe.Subscription.cancel(subscription.stripe_subscription_id)
                
                logger.info(f"Stripe subscription {subscription.stripe_subscription_id} cancelled successfully")
                
            except stripe.error.StripeError as e:
                logger.error(f"Stripe error while cancelling subscription {subscription.stripe_subscription_id}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to cancel subscription in Stripe: {str(e)}"
                )
        else:
            logger.warning(f"Subscription {subscription_id} has no Stripe subscription ID")
        
        # Update subscription status to cancelled in our database
        subscription.status = 'cancelled'
        subscription.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(subscription)
        
        logger.info(f"Subscription {subscription_id} cancelled successfully by admin {current_user.id}")
        
        return {
            "success": True,
            "message": "Subscription cancelled successfully",
            "subscription_id": subscription.id,
            "status": subscription.status,
            "user_id": subscription.user_id,
            "stripe_subscription_id": subscription.stripe_subscription_id
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Database error while cancelling subscription {subscription_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel subscription: {str(e)}"
        )

# Admin endpoint to view a specific user's subscriptions
@router.get("/users/{user_id}/subscriptions", response_model=List[UserSubscriptionRead])
async def get_user_subscriptions(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if user is admin or the user themselves
    user_roles = [role.name for role in current_user.roles]
    is_admin = any(role in ['admin', 'super_admin'] for role in user_roles)
    if not is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this user's subscriptions"
        )
    
    # Get user's subscriptions
    subscriptions_query = await db.execute(
        select(UserSubscription)
        .options(selectinload(UserSubscription.plan))
        .filter(UserSubscription.user_id == user_id)
    )
    subscriptions = subscriptions_query.scalars().all()
    
    return subscriptions 