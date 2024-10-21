
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.api.business.business_models import BusinessRead, BusinessCreate, BusinessUpdate
from app.db.models.business import Business
from app.db.session import get_db
from typing import List

from fastapi import UploadFile, File
import os
from pathlib import Path
from uuid import uuid4

from app.schemas import User

router = APIRouter(dependencies=[Depends(get_current_user)])


# 1. Create a Business
@router.post("/create", response_model=BusinessRead, status_code=status.HTTP_201_CREATED)
async def create_business(business: BusinessCreate, db: Session = Depends(get_db)):
    new_business = Business(**business.dict())
    db.add(new_business)
    await db.commit()
    await db.refresh(new_business)
    return new_business


# 2. Get Business by ID
@router.get("/get_business_by_id/{business_id}", response_model=BusinessRead)
async def get_business(business_id: int, db: Session = Depends(get_db)):
    businesses = await db.execute(select(Business).filter(Business.id == business_id))
    business = businesses.scalars().first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return business


# 3. Update Business by ID
@router.put("/{business_id}", response_model=BusinessRead)
async def update_business(business_id: int, business_data: BusinessUpdate, db: Session = Depends(get_db)):
    businesses = await db.execute(select(Business).filter(Business.id == business_id))
    business = businesses.scalars().first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    for key, value in business_data.dict(exclude_unset=True).items():
        setattr(business, key, value)

    await db.commit()
    await db.refresh(business)
    return business


# 4. Delete Business by ID
@router.delete("/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(business_id: int, db: Session = Depends(get_db)):
    businesses = await db.execute(select(Business).filter(Business.id == business_id))
    business = businesses.scalars().first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    await db.delete(business)
    await db.commit()
    return


# 5. List All Businesses
@router.get("/get_all", response_model=List[BusinessRead])
async def list_all_businesses(db: Session = Depends(get_db)):
    businesses = await db.execute(select(Business))
    all_businesses = businesses.scalars().all()
    return all_businesses


# 6. Filter Businesses by Industry
@router.get("/get_business_by_industry/{industry}", response_model=List[BusinessRead])
async def filter_businesses_by_industry(industry: str, db: Session = Depends(get_db)):
    businesses_search_query = await db.execute(select(Business).filter(Business.industry.ilike(f"%{industry}%")))
    businesses = businesses_search_query.scalars().all()
    return businesses


# 7. Filter Businesses by Location
@router.get("/get_business_by_location/{location}", response_model=List[BusinessRead])
async def filter_businesses_by_location(location: str, db: Session = Depends(get_db)):
    businesses_search_query = await db.execute(select(Business).filter(Business.location.ilike(f"%{location}%")))
    businesses = businesses_search_query.scalars().all()
    return businesses


# 8. Verify a Business
@router.put("/{business_id}/verify", response_model=BusinessRead)
async def verify_business(business_id: int, db: Session = Depends(get_db)):
    businesses = await db.execute(select(Business).filter(Business.id == business_id))
    business = businesses.scalars().first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    business.verified = True
    await db.commit()
    await db.refresh(business)
    return business


# 9. Deactivate a Business
@router.put("/businesses/{business_id}/deactivate", response_model=BusinessRead)
async def deactivate_business(business_id: int, db: Session = Depends(get_db)):
    businesses = await db.execute(select(Business).filter(Business.id == business_id))
    business = businesses.scalars().first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    business.active = False
    await db.commit()
    await db.refresh(business)
    return business


# 10. Activate a Business
@router.put("/businesses/{business_id}/activate", response_model=BusinessRead)
async def activate_business(business_id: int, db: Session = Depends(get_db)):
    businesses = await db.execute(select(Business).filter(Business.id == business_id))
    business = businesses.scalars().first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    business.active = True
    await db.commit()
    await db.refresh(business)
    return business


# 11. Get All Verified Businesses
@router.get("/businesses/verified", response_model=List[BusinessRead])
async def get_verified_businesses(db: Session = Depends(get_db)):
    businesses = await db.query(Business).filter(Business.verified == True).all()
    return businesses


# 12. Search Businesses by Name
@router.get("/businesses/search", response_model=List[BusinessRead])
async def search_businesses_by_name(name: str, db: Session = Depends(get_db)):
    businesses = await db.query(Business).filter(Business.name.ilike(f"%{name}%")).all()
    return businesses


# 13. Get Businesses by Owner (User ID)
@router.get("/users/{owner_id}/businesses", response_model=List[BusinessRead])
async def get_businesses_by_owner(owner_id: int, db: Session = Depends(get_db)):
    businesses = await db.query(Business).filter(Business.owner_id == owner_id).all()
    return businesses


# 14. Get Businesses by Rating
@router.get("/businesses/rating/{min_rating}", response_model=List[BusinessRead])
async def get_businesses_by_min_rating(min_rating: float, db: Session = Depends(get_db)):
    businesses = await db.query(Business).filter(Business.rating >= min_rating).all()
    return businesses


# 15. Count Total Businesses
@router.get("/businesses/count", response_model=dict)
async def count_total_businesses(db: Session = Depends(get_db)):
    count = await db.query(Business).count()
    return {"total_businesses": count}
