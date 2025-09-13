from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from typing import List, Dict, Optional
import logging
from app.db.session import get_db
from app.db.models.promotions import Promotion as PromotionModel
from app.db.models.collaborations import Collaboration as CollaborationModel
from app.db.models.business import Business as BusinessModel
from app.db.models.influencer import Influencer as InfluencerModel
from app.db.models.user import User as UserModel
from app.schemas.promotions import PromotionCreate, Promotion
from app.core.query_helpers import safe_scalar_one_or_none
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
    
    # Create promotion
    db_promotion = PromotionModel(**promotion.dict())
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
    for key, value in promotion.dict().items():
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
    result = await db.execute(select(PromotionModel))
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