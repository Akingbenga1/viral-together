from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, func, ForeignKey, Float
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.models.influencer_collaboration_country import influencer_collaboration_countries

class Influencer(Base):
    __tablename__ = "influencers"

    id = Column(Integer, primary_key=True, index=True)
    bio = Column(Text, nullable=True)
    profile_image_url = Column(String(255), nullable=True)
    website_url = Column(String(255), nullable=True)
    location = Column(String(100), nullable=True)
    languages = Column(String(255), nullable=True)
    availability = Column(Boolean(), default=True, nullable=False)
    rate_per_post = Column(Float, nullable=True)
    created_at = Column(DateTime(), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(), server_default=func.now(), onupdate=func.now(), nullable=False)
    total_posts = Column(Integer(),  nullable=True)
    growth_rate = Column(Float, nullable=True)
    successful_campaigns = Column(Integer(), default=0)
    base_country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    rate_cards = relationship("RateCard", back_populates="influencer")
    user = relationship("User")
    base_country = relationship("Country")
    collaboration_countries = relationship(
        "Country",
        secondary=influencer_collaboration_countries,
        backref="influencers_for_collaboration"
    )
    
    # Coaching relationships
    coaching_groups = relationship("InfluencerCoachingGroup", back_populates="coach")
    coaching_memberships = relationship("InfluencerCoachingMember", foreign_keys="InfluencerCoachingMember.member_influencer_id")
