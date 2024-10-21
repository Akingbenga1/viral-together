from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class BusinessBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    website_url: Optional[str] = None
    location: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    industry: Optional[str] = None
    logo_url: Optional[str] = None
    rating: Optional[float] = None
    verified: Optional[bool] = None
    active: Optional[bool] = True
    founded_year: Optional[int] = None
    number_of_employees: Optional[int] = None
    annual_revenue: Optional[float] = None

class BusinessCreate(BusinessBase):
    owner_id: int

class BusinessUpdate(BusinessBase):
    pass

class BusinessRead(BusinessBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
