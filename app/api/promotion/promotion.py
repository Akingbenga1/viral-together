from fastapi import APIRouter, Depends, HTTPException
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
from app.schemas.promotions import PromotionCreate, Promotion
from pydantic import BaseModel

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
async def create_promotion(promotion: PromotionCreate, db: AsyncSession = Depends(get_db)):
    db_promotion = PromotionModel(**promotion.dict())
    promotion_name = getattr(promotion, 'promotion_name', 'Untitled Promotion')
    logger.info(f"Creating promotion '{promotion_name}' for business ID: {promotion.business_id}")
    db.add(db_promotion)
    await db.commit()
    await db.refresh(db_promotion)
    logger.info(f"Promotion '{promotion_name}' (ID: {db_promotion.id}) created successfully")
    return db_promotion

@router.get("/{promotion_id}", response_model=Promotion)
async def get_promotion(promotion_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PromotionModel).filter(PromotionModel.id == promotion_id))
    promotion = result.scalar_one_or_none()
    if promotion is None:
        raise HTTPException(status_code=404, detail="Promotion not found")
    return promotion

@router.put("/{promotion_id}", response_model=Promotion)
async def update_promotion(promotion_id: int, promotion: PromotionCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PromotionModel).filter(PromotionModel.id == promotion_id))
    db_promotion = result.scalar_one_or_none()
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
    promotion = result.scalar_one_or_none()
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
        select(InfluencerModel).where(InfluencerModel.id == request.influencer_id)
    )
    influencer = influencer_result.scalar_one_or_none()
    
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")
    
    # 3. Check if collaboration already exists
    existing_collaboration = await db.execute(
        select(CollaborationModel).where(and_(
            CollaborationModel.promotion_id == promotion_id,
            CollaborationModel.influencer_id == request.influencer_id
        ))
    )
    if existing_collaboration.scalar_one_or_none():
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
    influencer_name = getattr(influencer, 'name', f'Influencer {influencer.id}')
    promotion_name = getattr(promotion, 'promotion_name', f'Promotion {promotion.id}')
    
    logger.info(f"Influencer '{influencer_name}' (ID: {request.influencer_id}) showed interest in promotion '{promotion_name}' (ID: {promotion_id}) for business '{business_name}' (ID: {business.id})")
    
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
        "created_at": new_collaboration.created_at
    } 