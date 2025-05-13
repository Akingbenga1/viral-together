from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid

class RateCard(Base):
    __tablename__ = "rate_cards"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    influencer_id = Column(Integer, ForeignKey("influencers.id", ondelete="CASCADE"), nullable=False)
    platform_id = Column(Integer, ForeignKey("social_media_platforms.id"), nullable=True)
    content_type = Column(String, nullable=False)  
    base_rate = Column(Float, nullable=False)
    audience_size_multiplier = Column(Float, default=1.0)
    engagement_rate_multiplier = Column(Float, default=1.0)
    exclusivity_fee = Column(Float, default=0.0)
    usage_rights_fee = Column(Float, default=0.0)
    revision_fee = Column(Float, default=0.0)
    rush_fee = Column(Float, default=0.0)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    influencer = relationship("Influencer", back_populates="rate_cards")
    platform = relationship("SocialMediaPlatform", foreign_keys=[platform_id])

    def calculate_total_rate(self):
        """Calculate the total rate based on all factors"""
        total = self.base_rate
        total *= self.audience_size_multiplier
        total *= self.engagement_rate_multiplier
        total += self.exclusivity_fee
        total += self.usage_rights_fee
        total += self.revision_fee
        total += self.rush_fee
        return total