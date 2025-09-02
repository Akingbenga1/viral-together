from pydantic import BaseModel, Field, validator
from typing import Optional
from decimal import Decimal
from datetime import datetime

class LocationPromotionRequestBase(BaseModel):
    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)
    country_id: Optional[int] = None
    city: Optional[str] = Field(None, max_length=100)
    region_name: Optional[str] = Field(None, max_length=100)
    region_code: Optional[str] = Field(None, max_length=10)
    postcode: Optional[str] = Field(None, max_length=20)
    time_zone: Optional[str] = Field(None, max_length=50)
    radius_km: int = Field(50, ge=1, le=1000)

    @validator('latitude', 'longitude')
    def validate_coordinates(cls, v):
        if isinstance(v, str):
            try:
                v = Decimal(v)
            except:
                raise ValueError('Invalid coordinate format')
        return v

class LocationPromotionRequestCreate(LocationPromotionRequestBase):
    business_id: int
    promotion_id: int

class LocationPromotionRequestUpdate(LocationPromotionRequestBase):
    pass

class LocationPromotionRequest(LocationPromotionRequestBase):
    id: int
    business_id: int
    promotion_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LocationPromotionRequestWithDetails(LocationPromotionRequest):
    business_name: Optional[str] = None
    promotion_title: Optional[str] = None
    country_name: Optional[str] = None
    distance_km: Optional[float] = None
