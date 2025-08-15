from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime

class AIAgentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    agent_type: str = Field(..., min_length=1, max_length=100)
    capabilities: Dict = Field(..., description="Agent capabilities and limitations")

class AIAgentCreate(AIAgentBase):
    pass

class AIAgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    agent_type: Optional[str] = Field(None, min_length=1, max_length=100)
    capabilities: Optional[Dict] = None
    status: Optional[str] = Field(None, min_length=1, max_length=50)
    is_active: Optional[bool] = None

class AIAgent(AIAgentBase):
    id: int
    uuid: UUID
    status: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
