from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# A minimal Country schema for nesting in InfluencerRead
class CountryRead(BaseModel):
    id: int
    name: str
    code: str

    class Config:
        from_attributes = True

# A minimal User schema for nesting
class UserRead(BaseModel):
    id: int
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True

class InfluencerBase(BaseModel):
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    website_url: Optional[str] = None
    languages: Optional[str] = None
    availability: Optional[bool] = True
    rate_per_post: Optional[float] = None
    total_posts: Optional[int] = None
    growth_rate: Optional[float] = None
    successful_campaigns: Optional[int] = None

class InfluencerCreate(InfluencerBase):
    user_id: int
    base_country_id: int
    collaboration_country_ids: List[int] = []

class InfluencerUpdate(InfluencerBase):
    base_country_id: Optional[int] = None
    collaboration_country_ids: Optional[List[int]] = None

class InfluencerRead(InfluencerBase):
    id: int
    user: UserRead
    base_country: CountryRead
    collaboration_countries: List[CountryRead] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class InfluencerSearchCriteria(BaseModel):
    country_ids: List[int]
    industry: Optional[str] = None
    social_media_platform: Optional[str] = None

class SocialMediaPlatformInput(BaseModel):
    social_media_platform_id: int  # Foreign key to social_media_platforms table
    handle: str  # Username, handle, or URL
    bio_url: Optional[str] = None  # Profile/bio URL
    follower_count: Optional[int] = None
    is_verified: Optional[bool] = False

class LocationInput(BaseModel):
    latitude: float
    longitude: float
    city_name: Optional[str] = None
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    region_name: Optional[str] = None
    region_code: Optional[str] = None
    display_name: Optional[str] = None

class InfluencerCreatePublic(InfluencerBase):
    first_name: str
    last_name: str
    username: str
    email: str
    password: Optional[str] = None  # Optional password
    base_country_id: int
    collaboration_country_ids: List[int] = []
    
    # Social media platforms (mandatory - at least one required)
    social_media_platforms: List[SocialMediaPlatformInput]
    
    # Locations
    base_location: LocationInput  # Required
    desired_location: Optional[LocationInput] = None  # Optional
    
    @validator('social_media_platforms')
    def validate_social_media_platforms(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one social media platform is required for influencer registration')
        return v

