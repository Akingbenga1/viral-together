from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

class InfluencersTargetsBase(BaseModel):
    posting_frequency: Optional[str] = None
    engagement_goals: Optional[str] = None
    follower_growth: Optional[str] = None
    pricing: Optional[Decimal] = Field(None, ge=0)  # Changed from pricing_strategy
    pricing_currency: str = Field(default="USD", max_length=3)  # New field
    estimated_hours_per_week: Optional[str] = None
    content_types: Optional[List[str]] = None  # JSON will handle this automatically
    platform_recommendations: Optional[List[str]] = None
    content_creation_tips: Optional[List[str]] = None

class InfluencersTargetsCreate(InfluencersTargetsBase):
    pass

class InfluencersTargetsUpdate(InfluencersTargetsBase):
    pass

class InfluencersTargets(InfluencersTargetsBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }
