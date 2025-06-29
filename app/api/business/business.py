from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, or_, not_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy

from app.api.auth import get_current_user
from app.api.business.business_models import BusinessRead, BusinessCreate, BusinessUpdate
from app.db.models import Business, User
from app.db.models.country import Country
from app.core.dependencies import require_role, require_any_role
from app.db.session import get_db
from typing import List

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("/create", response_model=BusinessRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_any_role(["business", "admin", "super_admin"]))])
async def create_business(business_data: BusinessCreate, db: AsyncSession = Depends(get_db)):
    collaboration_ids = business_data.collaboration_country_ids
    create_data = business_data.dict(exclude={'collaboration_country_ids'})

    if collaboration_ids:
        countries_result = await db.execute(select(Country).where(Country.id.in_(collaboration_ids)))
        countries = countries_result.scalars().all()
        if len(countries) != len(collaboration_ids):
            raise HTTPException(status_code=400, detail="One or more collaboration countries not found.")
    else:
        countries = []

    new_business = Business(**create_data)
    new_business.collaboration_countries = countries
    
    db.add(new_business)
    try:
        await db.commit()
        await db.refresh(new_business)
        result = await db.execute(
            select(Business)
            .options(selectinload(Business.user), selectinload(Business.base_country), selectinload(Business.collaboration_countries))
            .where(Business.id == new_business.id)
        )
        return result.scalars().one()
    except sqlalchemy.exc.IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Data integrity error: {e.orig}")


@router.get("/get_business_by_id/{business_id}", response_model=BusinessRead)
async def get_business(business_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Business)
        .options(selectinload(Business.user), selectinload(Business.base_country), selectinload(Business.collaboration_countries))
        .where(Business.id == business_id)
    )
    business = result.scalars().first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business


@router.put("/{business_id}", response_model=BusinessRead, dependencies=[Depends(require_any_role(["admin", "super_admin"]))])
async def update_business(business_id: int, business_data: BusinessUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Business).where(Business.id == business_id))
    business = result.scalars().first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    update_data = business_data.dict(exclude_unset=True)
    
    if 'collaboration_country_ids' in update_data:
        collaboration_ids = update_data.pop('collaboration_country_ids')
        if collaboration_ids:
            countries_result = await db.execute(select(Country).where(Country.id.in_(collaboration_ids)))
            business.collaboration_countries = countries_result.scalars().all()
        else:
            business.collaboration_countries = []

    for key, value in update_data.items():
        setattr(business, key, value)

    await db.commit()
    await db.refresh(business)
    
    final_result = await db.execute(
        select(Business)
        .options(selectinload(Business.user), selectinload(Business.base_country), selectinload(Business.collaboration_countries))
        .where(Business.id == business.id)
    )
    return final_result.scalars().one()


@router.delete("/{business_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_any_role(["admin", "super_admin"]))])
async def delete_business(business_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Business).where(Business.id == business_id))
    business = result.scalars().first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    await db.delete(business)
    await db.commit()


@router.get("/get_all", response_model=List[BusinessRead])
async def list_all_businesses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Business)
        .options(selectinload(Business.user), selectinload(Business.base_country), selectinload(Business.collaboration_countries))
    )
    return result.scalars().all()


@router.get("/search/by_base_country", response_model=List[BusinessRead])
async def search_by_base_country(country_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Business)
        .where(Business.base_country_id == country_id)
        .options(selectinload(Business.user), selectinload(Business.base_country), selectinload(Business.collaboration_countries))
    )
    return result.scalars().all()


@router.get("/search/by_collaboration_country", response_model=List[BusinessRead])
async def search_by_collaboration_country(country_id: int, db: AsyncSession = Depends(get_db)):
    subquery = select(Business.id).join(Business.collaboration_countries).distinct()
    
    result = await db.execute(
        select(Business)
        .where(
            or_(
                Business.collaboration_countries.any(Country.id == country_id),
                not_(Business.id.in_(subquery))
            )
        )
        .options(selectinload(Business.user), selectinload(Business.base_country), selectinload(Business.collaboration_countries))
    )
    return result.scalars().all()
