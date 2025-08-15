from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.base import Base

class AIAgent(Base):
    __tablename__ = "ai_agents"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    agent_type = Column(String(100), nullable=False)  # e.g., "chat_support", "marketing", "analytics"
    capabilities = Column(JSON, nullable=False)  # {"capabilities": ["chat", "analysis"], "limitations": []}
    status = Column(String(50), default="active")  # active, inactive, busy
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    responses = relationship("AIAgentResponse", back_populates="agent")
    user_associations = relationship("UserAgentAssociation", back_populates="agent")
