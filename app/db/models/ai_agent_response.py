from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.base import Base

class AIAgentResponse(Base):
    __tablename__ = "ai_agent_responses"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    agent_id = Column(Integer, ForeignKey("ai_agents.id"), nullable=False)
    task_id = Column(String(255), nullable=False)  # UUID or task identifier
    response = Column(Text, nullable=False)
    response_type = Column(String(100), default="task_response")  # task_response, error, handoff
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    agent = relationship("AIAgent", back_populates="responses")
