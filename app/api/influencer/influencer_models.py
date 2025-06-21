from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# A minimal Country schema for nesting in InfluencerRead
class CountryRead(BaseModel):
    id: int
    name: str
    code: str

    class Config:
        orm_mode = True

# A minimal User schema for nesting
class UserRead(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True

class InfluencerBase(BaseModel):
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    website_url: Optional[str] = None
    languages: Optional[str] = None
    availability: bool = True
    rate_per_post: Optional[float] = None
    total_posts: Optional[int] = None
    growth_rate: Optional[int] = None
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
        orm_mode = True

