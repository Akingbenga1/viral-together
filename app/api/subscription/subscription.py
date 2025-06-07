from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional
from datetime import datetime
import stripe
import os
from uuid import UUID

from app.api.auth import get_current_user
from app.api.subscription.subscription_models import (
    SubscriptionPlanCreate, SubscriptionPlanRead, SubscriptionPlanUpdate
)
from app.db.models.subscription import SubscriptionPlan
from app.db.models import User as UserModel
from app.db.session import get_db
from app.schemas import User

# Set up Stripe API key
stripe.api_key = os.getenv("STRIPE_API_KEY")
stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

router = APIRouter()

# Admin endpoints for managing subscription plans
@router.post("/plans", response_model=SubscriptionPlanRead)
async def create_subscription_plan(
    plan: SubscriptionPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if user is admin
    # if not current_user.is_admin:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Only administrators can create subscription plans"
    #     )
    
    # Create new subscription plan
    new_plan = SubscriptionPlan(**plan.dict())
    db.add(new_plan)
    await db.commit()
    await db.refresh(new_plan)
    
    return new_plan

@router.get("/plans", response_model=List[SubscriptionPlanRead])
async def list_subscription_plans(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    query = select(SubscriptionPlan)
    
    if active_only:
        query = query.filter(SubscriptionPlan.is_active == True)
    
    plans_query = await db.execute(query)
    plans = plans_query.scalars().all()
    
    return plans

@router.get("/plans/{plan_id}", response_model=SubscriptionPlanRead)
async def get_subscription_plan(
    plan_id: int,
    db: Session = Depends(get_db)
):
    plan_query = await db.execute(
        select(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id)
    )
    plan = plan_query.scalars().first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    
    return plan

@router.put("/plans/{plan_id}", response_model=SubscriptionPlanRead)
async def update_subscription_plan(
    plan_id: int,
    plan_data: SubscriptionPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update subscription plans"
        )
    
    # Get the plan
    plan_query = await db.execute(
        select(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id)
    )
    plan = plan_query.scalars().first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Subscription plan not found")
    
    # Update plan fields
    for key, value in plan_data.dict(exclude_unset=True).items():
        setattr(plan, key, value)
    
    await db.commit()
    await db.refresh(plan)
    
    return plan