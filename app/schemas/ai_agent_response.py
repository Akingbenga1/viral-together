from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class AIAgentResponseBase(BaseModel):
    agent_id: int
    task_id: str = Field(..., min_length=1, max_length=255)
    response: str = Field(..., min_length=1)
    response_type: str = Field(default="task_response", min_length=1, max_length=100)

class AIAgentResponseCreate(AIAgentResponseBase):
    pass

class AIAgentResponseUpdate(BaseModel):
    response: Optional[str] = Field(None, min_length=1)
    response_type: Optional[str] = Field(None, min_length=1, max_length=100)

class AIAgentResponse(AIAgentResponseBase):
    id: int
    uuid: UUID
    created_at: datetime

    class Config:
        from_attributes = True
