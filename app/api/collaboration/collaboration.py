from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.db.session import get_db
from app.db.models.collaborations import Collaboration as CollaborationModel
from app.schemas.collaborations import CollaborationCreate, Collaboration
import logging

router = APIRouter(prefix="/collaborations", tags=["collaborations"])

# Configure logging
logger = logging.getLogger(__name__)

@router.post("", response_model=Collaboration)
async def create_collaboration(collaboration: CollaborationCreate, db: AsyncSession = Depends(get_db)):
    db_collaboration = CollaborationModel(**collaboration.dict())
    logger.info(f"Creating collaboration: {db_collaboration}")
    db.add(db_collaboration)
    await db.commit()
    await db.refresh(db_collaboration)
    return db_collaboration

@router.get("/{collaboration_id}", response_model=Collaboration)
async def get_collaboration(collaboration_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CollaborationModel).filter(CollaborationModel.id == collaboration_id))
    collaboration = result.scalar_one_or_none()
    if collaboration is None:
        raise HTTPException(status_code=404, detail="Collaboration not found")
    return collaboration

@router.put("/{collaboration_id}", response_model=Collaboration)
async def update_collaboration(collaboration_id: int, collaboration: CollaborationCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CollaborationModel).filter(CollaborationModel.id == collaboration_id))
    db_collaboration = result.scalar_one_or_none()
    if db_collaboration is None:
        raise HTTPException(status_code=404, detail="Collaboration not found")
    for key, value in collaboration.dict().items():
        setattr(db_collaboration, key, value)
    await db.commit()
    await db.refresh(db_collaboration)
    return db_collaboration

@router.delete("/{collaboration_id}")
async def delete_collaboration(collaboration_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CollaborationModel).filter(CollaborationModel.id == collaboration_id))
    collaboration = result.scalar_one_or_none()
    if collaboration is None:
        raise HTTPException(status_code=404, detail="Collaboration not found")
    await db.delete(collaboration)
    await db.commit()
    return {"detail": "Collaboration deleted"}

@router.get("", response_model=List[Collaboration])
async def list_collaborations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CollaborationModel))
    collaborations = result.scalars().all()
    return collaborations 