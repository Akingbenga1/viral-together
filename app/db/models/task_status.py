"""
Database model for task status tracking
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.db.base import Base

class TaskStatus(Base):
    """Task status tracking model"""
    
    __tablename__ = "task_status"
    
    task_id = Column(String(255), primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    task_type = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)  # created, processing, completed, failed, cancelled
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    result = Column(JSON, nullable=True)
    error_details = Column(Text, nullable=True)
    celery_task_id = Column(String(255), nullable=True, index=True)  # Celery task ID for tracking
    task_data = Column(JSON, nullable=True)  # Original task data
    
    def __repr__(self):
        return f"<TaskStatus(task_id='{self.task_id}', status='{self.status}')>"
