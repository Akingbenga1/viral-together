from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class PromotionBase(BaseModel):
    business_id: int
    promotion_name: str
    promotion_item: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    discount: Optional[float] = None
    budget: Optional[float] = None
    spent_amount: Optional[float] = 0
    status: Optional[str] = 'pending'
    target_audience: Optional[str] = None
    social_media_platform_id: int

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def convert_timezone_aware_to_naive(cls, v):
        """Convert timezone-aware datetime to naive datetime for database storage"""
        if isinstance(v, datetime):
            # If datetime has timezone info, convert to UTC and remove timezone info
            if v.tzinfo is not None:
                # Convert to UTC first, then remove timezone info
                utc_dt = v.astimezone()
                return utc_dt.replace(tzinfo=None)
            return v
        return v

class PromotionCreate(PromotionBase):
    pass

class Promotion(PromotionBase):
    id: int
    uuid: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @field_validator('uuid', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID object to string"""
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True

class PromotionWithInfluencers(Promotion):
    influencers: Optional[List[dict]] = None

class PromotionStatusUpdate(BaseModel):
    status: str

class PromotionSpentUpdate(BaseModel):
    spent_amount: float 