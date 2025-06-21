from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy

from app.api.auth import get_current_user
from app.api.influencer.influencer_models import InfluencerRead, InfluencerCreate, InfluencerUpdate
from app.db.models import Influencer, User
from app.db.models.country import Country
from app.core.dependencies import require_role
from app.db.session import get_db
from typing import List

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("/create_influencer", response_model=InfluencerRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("influencer"))])
async def create_influencer(influencer_data: InfluencerCreate, db: AsyncSession = Depends(get_db)):
    # Extract collaboration country IDs
    collaboration_ids = influencer_data.collaboration_country_ids
    create_data = influencer_data.dict(exclude={'collaboration_country_ids'})

    # Fetch country objects from the database
    if collaboration_ids:
        countries_result = await db.execute(select(Country).where(Country.id.in_(collaboration_ids)))
        countries = countries_result.scalars().all()
        if len(countries) != len(collaboration_ids):
            raise HTTPException(status_code=400, detail="One or more collaboration countries not found.")
    else:
        countries = []

    # Create influencer instance
    new_influencer = Influencer(**create_data)
    new_influencer.collaboration_countries = countries
    
    db.add(new_influencer)
    try:
        await db.commit()
        await db.refresh(new_influencer)
        # Eagerly load relationships for the response
        result = await db.execute(
            select(Influencer)
            .options(selectinload(Influencer.user), selectinload(Influencer.base_country), selectinload(Influencer.collaboration_countries))
            .where(Influencer.id == new_influencer.id)
        )
        return result.scalars().one()
    except sqlalchemy.exc.IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Data integrity error: {e.orig}")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@router.get("/get_influencer/{influencer_id}", response_model=InfluencerRead)
async def get_influencer_by_id(influencer_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Influencer)
        .options(selectinload(Influencer.user), selectinload(Influencer.base_country), selectinload(Influencer.collaboration_countries))
        .where(Influencer.id == influencer_id)
    )
    influencer = result.scalars().first()
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")
    return influencer


@router.put("/update_influencer/{influencer_id}", response_model=InfluencerRead, dependencies=[Depends(require_role("admin"))])
async def update_influencer(influencer_id: int, influencer_data: InfluencerUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Influencer).where(Influencer.id == influencer_id))
    influencer = result.scalars().first()
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")

    update_data = influencer_data.dict(exclude_unset=True)
    
    if 'collaboration_country_ids' in update_data:
        collaboration_ids = update_data.pop('collaboration_country_ids')
        if collaboration_ids:
            countries_result = await db.execute(select(Country).where(Country.id.in_(collaboration_ids)))
            influencer.collaboration_countries = countries_result.scalars().all()
        else:
            influencer.collaboration_countries = []

    for key, value in update_data.items():
        setattr(influencer, key, value)

    await db.commit()
    await db.refresh(influencer)
    
    # Eagerly load relationships for the response
    final_result = await db.execute(
        select(Influencer)
        .options(selectinload(Influencer.user), selectinload(Influencer.base_country), selectinload(Influencer.collaboration_countries))
        .where(Influencer.id == influencer.id)
    )
    return final_result.scalars().one()


@router.delete("/remove_influencer/{influencer_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("admin"))])
async def delete_influencer(influencer_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Influencer).where(Influencer.id == influencer_id))
    influencer = result.scalars().first()
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")
    await db.delete(influencer)
    await db.commit()


@router.get("/list", response_model=List[InfluencerRead])
async def list_influencers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Influencer)
        .options(selectinload(Influencer.user), selectinload(Influencer.base_country), selectinload(Influencer.collaboration_countries))
    )
    return result.scalars().all()


@router.get("/search/by_base_country", response_model=List[InfluencerRead])
async def search_by_base_country(country_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Influencer)
        .where(Influencer.base_country_id == country_id)
        .options(selectinload(Influencer.user), selectinload(Influencer.base_country), selectinload(Influencer.collaboration_countries))
    )
    return result.scalars().all()


@router.get("/search/by_collaboration_country", response_model=List[InfluencerRead])
async def search_by_collaboration_country(country_id: int, db: AsyncSession = Depends(get_db)):
    # Find influencers who are open to collaboration in the specified country OR are available globally.
    # The subquery finds influencers who have at least one entry in the collaboration table.
    subquery = select(Influencer.id).join(Influencer.collaboration_countries).distinct()
    
    result = await db.execute(
        select(Influencer)
        .where(
            sqlalchemy.or_(
                # Condition 1: They have the specific country in their list
                Influencer.collaboration_countries.any(Country.id == country_id),
                # Condition 2: They have NO entries in the collaboration list (they are global)
                sqlalchemy.not_(Influencer.id.in_(subquery))
            )
        )
        .options(selectinload(Influencer.user), selectinload(Influencer.base_country), selectinload(Influencer.collaboration_countries))
    )
    return result.scalars().all()

