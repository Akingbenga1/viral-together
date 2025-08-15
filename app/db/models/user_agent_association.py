from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.base import Base

class UserAgentAssociation(Base):
    __tablename__ = "user_agent_associations"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("ai_agents.id"), nullable=False)
    association_type = Column(String(100), nullable=True)  # primary, secondary, specialized, content_optimization, etc.
    is_primary = Column(Boolean, nullable=False, default=False)
    priority = Column(Integer, nullable=True)  # For ordering multiple agents per user
    status = Column(String(50), default="active")  # active, inactive, suspended
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Who assigned this agent
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="agent_associations", foreign_keys=[user_id])
    agent = relationship("AIAgent", back_populates="user_associations")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])
