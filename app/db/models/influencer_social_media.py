from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class InfluencerSocialMedia(Base):
    """Single responsibility: Represent influencer social media account data"""
    __tablename__ = "influencer_social_media"
    
    id = Column(Integer, primary_key=True, index=True)
    influencer_id = Column(Integer, ForeignKey("influencers.id", ondelete="CASCADE"), nullable=False)
    social_media_platform_id = Column(Integer, ForeignKey("social_media_platforms.id", ondelete="CASCADE"), nullable=False)
    handle = Column(String(255), nullable=False)  # Username, handle, or URL
    bio_url = Column(String(500), nullable=True)  # Profile/bio URL
    follower_count = Column(Integer, nullable=True)
    is_verified = Column(String(10), default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships only - no business logic
    influencer = relationship("Influencer", back_populates="social_media_accounts")
    platform = relationship("SocialMediaPlatform")

