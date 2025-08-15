from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class BlogBase(BaseModel):
    topic: str
    description: Optional[str] = None
    body: str
    images: Optional[List[str]] = None
    cover_image_url: Optional[str] = None


class BlogCreate(BlogBase):
    author_id: int


class BlogUpdate(BaseModel):
    topic: Optional[str] = None
    description: Optional[str] = None
    body: Optional[str] = None
    images: Optional[List[str]] = None
    cover_image_url: Optional[str] = None


class BlogRead(BaseModel):
    id: int
    slug: str
    author_id: int
    topic: str
    description: Optional[str] = None
    body: str
    images: Optional[List[str]] = None
    cover_image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


