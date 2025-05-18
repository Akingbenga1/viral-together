
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
import sqlalchemy
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.api.influencer.influencer_models import InfluencerCreateResponse, InfluencerRead, InfluencerCreate, InfluencerUpdate
from app.db.models import Influencer
from app.db.session import get_db
from typing import List

from fastapi import UploadFile, File
import os
from pathlib import Path
from uuid import uuid4

from app.schemas import User

router = APIRouter(dependencies=[Depends(get_current_user)])


# 1. Create an Influencer
@router.post("/create_influencer", response_model=InfluencerCreateResponse)
async def create_influencer(influencer: InfluencerCreate, db: Session = Depends(get_db),  current_user: User = Depends(get_current_user)):
    try:
        new_influencer = Influencer(**influencer.dict())
        db.add(new_influencer)
        await db.commit()
        await db.refresh(new_influencer)
        return new_influencer
    except sqlalchemy.exc.IntegrityError as e:
        if "foreign key constraint" in str(e).lower():
            raise HTTPException(status_code=400, detail="Foreign key constraint failed")
        elif "unique constraint" in str(e).lower():
            raise HTTPException(status_code=400, detail="Unique constraint failed")
        else:
            raise HTTPException(status_code=400, detail="Duplicate entry found")
    except sqlalchemy.exc.OperationalError as e:
        raise HTTPException(status_code=503, detail="Database operation failed")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 2. Get Influencer by ID
@router.get("/get_influencer/{influencer_id}", response_model=InfluencerRead)
async def get_influencer_by_id(influencer_id: int, db: AsyncSession = Depends(get_db)):
    influencers = await db.execute(select(Influencer).filter(Influencer.id == influencer_id))
    influencer = influencers.scalars().first()  # Get the first result
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")
    return influencer


# 3. Update an Influencer by ID
@router.put("/update_influencer/{influencer_id}", response_model=InfluencerRead)
async def update_influencer(influencer_id: int, influencer_data: InfluencerUpdate, db: Session = Depends(get_db)):
    influencers = await db.execute(select(Influencer).filter(Influencer.id == influencer_id))
    influencer = influencers.scalars().first()  # Get the first result
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")

    for key, value in influencer_data.dict(exclude_unset=True).items():
        setattr(influencer, key, value)

    await db.commit()
    await db.refresh(influencer)
    return influencer


# 4. Delete an Influencer by ID
@router.delete("/remove_influencer/{influencer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_influencer(influencer_id: int, db: Session = Depends(get_db)):
    influencers = await db.execute(select(Influencer).filter(Influencer.id == influencer_id))
    influencer = influencers.scalars().first()  # Get the first result
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")
    await db.delete(influencer)
    await db.commit()
    return


# 5. List All Influencers
@router.get("/list", response_model=List[InfluencerRead])
async def list_influencers(db: Session = Depends(get_db)):
    influencers = await db.execute(select(Influencer))
    all_influencers = influencers.scalars().all()
    return all_influencers


# 7. Set Influencer Availability
@router.put("/set_availability/{influencer_id}/{availability}", response_model=InfluencerRead)
async def update_influencer_availability(influencer_id: int, availability: bool, db: Session = Depends(get_db)):
    influencers = await db.execute(select(Influencer).filter(Influencer.id == influencer_id))
    influencer = influencers.scalars().first()
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")

    influencer.availability = bool(availability)
    await db.commit()
    await db.refresh(influencer)
    return influencer

# Define where you want to save the uploaded files
UPLOAD_DIRECTORY = "uploads/profile_pictures/"  # Make sure this directory exists


# 8. Update Influencer
# Pro# file Picture
@router.put("/update_profile_picture/{influencer_id}", response_model=InfluencerRead)
async def update_profile_picture(influencer_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    influencers = await db.execute(select(Influencer).filter(Influencer.id == influencer_id))
    influencer = influencers.scalars().first()
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")

    # Generate a unique filename to avoid conflicts
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIRECTORY, unique_filename)

    # Save the uploaded file to disk
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    # Save the file URL to the database
    influencer.profile_image_url = file_path  # You may adjust the path format for serving static files if needed
    await db.commit()
    await db.refresh(influencer)

    return influencer


# 9. Get All Available Influencers
@router.get("/influencers/available", response_model=List[InfluencerRead] | None)
async def get_available_influencers(db: Session = Depends(get_db)):
    influencers = await db.execute(select(Influencer).filter(Influencer.availability == True))
    influencers = influencers.scalars().all()
    return influencers


# 10. Search Influencers by Location
@router.get("/search/{location}", response_model=List[InfluencerRead])
async def search_influencers_by_location(location: str, db: Session = Depends(get_db)):
    influencers_search_query = await db.execute(select(Influencer).filter(Influencer.location.ilike(f"%{location}%")))
    influencers = influencers_search_query.scalars().all()
    return influencers


# 11. Search Influencers by Language
@router.get("/search_by_language/{language}", response_model=List[InfluencerRead])
async def search_influencers_by_language(language: str, db: Session = Depends(get_db)):
    # influencers = await db.query(Influencer).filter(Influencer.languages.ilike(f"%{language}%")).all()
    influencers_search_query = await db.execute(select(Influencer).filter(Influencer.languages.ilike(f"%{language}%")))
    influencers = influencers_search_query.scalars().all()
    return influencers


# 12. Get Influencers with High Growth Rate
@router.get("/high_growth", response_model=List[InfluencerRead])
async def get_high_growth_influencers(db: Session = Depends(get_db)):
    influencers_search_query = await db.execute(select(Influencer).filter(Influencer.growth_rate > 50))
    influencers = influencers_search_query.scalars().all()
    return influencers


# 13. Get Influencers by Number of Successful Campaigns
@router.get("/successful_campaigns/{min_campaigns}", response_model=List[InfluencerRead])
async def get_influencers_by_successful_campaigns(min_campaigns: int, db: Session = Depends(get_db)):
    # influencers = await db.query(Influencer).filter(Influencer.successful_campaigns >= min_campaigns).all()
    influencers_search_query = await db.execute(select(Influencer).filter(Influencer.successful_campaigns >= min_campaigns))
    influencers = influencers_search_query.scalars().all()
    return influencers


# 14. Filter Influencers by Rate per Post
@router.get("/get_rates/{min_rate}/{max_rate}", response_model=List[InfluencerRead])
async def filter_influencers_by_rate(max_rate: float, min_rate: float = 1, db: Session = Depends(get_db)):
    if max_rate < min_rate:
        raise HTTPException(status_code=404, detail=f"max rate cannot be lower than min rate ")

    # influencers = await db.query(Influencer).filter(Influencer.rate_per_post.between(min_rate, max_rate)).all()
    influencers_search_query = await db.execute(
        select(Influencer).filter(Influencer.rate_per_post.between(min_rate, max_rate)))
    influencers = influencers_search_query.scalars().all()
    return influencers

