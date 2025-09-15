from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from decimal import Decimal

from app.db.session import get_db
from app.api.auth import get_current_user_dependency
from app.db.models.influencers_targets import InfluencersTargets
from app.schemas.influencers_targets import InfluencersTargetsCreate, InfluencersTargets as InfluencersTargetsSchema
from app.db.models.user import User

router = APIRouter()

@router.post("/influencers-targets/", response_model=InfluencersTargetsSchema)
async def create_influencer_targets(
    targets: InfluencersTargetsCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    # JSON columns will be handled automatically by SQLAlchemy
    db_targets = InfluencersTargets(
        user_id=current_user.id,
        **targets.dict(exclude_unset=True)
    )
    db.add(db_targets)
    await db.commit()
    await db.refresh(db_targets)
    return db_targets

@router.get("/influencers-targets/", response_model=List[InfluencersTargetsSchema])
async def get_influencer_targets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    result = await db.execute(select(InfluencersTargets).filter(InfluencersTargets.user_id == current_user.id))
    targets = result.scalars().all()
    return targets
