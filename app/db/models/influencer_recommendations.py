from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.base import Base

class InfluencerRecommendations(Base):
    __tablename__ = "influencer_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_level = Column(String(50), nullable=False)  # beginner, intermediate, advanced
    base_plan = Column(JSON, nullable=False)
    enhanced_plan = Column(JSON, nullable=False)
    monthly_schedule = Column(JSON, nullable=False)
    performance_goals = Column(JSON, nullable=False)
    pricing_recommendations = Column(JSON, nullable=False)
    ai_insights = Column(JSON, nullable=True)
    coordination_uuid = Column(String(255), nullable=True)  # Link to coordination session
    status = Column(String(50), default="active")  # active, implemented, archived
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="recommendations")
