from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Promotion(Base):
    __tablename__ = 'promotions'
    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey('businesses.id'), nullable=False)
    promotion_name = Column(String(255), nullable=False)
    promotion_item = Column(String(255), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    discount = Column(Numeric(5, 2))
    budget = Column(Numeric(10, 2))
    target_audience = Column(String(255))
    social_media_platform_id = Column(Integer, ForeignKey('social_media_platforms.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Location relationships
    location_requests = relationship("LocationPromotionRequest", back_populates="promotion") 