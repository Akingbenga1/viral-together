from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import logging
from app.db.session import get_db
from app.db.models.promotions import Promotion as PromotionModel
from app.schemas.promotions import PromotionCreate, Promotion

router = APIRouter(prefix="/promotions", tags=["promotions"])



# Configure logging
logger = logging.getLogger(__name__)

@router.post("", response_model=Promotion)
async def create_promotion(promotion: PromotionCreate, db: AsyncSession = Depends(get_db)):
    db_promotion = PromotionModel(**promotion.dict())
    logger.info(f"Creating promotion: {db_promotion}")
    db.add(db_promotion)
    await db.commit()
    await db.refresh(db_promotion)
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