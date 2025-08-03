from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Re-using the minimal schemas from the influencer models for consistency
class CountryRead(BaseModel):
    id: int
    name: str
    code: str
    class Config:
        from_attributes = True

class UserRead(BaseModel):
    id: int
    username: str
    class Config:
        from_attributes = True

class BusinessBase(BaseModel):
    # Optional fields that can be set on create or update
    description: Optional[str] = None
    website_url: Optional[str] = None
    contact_phone: Optional[str] = None
    industry: Optional[str] = None
    logo_url: Optional[str] = None
    rating: Optional[float] = None
    verified: Optional[bool] = None
    active: Optional[bool] = True
    category: Optional[str] = None
    founded_year: Optional[int] = None
    number_of_employees: Optional[int] = None
    annual_revenue: Optional[float] = None

class BusinessCreate(BusinessBase):
    # Required fields for creation
    name: str
    contact_email: str
    owner_id: int
    base_country_id: int
    collaboration_country_ids: List[int] = []

class BusinessCreatePublic(BusinessBase):
    # Required fields for unauthenticated business creation
    name: str
    contact_email: str
    base_country_id: int
    collaboration_country_ids: List[int] = []
    
    # User creation fields
    first_name: str
    last_name: str
    username: str

class BusinessUpdate(BusinessBase):
    # Make all fields optional for updates
    name: Optional[str] = None
    contact_email: Optional[str] = None
    base_country_id: Optional[int] = None
    collaboration_country_ids: Optional[List[int]] = None

class BusinessRead(BusinessBase):
    id: int
    name: str
    contact_email: str
    user: UserRead
    base_country: CountryRead
    collaboration_countries: List[CountryRead] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
