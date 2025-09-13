from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

from uuid import UUID

from app.api.social_media_platform.social_media_platform_models import SocialMediaPlatformRead


class RateCardBase(BaseModel):
    content_type: Optional[str] = None
    base_rate: float
    audience_size_multiplier: Optional[float] = 1.0
    engagement_rate_multiplier: Optional[float] = 1.0
    exclusivity_fee: Optional[float] = 0.0
    usage_rights_fee: Optional[float] = 0.0
    revision_fee: Optional[float] = 0.0
    rush_fee: Optional[float] = 0.0
    description: Optional[str] = None

class RateCardCreate(RateCardBase):
    influencer_id: int
    platform_id: Optional[int] = None

class RateCardCreateResponse(RateCardCreate):
    id: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

class RateCardUpdate(BaseModel):
    content_type: Optional[str] = None
    base_rate: Optional[float] = None
    audience_size_multiplier: Optional[float] = None
    engagement_rate_multiplier: Optional[float] = None
    exclusivity_fee: Optional[float] = None
    usage_rights_fee: Optional[float] = None
    revision_fee: Optional[float] = None
    rush_fee: Optional[float] = None
    description: Optional[str] = None
    platform_id: Optional[int] = None

class RateCardRead(RateCardBase):
    id: int
    uuid: UUID
    influencer_id: int
    platform_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    total_rate: float
    platform: Optional[SocialMediaPlatformRead] = None

    class Config:
        from_attributes = True

class RateCardSummary(BaseModel):
    influencer_id: int
    content_types: List[str]
    min_rate: float
    max_rate: float
    avg_rate: float

    class Config:
        from_attributes = True

class RateProposalBase(BaseModel):
    proposed_rate: float
    content_type: str
    message: Optional[str] = None

class RateProposalCreate(RateProposalBase):
    influencer_id: int
    business_id: int
    platform_id: int

class RateProposalUpdate(BaseModel):
    proposed_rate: Optional[float] = None
    status: Optional[str] = None
    message: Optional[str] = None

class RateProposalRead(RateProposalBase):
    id: int
    uuid: UUID
    influencer_id: int
    business_id: int
    platform_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 