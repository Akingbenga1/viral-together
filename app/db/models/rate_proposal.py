from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid

class RateProposal(Base):
    __tablename__ = "rate_proposals"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    influencer_id = Column(Integer, ForeignKey("influencers.id", ondelete="CASCADE"), nullable=False)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    platform_id = Column(Integer, ForeignKey("social_media_platforms.id"), nullable=False)
    proposed_rate = Column(Float, nullable=False)
    content_type = Column(String, nullable=False)
    status = Column(String, default="pending")
    message = Column(String, nullable=True)
    influencer_approved = Column(String, nullable=True)  # New column
    business_approved = Column(String, nullable=True)  # New column
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    influencer = relationship("Influencer", back_populates="rate_proposals")
    business = relationship("Business", back_populates="rate_proposals")
    platform = relationship("SocialMediaPlatform") 