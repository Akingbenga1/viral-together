from sqlalchemy import Column, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class InfluencerRecommendationSummaries(Base):
    __tablename__ = "influencer_recommendation_summaries"

    id = Column(Integer, primary_key=True, index=True)
    influencer_recommendation_id = Column(Integer, ForeignKey("influencer_recommendations.id"), nullable=False)
    influencer_id = Column(Integer, ForeignKey("influencers.id"), nullable=False)
    
    # Growth strategy summaries as JSONB
    more_followers = Column(JSON, nullable=True)
    content_ideas = Column(JSON, nullable=True)
    social_profiles = Column(JSON, nullable=True)
    influencer_collab = Column(JSON, nullable=True)
    business_collab = Column(JSON, nullable=True)
    content_scripts = Column(JSON, nullable=True)
    
    # Download links for generated files
    download_links = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    influencer_recommendation = relationship("InfluencerRecommendations", back_populates="summaries")
    influencer = relationship("Influencer", back_populates="recommendation_summaries")
