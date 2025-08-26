from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from app.db.session import get_db
from app.api.auth import get_current_user_dependency
from app.db.models.influencers_targets import InfluencersTargets
from app.schemas.influencers_targets import InfluencersTargetsCreate, InfluencersTargets
from app.db.models.user import User

router = APIRouter()

@router.post("/influencers-targets/", response_model=InfluencersTargets)
def create_influencer_targets(
    targets: InfluencersTargetsCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    # JSON columns will be handled automatically by SQLAlchemy
    db_targets = InfluencersTargets(
        user_id=current_user.id,
        **targets.dict(exclude_unset=True)
    )
    db.add(db_targets)
    db.commit()
    db.refresh(db_targets)
    return db_targets

@router.get("/influencers-targets/", response_model=List[InfluencersTargets])
def get_influencer_targets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    targets = db.query(InfluencersTargets).filter(InfluencersTargets.user_id == current_user.id).all()
    return targets
