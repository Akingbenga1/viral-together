from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.auth import get_current_user
from app.db.models.social_media_platform import SocialMediaPlatform
from app.api.social_media_platform.social_media_platform_models import (
    SocialMediaPlatformCreate, SocialMediaPlatformRead, SocialMediaPlatformUpdate
)
from app.db.session import get_db
from app.schemas import User

router = APIRouter()

# 1. Create a Social Media Platform
@router.post("/create", response_model=SocialMediaPlatformRead)
async def create_social_media_platform(
    platform: SocialMediaPlatformCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if platform with the same name already exists
    existing_query = await db.execute(
        select(SocialMediaPlatform).filter(SocialMediaPlatform.name == platform.name)
    )
    existing = existing_query.scalars().first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"A platform with the name '{platform.name}' already exists"
        )
    
    # Create new platform
    new_platform = SocialMediaPlatform(**platform.dict())
    db.add(new_platform)
    await db.commit()
    await db.refresh(new_platform)
    
    return new_platform

# 2. Get All Social Media Platforms
@router.get("/list", response_model=List[SocialMediaPlatformRead], dependencies=[])
async def list_social_media_platforms(db: AsyncSession = Depends(get_db)):
    platforms_query = await db.execute(select(SocialMediaPlatform))
    platforms = platforms_query.scalars().all()
    return platforms

# 3. Get Social Media Platform by ID
@router.get("/{platform_id}", response_model=SocialMediaPlatformRead)
async def get_social_media_platform(platform_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    platform_query = await db.execute(
        select(SocialMediaPlatform).filter(SocialMediaPlatform.id == platform_id)
    )
    platform = platform_query.scalars().first()
    
    if not platform:
        raise HTTPException(status_code=404, detail="Social media platform not found")
    
    return platform

# 4. Update Social Media Platform
@router.put("/{platform_id}", response_model=SocialMediaPlatformRead)
async def update_social_media_platform(
    platform_id: int, 
    platform_data: SocialMediaPlatformUpdate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get the platform
    platform_query = await db.execute(
        select(SocialMediaPlatform).filter(SocialMediaPlatform.id == platform_id)
    )
    platform = platform_query.scalars().first()
    
    if not platform:
        raise HTTPException(status_code=404, detail="Social media platform not found")
    
    # Check if name is being updated and if it already exists
    if platform_data.name and platform_data.name != platform.name:
        existing_query = await db.execute(
            select(SocialMediaPlatform).filter(SocialMediaPlatform.name == platform_data.name)
        )
        existing = existing_query.scalars().first()
        
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"A platform with the name '{platform_data.name}' already exists"
            )
    
    # Update platform fields
    for key, value in platform_data.dict(exclude_unset=True).items():
        setattr(platform, key, value)
    
    await db.commit()
    await db.refresh(platform)
    
    return platform

# 5. Delete Social Media Platform
@router.delete("/{platform_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_social_media_platform(
    platform_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get the platform
    platform_query = await db.execute(
        select(SocialMediaPlatform).filter(SocialMediaPlatform.id == platform_id)
    )
    platform = platform_query.scalars().first()
    
    if not platform:
        raise HTTPException(status_code=404, detail="Social media platform not found")
    
    # Delete the platform
    await db.delete(platform)
    await db.commit()
    
    return 