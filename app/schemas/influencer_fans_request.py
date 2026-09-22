from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime


class LocationData(BaseModel):
    """Location data for the invite request"""
    latitude: float
    longitude: float
    city_name: Optional[str] = None
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    region_name: Optional[str] = None
    region_code: Optional[str] = None


class InfluencerFansRequestCreate(BaseModel):
    """Schema for creating a new fans request"""
    influencer_id: int = Field(..., description="ID of the influencer being invited")
    country_id: int = Field(..., description="ID of the country where influencer is invited")
    requester_name: Optional[str] = Field(None, max_length=255, description="Name of the person making the request")
    requester_email: Optional[EmailStr] = Field(None, description="Email of the person making the request")
    message: Optional[str] = Field(None, description="Optional message to the influencer")

    # Location details
    city_name: Optional[str] = Field(None, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    country_code: Optional[str] = Field(None, max_length=10)
    country_name: Optional[str] = Field(None, max_length=255)
    region_name: Optional[str] = Field(None, max_length=255)
    region_code: Optional[str] = Field(None, max_length=50)

    class Config:
        json_schema_extra = {
            "example": {
                "influencer_id": 1,
                "country_id": 1,
                "requester_name": "John Doe",
                "requester_email": "john@example.com",
                "message": "We'd love to have you visit our city!",
                "city_name": "New York",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "country_code": "US",
                "country_name": "United States"
            }
        }


class InfluencerFansRequestUpdate(BaseModel):
    """Schema for updating a fans request"""
    status: Optional[str] = Field(None, description="Status: pending, acknowledged, declined")
    message: Optional[str] = Field(None, description="Optional message")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "acknowledged",
                "message": "Thank you for the invitation!"
            }
        }


class InfluencerFansRequestRead(BaseModel):
    """Schema for reading a fans request"""
    id: int
    uuid: str
    influencer_id: int
    requester_name: Optional[str] = None
    requester_email: Optional[str] = None
    country_id: int
    city_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    region_name: Optional[str] = None
    region_code: Optional[str] = None
    message: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InfluencerFansRequestWithInfluencer(InfluencerFansRequestRead):
    """Schema for reading a fans request with influencer details"""
    influencer_name: Optional[str] = None
    influencer_username: Optional[str] = None
    influencer_bio: Optional[str] = None
    influencer_profile_image: Optional[str] = None

    class Config:
        from_attributes = True


class InfluencerFansRequestsByCountry(BaseModel):
    """Grouped fans requests by country"""
    country_id: int
    country_name: str
    country_code: Optional[str] = None
    request_count: int
    requests: list[InfluencerFansRequestRead]

    class Config:
        from_attributes = True


class InfluencerListItem(BaseModel):
    """Simplified influencer info for list page"""
    id: int
    user_id: int
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    base_country_id: int
    base_country_name: Optional[str] = None
    social_media_handles: list[dict] = []
    total_requests: int = 0

    class Config:
        from_attributes = True


class InfluencerListResponse(BaseModel):
    """Paginated response for influencer list"""
    data: list[InfluencerListItem]
    total: int
    page: int
    limit: int
    total_pages: int

    class Config:
        from_attributes = True
