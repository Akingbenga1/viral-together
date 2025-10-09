from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Promotion(Base):
    __tablename__ = 'promotions'
    id = Column(Integer, primary_key=True)
    uuid = Column(PG_UUID(as_uuid=True), nullable=True)
    business_id = Column(Integer, ForeignKey('businesses.id'), nullable=False)
    promotion_name = Column(String(255), nullable=False)
    promotion_item = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    discount = Column(Numeric(5, 2))
    budget = Column(Numeric(10, 2))
    spent_amount = Column(Numeric(10, 2), default=0)
    status = Column(String(50), default='pending')
    target_audience = Column(String(255))
    social_media_platform_id = Column(Integer, ForeignKey('social_media_platforms.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    location_requests = relationship("LocationPromotionRequest", back_populates="promotion")
    collaborations = relationship("Collaboration", back_populates="promotion") 