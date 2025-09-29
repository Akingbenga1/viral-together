from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class TaskStatusEnum(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskStatus(BaseModel):
    task_id: str
    status: TaskStatusEnum
    message: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_details: Optional[str] = None
    user_id: Optional[int] = None
    task_type: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: TaskStatusEnum
    message: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_details: Optional[str] = None
    user_id: Optional[int] = None
    task_type: str

class TaskCreateRequest(BaseModel):
    user_id: int
    task_type: str
    parameters: Optional[Dict[str, Any]] = None

class TaskListResponse(BaseModel):
    tasks: list[TaskStatusResponse]
    total: int
    page: int
    page_size: int
