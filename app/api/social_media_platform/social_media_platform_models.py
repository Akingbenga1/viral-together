from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SocialMediaPlatformBase(BaseModel):
    name: str
    icon_url: Optional[str] = None
    description: Optional[str] = None

class SocialMediaPlatformCreate(SocialMediaPlatformBase):
    pass

class SocialMediaPlatformUpdate(BaseModel):
    name: Optional[str] = None
    icon_url: Optional[str] = None
    description: Optional[str] = None

class SocialMediaPlatformRead(SocialMediaPlatformBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 