from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base

class Influencer(Base):
    __tablename__ = "influencers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bio = Column(Text, nullable=True)
    profile_image_url = Column(String(255), nullable=True)
    website_url = Column(String(255), nullable=True)
    location = Column(String(100), nullable=True)
    languages = Column(String(255), nullable=True)
    availability = Column(Boolean(), default=True, nullable=False)
    rate_per_post = Column(Numeric(precision=10, scale=2), nullable=True)
    created_at = Column(DateTime(), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(), server_default=func.now(), onupdate=func.now(), nullable=False)
    total_posts = Column(Integer(),  nullable=True)
    growth_rate = Column(Numeric(precision=5, scale=2), nullable=True)
    successful_campaigns = Column(Integer(), nullable=True)

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    rate_cards = relationship("RateCard", back_populates="influencer")
