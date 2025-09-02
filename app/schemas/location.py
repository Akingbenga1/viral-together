from pydantic import BaseModel, Field, validator
from typing import Optional, List
from decimal import Decimal
from datetime import datetime

class LocationBase(BaseModel):
    city_name: str = Field(..., min_length=1, max_length=100)
    region_name: Optional[str] = Field(None, max_length=100)
    region_code: Optional[str] = Field(None, max_length=10)
    country_code: str = Field(..., min_length=2, max_length=2)
    country_name: str = Field(..., min_length=1, max_length=100)
    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)
    postcode: Optional[str] = Field(None, max_length=20)
    time_zone: Optional[str] = Field(None, max_length=50)
    is_primary: bool = False

    @validator('latitude', 'longitude')
    def validate_coordinates(cls, v):
        if isinstance(v, str):
            try:
                v = Decimal(v)
            except:
                raise ValueError('Invalid coordinate format')
        return v

class InfluencerLocationCreate(LocationBase):
    pass

class InfluencerLocationUpdate(LocationBase):
    pass

class InfluencerLocation(LocationBase):
    id: int
    influencer_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class BusinessLocationCreate(LocationBase):
    pass

class BusinessLocationUpdate(LocationBase):
    pass

class BusinessLocation(LocationBase):
    id: int
    business_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class LocationSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    country_code: Optional[str] = Field(None, min_length=2, max_length=2)
    limit: int = Field(10, ge=1, le=50)

class LocationSearchResult(BaseModel):
    display_name: str
    latitude: Decimal
    longitude: Decimal
    city: Optional[str]
    region: Optional[str]
    country: Optional[str]
    country_code: Optional[str]

class GeocodeRequest(BaseModel):
    address: str = Field(..., min_length=1)
    country_code: Optional[str] = Field(None, min_length=2, max_length=2)

class ReverseGeocodeRequest(BaseModel):
    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)
