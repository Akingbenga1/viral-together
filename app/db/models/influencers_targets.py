from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, DECIMAL, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class InfluencersTargets(Base):
    __tablename__ = "influencers_targets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    posting_frequency = Column(String(100), nullable=True)
    engagement_goals = Column(String(200), nullable=True)
    follower_growth = Column(String(100), nullable=True)
    pricing = Column(DECIMAL(10, 2), nullable=True)  # Changed from pricing_strategy
    pricing_currency = Column(String(3), nullable=False, default="USD")  # New column
    estimated_hours_per_week = Column(String(50), nullable=True)
    content_types = Column(JSON, nullable=True)  # Changed to JSON for better list handling
    platform_recommendations = Column(JSON, nullable=True)  # Changed to JSON
    content_creation_tips = Column(JSON, nullable=True)  # Changed to JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    user = relationship("User", back_populates="influencer_targets")
