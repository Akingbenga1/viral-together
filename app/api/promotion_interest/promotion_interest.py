from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.db.session import get_db
from app.db.models.promotion_interest import PromotionInterest as PromotionInterestModel
from app.schemas.promotion_interest import PromotionInterestCreate, PromotionInterest
from app.core.query_helpers import safe_scalar_one_or_none

router = APIRouter(prefix="/promotion_interest", tags=["promotion_interests"])

@router.post("", response_model=PromotionInterest)
async def create_promotion_interest(promotion_interest: PromotionInterestCreate, db: AsyncSession = Depends(get_db)):
    db_promotion_interest = PromotionInterestModel(**promotion_interest.dict())
    db.add(db_promotion_interest)
    await db.commit()
    await db.refresh(db_promotion_interest)
    return db_promotion_interest

@router.get("/{promotion_interest_id}", response_model=PromotionInterest)
async def get_promotion_interest(promotion_interest_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PromotionInterestModel).filter(PromotionInterestModel.id == promotion_interest_id))
    promotion_interest = await safe_scalar_one_or_none(result)
    if promotion_interest is None:
        raise HTTPException(status_code=404, detail="Promotion Interest not found")
    return promotion_interest

@router.put("/{promotion_interest_id}", response_model=PromotionInterest)
async def update_promotion_interest(promotion_interest_id: int, promotion_interest: PromotionInterestCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PromotionInterestModel).filter(PromotionInterestModel.id == promotion_interest_id))
    db_promotion_interest = await safe_scalar_one_or_none(result)
    if db_promotion_interest is None:
        raise HTTPException(status_code=404, detail="Promotion Interest not found")
    for key, value in promotion_interest.dict().items():
        setattr(db_promotion_interest, key, value)
    await db.commit()
    await db.refresh(db_promotion_interest)
    return db_promotion_interest

@router.delete("/{promotion_interest_id}")
async def delete_promotion_interest(promotion_interest_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PromotionInterestModel).filter(PromotionInterestModel.id == promotion_interest_id))
    promotion_interest = await safe_scalar_one_or_none(result)
    if promotion_interest is None:
        raise HTTPException(status_code=404, detail="Promotion Interest not found")
    await db.delete(promotion_interest)
    await db.commit()
    return {"detail": "Promotion Interest deleted"}

@router.get("", response_model=List[PromotionInterest])
async def list_promotion_interests(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PromotionInterestModel))
    promotion_interests = result.scalars().all()
    return promotion_interests 