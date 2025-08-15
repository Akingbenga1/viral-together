from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime

class CoordinationSessionBase(BaseModel):
    user_id: int
    task_type: str = Field(..., min_length=1, max_length=100)
    initial_context: Dict[str, Any] = Field(default_factory=dict)

class CoordinationSessionCreate(CoordinationSessionBase):
    pass

class CoordinationSession(CoordinationSessionBase):
    coordination_uuid: str
    status: str = "active"
    created_at: datetime

    class Config:
        from_attributes = True

class TaskAssignmentBase(BaseModel):
    agent_id: int
    task_details: Dict[str, Any] = Field(default_factory=dict)

class TaskAssignment(TaskAssignmentBase):
    pass

class AgentContextRequest(BaseModel):
    user_id: int
    current_prompt: str
    agent_id: int
    context_window: int = Field(default=10, ge=1, le=100)

class AgentContextResponse(BaseModel):
    current_prompt: str
    conversation_history: List[Dict[str, Any]]
    agent_responses: List[Dict[str, Any]]
    context_metadata: Dict[str, Any] = Field(default_factory=dict)
