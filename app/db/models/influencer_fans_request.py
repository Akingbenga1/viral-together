from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import uuid as uuid_lib


class InfluencerFansRequest(Base):
    """
    Table to store fan/user requests inviting influencers to specific locations
    """
    __tablename__ = 'influencer_fans_requests'

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid_lib.uuid4()), nullable=False)

    # Influencer being invited
    influencer_id = Column(Integer, ForeignKey('influencers.id', ondelete='CASCADE'), nullable=False, index=True)

    # Requester information (anonymous users only)
    requester_name = Column(String(255), nullable=True)
    requester_email = Column(String(255), nullable=True)

    # Location where influencer is requested to visit
    country_id = Column(Integer, ForeignKey('countries.id', ondelete='RESTRICT'), nullable=False, index=True)
    city_name = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    country_code = Column(String(10), nullable=True)
    country_name = Column(String(255), nullable=True)
    region_name = Column(String(255), nullable=True)
    region_code = Column(String(50), nullable=True)

    # Request details
    message = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default='pending', index=True)  # pending, acknowledged, declined

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    influencer = relationship("Influencer", back_populates="fans_requests")
    country = relationship("Country")
