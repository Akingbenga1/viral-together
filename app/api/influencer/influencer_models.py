from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class InfluencerCreate(BaseModel):
    bio: Optional[str]
    profile_image_url: Optional[str]
    website_url: Optional[str]
    location: Optional[str]
    languages: Optional[str]
    availability: bool = True
    rate_per_post: Optional[float]
    total_posts: Optional[int]
    growth_rate: Optional[int]
    successful_campaigns: Optional[int]
    user_id: int

class InfluencerUpdate(BaseModel):
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    website_url: Optional[str] = None
    location: Optional[str] = None
    languages: Optional[str] = None
    availability: Optional[bool] = None
    rate_per_post: Optional[float] = None
    total_posts: Optional[int] = None
    growth_rate: Optional[int] = None
    successful_campaigns: Optional[int] = None

class InfluencerRead(BaseModel):
    id: int
    bio: Optional[str]
    profile_image_url: Optional[str]
    website_url: Optional[str]
    location: Optional[str]
    languages: Optional[str]
    availability: bool
    rate_per_post: Optional[float]
    total_posts: Optional[int]
    growth_rate: Optional[int]
    successful_campaigns: Optional[int]
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

