from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

# Base schemas
class InfluencerCoachingGroupBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    is_paid: bool = False
    price: Optional[Decimal] = Field(None, ge=0)
    currency: str = Field(default="USD", max_length=3)
    max_members: Optional[int] = Field(None, ge=1)


class InfluencerCoachingGroupCreate(InfluencerCoachingGroupBase):
    pass

class InfluencerCoachingGroupUpdate(InfluencerCoachingGroupBase):
    name: Optional[str] = Field(None, max_length=255)
    is_paid: Optional[bool] = None
    is_active: Optional[bool] = None

class InfluencerCoachingGroup(InfluencerCoachingGroupBase):
    id: int
    coach_influencer_id: int
    current_members: int
    join_code: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }

# Member schemas
class InfluencerCoachingMemberBase(BaseModel):
    group_id: int
    member_influencer_id: int

class InfluencerCoachingMemberCreate(InfluencerCoachingMemberBase):
    join_code: str  # For joining with code
    payment_reference: Optional[str] = None

class InfluencerCoachingMemberUpdate(BaseModel):
    is_active: Optional[bool] = None
    payment_status: Optional[str] = Field(None, pattern="^(pending|paid|free)$")

class InfluencerCoachingMember(InfluencerCoachingMemberBase):
    id: int
    joined_at: datetime
    is_active: bool
    payment_status: str
    payment_reference: Optional[str] = None

    class Config:
        from_attributes = True

# Session schemas
class InfluencerCoachingSessionBase(BaseModel):
    group_id: int
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    session_date: datetime
    duration_minutes: Optional[int] = Field(None, ge=1)
    meeting_link: Optional[str] = None
    recording_url: Optional[str] = None
    materials: Optional[List[str]] = None

class InfluencerCoachingSessionCreate(InfluencerCoachingSessionBase):
    pass

class InfluencerCoachingSessionUpdate(InfluencerCoachingSessionBase):
    title: Optional[str] = Field(None, max_length=255)
    session_date: Optional[datetime] = None
    is_completed: Optional[bool] = None

class InfluencerCoachingSession(InfluencerCoachingSessionBase):
    id: int
    is_completed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Message schemas
class InfluencerCoachingMessageBase(BaseModel):
    group_id: int
    message: str
    message_type: str = Field(default="text", pattern="^(text|file|image|video)$")
    file_url: Optional[str] = None
    is_announcement: bool = False

class InfluencerCoachingMessageCreate(InfluencerCoachingMessageBase):
    pass

class InfluencerCoachingMessage(InfluencerCoachingMessageBase):
    id: int
    sender_influencer_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Response schemas
class CoachingGroupWithMembers(InfluencerCoachingGroup):
    members: List[InfluencerCoachingMember] = []

class CoachingGroupWithSessions(InfluencerCoachingGroup):
    sessions: List[InfluencerCoachingSession] = []

class CoachingGroupWithMessages(InfluencerCoachingGroup):
    messages: List[InfluencerCoachingMessage] = []

# Join group response
class JoinGroupResponse(BaseModel):
    success: bool
    message: str
    group: Optional[InfluencerCoachingGroup] = None
    member: Optional[InfluencerCoachingMember] = None

# Generate join code response
class GenerateJoinCodeResponse(BaseModel):
    join_code: str
    group_id: int
    message: str
