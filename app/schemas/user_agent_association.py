from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class UserAgentAssociationBase(BaseModel):
    user_id: int
    agent_id: int
    association_type: Optional[str] = Field(None, min_length=1, max_length=100)
    is_primary: bool = Field(default=False, description="Whether this is the user's primary agent")
    priority: Optional[int] = Field(None, ge=1, description="Priority order for multiple agents")
    status: str = Field(default="active", min_length=1, max_length=50)

class UserAgentAssociationCreate(UserAgentAssociationBase):
    assigned_by: Optional[int] = Field(None, description="User ID who assigned this agent")

class UserAgentAssociationUpdate(BaseModel):
    association_type: Optional[str] = Field(None, min_length=1, max_length=100)
    is_primary: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1)
    status: Optional[str] = Field(None, min_length=1, max_length=50)

class UserAgentAssociation(UserAgentAssociationBase):
    id: int
    uuid: UUID
    assigned_at: datetime
    assigned_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
