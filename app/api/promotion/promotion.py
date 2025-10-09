from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from typing import List, Dict, Optional
from datetime import datetime
import uuid
import logging
from app.db.session import get_db
from app.db.models.promotions import Promotion as PromotionModel
from app.db.models.collaborations import Collaboration as CollaborationModel
from app.db.models.business import Business as BusinessModel
from app.db.models.influencer import Influencer as InfluencerModel
from app.db.models.user import User as UserModel
from app.schemas.promotions import PromotionCreate, Promotion, PromotionWithInfluencers, PromotionStatusUpdate, PromotionSpentUpdate
from app.core.query_helpers import safe_scalar_one_or_none
from app.core.util import ensure_naive_datetime
from pydantic import BaseModel

# Import notification services
from app.services.notification_service import notification_service
from app.schemas.notification import (
    PromotionCreatedNotificationData,
    InfluencerInterestNotificationData
)

router = APIRouter(prefix="/promotions", tags=["promotions"])

# Pydantic models for collaboration interest
class CollaborationInterestRequest(BaseModel):
    influencer_id: int
    proposed_amount: Optional[float] = None
    collaboration_type: str = "sponsored_post"
    deliverables: Optional[str] = None
    message: Optional[str] = None  # Optional message from influencer

# Configure logging
logger = logging.getLogger(__name__)

@router.post("", response_model=Promotion)
async def create_promotion(
    promotion: PromotionCreate, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    # Get business details for notification
    business_result = await db.execute(
        select(BusinessModel).where(BusinessModel.id == promotion.business_id)
    )
    business = await safe_scalar_one_or_none(business_result)
    
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Create promotion with timezone-safe datetime conversion
    promotion_data = promotion.dict()
    # Ensure datetime fields are naive for database storage
    if 'start_date' in promotion_data:
        promotion_data['start_date'] = ensure_naive_datetime(promotion_data['start_date'])
    if 'end_date' in promotion_data:
        promotion_data['end_date'] = ensure_naive_datetime(promotion_data['end_date'])
    
    # Ensure UUID is set server-side if not provided
    if 'uuid' not in promotion_data or not promotion_data.get('uuid'):
        promotion_data['uuid'] = uuid.uuid4()

    db_promotion = PromotionModel(**promotion_data)
    promotion_name = getattr(promotion, 'promotion_name', 'Untitled Promotion')
    business_name = getattr(business, 'name', f'Business {business.id}')
    
    logger.info(f"Creating promotion '{promotion_name}' for business '{business_name}' (ID: {promotion.business_id})")
    
    db.add(db_promotion)
    await db.commit()
    await db.refresh(db_promotion)
    
    logger.info(f"Promotion '{promotion_name}' (ID: {db_promotion.id}) created successfully")
    
    # 🔔 TRIGGER NOTIFICATION: Promotion Created
    notification_data = PromotionCreatedNotificationData(
        promotion_id=db_promotion.id,
        promotion_name=promotion_name,
        business_id=promotion.business_id,
        business_name=business_name,
        industry=getattr(promotion, 'industry', None),
        budget=getattr(promotion, 'budget', None)
    )
    
    # Create notifications for relevant influencers
    await notification_service.create_promotion_created_notification(
        db=db,
        data=notification_data,
        background_tasks=background_tasks
    )
    
    logger.info(f"Notification triggered for promotion creation: '{promotion_name}' by '{business_name}'")
    
    return db_promotion

@router.get("/{promotion_id}", response_model=Promotion)
async def get_promotion(promotion_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PromotionModel).filter(PromotionModel.id == promotion_id))
    promotion = await safe_scalar_one_or_none(result)
    if promotion is None:
        raise HTTPException(status_code=404, detail="Promotion not found")
    return promotion

@router.put("/{promotion_id}", response_model=Promotion)
async def update_promotion(promotion_id: int, promotion: PromotionCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PromotionModel).filter(PromotionModel.id == promotion_id))
    db_promotion = await safe_scalar_one_or_none(result)
    if db_promotion is None:
        raise HTTPException(status_code=404, detail="Promotion not found")
    
    # Update promotion with timezone-safe datetime conversion
    promotion_data = promotion.dict()
    for key, value in promotion_data.items():
        # Handle datetime fields specially to ensure they're naive
        if key in ['start_date', 'end_date'] and isinstance(value, datetime):
            value = ensure_naive_datetime(value)
        setattr(db_promotion, key, value)
    
    await db.commit()
    await db.refresh(db_promotion)
    return db_promotion

@router.delete("/{promotion_id}")
async def delete_promotion(promotion_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PromotionModel).filter(PromotionModel.id == promotion_id))
    promotion = await safe_scalar_one_or_none(result)
    if promotion is None:
        raise HTTPException(status_code=404, detail="Promotion not found")
    await db.delete(promotion)
    await db.commit()
    return {"detail": "Promotion deleted"}

@router.get("", response_model=List[Promotion])
async def list_promotions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PromotionModel).order_by(PromotionModel.created_at.desc())
    )
    promotions = result.scalars().all()
    return promotions

@router.post("/{promotion_id}/show-interest", response_model=Dict)
async def show_collaboration_interest(
    promotion_id: int,
    request: CollaborationInterestRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Allow an influencer to show interest in a promotion by creating a pending collaboration"""
    
    # 1. Validate promotion exists and get business details
    promotion_result = await db.execute(
        select(PromotionModel, BusinessModel)
        .join(BusinessModel, PromotionModel.business_id == BusinessModel.id)
        .where(PromotionModel.id == promotion_id)
    )
    promotion_data = promotion_result.first()
    
    if not promotion_data:
        raise HTTPException(status_code=404, detail="Promotion not found")
    
    promotion, business = promotion_data
    
    # 2. Validate influencer exists
    influencer_result = await db.execute(
        select(InfluencerModel, UserModel)
        .join(UserModel, InfluencerModel.user_id == UserModel.id)
        .where(InfluencerModel.id == request.influencer_id)
    )
    influencer_data = influencer_result.first()
    
    if not influencer_data:
        raise HTTPException(status_code=404, detail="Influencer not found")
    
    influencer, user = influencer_data
    
    # 3. Check if collaboration already exists
    existing_collaboration = await db.execute(
        select(CollaborationModel).where(and_(
            CollaborationModel.promotion_id == promotion_id,
            CollaborationModel.influencer_id == request.influencer_id
        ))
    )
    if await safe_scalar_one_or_none(existing_collaboration):
        raise HTTPException(
            status_code=400, 
            detail="Influencer already has a collaboration for this promotion"
        )
    
    # 4. Create collaboration record
    new_collaboration = CollaborationModel(
        influencer_id=request.influencer_id,
        promotion_id=promotion_id,
        status='pending',  # Key requirement!
        proposed_amount=request.proposed_amount,
        collaboration_type=request.collaboration_type,
        deliverables=request.deliverables,
        terms_and_conditions=request.message,
        negotiable=True if request.proposed_amount else False,
        contract_signed=False,
        payment_status='pending'
    )
    
    db.add(new_collaboration)
    await db.commit()
    await db.refresh(new_collaboration)
    
    # 5. Enhanced logging
    business_name = getattr(business, 'name', f'Business {business.id}')
    
    # Extract full name from user's first_name + last_name with graceful handling
    if user and user.first_name and user.last_name:
        influencer_name = f"{user.first_name} {user.last_name}"
    elif user and user.first_name:
        influencer_name = user.first_name
    elif user and user.last_name:
        influencer_name = user.last_name
    else:
        influencer_name = f'Influencer {influencer.id}'
    
    promotion_name = getattr(promotion, 'promotion_name', f'Promotion {promotion.id}')
    
    logger.info(f"Influencer '{influencer_name}' (ID: {request.influencer_id}) showed interest in promotion '{promotion_name}' (ID: {promotion_id}) for business '{business_name}' (ID: {business.id})")
    
    # 🔔 TRIGGER NOTIFICATION: Influencer Interest
    notification_data = InfluencerInterestNotificationData(
        collaboration_id=new_collaboration.id,
        promotion_id=promotion_id,
        promotion_name=promotion_name,
        business_id=business.id,
        business_name=business_name,
        influencer_id=request.influencer_id,
        influencer_name=influencer_name,
        proposed_amount=request.proposed_amount,
        message=request.message
    )
    
    # Create notification for business
    await notification_service.create_influencer_interest_notification(
        db=db,
        data=notification_data,
        background_tasks=background_tasks
    )
    
    logger.info(f"Notification triggered for influencer interest: '{influencer_name}' interested in '{promotion_name}' by '{business_name}'")
    
    return {
        "message": "Collaboration interest submitted successfully",
        "collaboration_id": new_collaboration.id,
        "promotion_name": promotion_name,
        "promotion_id": promotion_id,
        "business_name": business_name,
        "business_id": business.id,
        "influencer_name": influencer_name,
        "influencer_id": request.influencer_id,
        "status": "pending",
        "collaboration_type": request.collaboration_type,
        "proposed_amount": request.proposed_amount,
        "deliverables": request.deliverables,
        "message": request.message,
        "created_at": new_collaboration.created_at,
        "notification_triggered": True  # Indicate notification was sent
    }

@router.get("/{promotion_id}/influencers")
async def get_promotion_influencers(promotion_id: int, db: AsyncSession = Depends(get_db)):
    """Get all influencers associated with a promotion through collaborations"""
    
    # Verify promotion exists
    promotion_result = await db.execute(
        select(PromotionModel).where(PromotionModel.id == promotion_id)
    )
    promotion = await safe_scalar_one_or_none(promotion_result)
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found")
    
    # Get collaborations with influencer and user details
    collaborations_result = await db.execute(
        select(CollaborationModel, InfluencerModel, UserModel)
        .select_from(CollaborationModel)
        .join(InfluencerModel, CollaborationModel.influencer_id == InfluencerModel.id, isouter=False)
        .join(UserModel, InfluencerModel.user_id == UserModel.id, isouter=True)
        .where(CollaborationModel.promotion_id == promotion_id)
    )
    
    collaborations_data = collaborations_result.unique().all()
    
    influencers = []
    for collaboration, influencer, user in collaborations_data:
        # Extract full name from user's first_name + last_name with graceful handling
        if user and user.first_name and user.last_name:
            influencer_name = f"{user.first_name} {user.last_name}"
        elif user and user.first_name:
            influencer_name = user.first_name
        elif user and user.last_name:
            influencer_name = user.last_name
        else:
            influencer_name = f'Influencer {influencer.id}'
        
        # Ensure all values are JSON serializable (avoid Decimal/datetime issues)
        influencers.append({
            "collaboration_id": collaboration.id,
            "influencer_id": influencer.id,
            "influencer_name": influencer_name,
            "influencer_email": user.email if user else None,
            "collaboration_status": collaboration.status,
            "collaboration_type": collaboration.collaboration_type,
            "proposed_amount": float(collaboration.proposed_amount) if getattr(collaboration, "proposed_amount", None) is not None else None,
            "negotiated_amount": float(collaboration.negotiated_amount) if getattr(collaboration, "negotiated_amount", None) is not None else None,
            "deliverables": collaboration.deliverables,
            "contract_signed": bool(collaboration.contract_signed) if collaboration.contract_signed is not None else False,
            "payment_status": collaboration.payment_status,
            "created_at": collaboration.created_at.isoformat() if getattr(collaboration, "created_at", None) else None,
            "updated_at": collaboration.updated_at.isoformat() if getattr(collaboration, "updated_at", None) else None
        })
    
    return JSONResponse(content=influencers)

@router.patch("/{promotion_id}/status", response_model=Promotion)
async def update_promotion_status(
    promotion_id: int, 
    status_update: PromotionStatusUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """Update promotion status"""
    
    result = await db.execute(select(PromotionModel).filter(PromotionModel.id == promotion_id))
    db_promotion = await safe_scalar_one_or_none(result)
    if db_promotion is None:
        raise HTTPException(status_code=404, detail="Promotion not found")
    
    db_promotion.status = status_update.status
    await db.commit()
    await db.refresh(db_promotion)
    
    logger.info(f"Promotion {promotion_id} status updated to {status_update.status}")
    return db_promotion

@router.patch("/{promotion_id}/spent", response_model=Promotion)
async def update_promotion_spent(
    promotion_id: int, 
    spent_update: PromotionSpentUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """Update promotion spent amount"""
    
    result = await db.execute(select(PromotionModel).filter(PromotionModel.id == promotion_id))
    db_promotion = await safe_scalar_one_or_none(result)
    if db_promotion is None:
        raise HTTPException(status_code=404, detail="Promotion not found")
    
    # Validate spent amount doesn't exceed budget
    if spent_update.spent_amount > db_promotion.budget:
        raise HTTPException(
            status_code=400, 
            detail=f"Spent amount ({spent_update.spent_amount}) cannot exceed budget ({db_promotion.budget})"
        )
    
    db_promotion.spent_amount = spent_update.spent_amount
    await db.commit()
    await db.refresh(db_promotion)
    
    logger.info(f"Promotion {promotion_id} spent amount updated to {spent_update.spent_amount}")
    return db_promotion

@router.get("/{promotion_id}/with-influencers")
async def get_promotion_with_influencers(promotion_id: int, db: AsyncSession = Depends(get_db)):
    """Get promotion details with associated influencers"""
    
    # Get promotion
    promotion_result = await db.execute(
        select(PromotionModel).where(PromotionModel.id == promotion_id)
    )
    promotion = await safe_scalar_one_or_none(promotion_result)
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found")
    
    # Get influencers
    influencers_result = await db.execute(
        select(CollaborationModel, InfluencerModel, UserModel)
        .select_from(CollaborationModel)
        .join(InfluencerModel, CollaborationModel.influencer_id == InfluencerModel.id, isouter=False)
        .join(UserModel, InfluencerModel.user_id == UserModel.id, isouter=True)
        .where(CollaborationModel.promotion_id == promotion_id)
    )
    
    influencers_data = influencers_result.unique().all()
    
    influencers = []
    for collaboration, influencer, user in influencers_data:
        # Extract full name from user's first_name + last_name with graceful handling
        if user and user.first_name and user.last_name:
            influencer_name = f"{user.first_name} {user.last_name}"
        elif user and user.first_name:
            influencer_name = user.first_name
        elif user and user.last_name:
            influencer_name = user.last_name
        else:
            influencer_name = f'Influencer {influencer.id}'
        
        influencers.append({
            "collaboration_id": collaboration.id,
            "influencer_id": influencer.id,
            "influencer_name": influencer_name,
            "collaboration_status": collaboration.status,
            "collaboration_type": collaboration.collaboration_type,
            "proposed_amount": float(collaboration.proposed_amount) if collaboration.proposed_amount else None,
            "contract_signed": collaboration.contract_signed,
            "payment_status": collaboration.payment_status
        })
    
    # Convert promotion to dict and add influencers
    promotion_dict = {
        "id": promotion.id,
        "business_id": promotion.business_id,
        "promotion_name": promotion.promotion_name,
        "promotion_item": promotion.promotion_item,
        "description": promotion.description,
        "start_date": promotion.start_date,
        "end_date": promotion.end_date,
        "discount": float(promotion.discount) if promotion.discount else None,
        "budget": float(promotion.budget) if promotion.budget else None,
        "spent_amount": float(promotion.spent_amount) if promotion.spent_amount else 0,
        "status": promotion.status,
        "target_audience": promotion.target_audience,
        "social_media_platform_id": promotion.social_media_platform_id,
        "created_at": promotion.created_at,
        "updated_at": promotion.updated_at,
        "influencers": influencers
    }
    
    return JSONResponse(content=promotion_dict)