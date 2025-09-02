from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base

class InfluencerOperationalLocation(Base):
    """Single responsibility: Represent influencer operational location data"""
    __tablename__ = "influencer_operational_locations"
    
    id = Column(Integer, primary_key=True, index=True)
    influencer_id = Column(Integer, ForeignKey("influencers.id", ondelete="CASCADE"), nullable=False)
    city_name = Column(String(100), nullable=False)
    region_name = Column(String(100))
    region_code = Column(String(10))
    country_code = Column(String(2), nullable=False)
    country_name = Column(String(100), nullable=False)
    latitude = Column(Numeric(9, 6), nullable=False)
    longitude = Column(Numeric(9, 6), nullable=False)
    postcode = Column(String(20))
    time_zone = Column(String(50))
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationship only - no business logic
    influencer = relationship("Influencer", back_populates="operational_locations")

class BusinessOperationalLocation(Base):
    """Single responsibility: Represent business operational location data"""
    __tablename__ = "business_operational_locations"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    city_name = Column(String(100), nullable=False)
    region_name = Column(String(100))
    region_code = Column(String(10))
    country_code = Column(String(2), nullable=False)
    country_name = Column(String(100), nullable=False)
    latitude = Column(Numeric(9, 6), nullable=False)
    longitude = Column(Numeric(9, 6), nullable=False)
    postcode = Column(String(20))
    time_zone = Column(String(50))
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationship only - no business logic
    business = relationship("Business", back_populates="operational_locations")

class LocationPromotionRequest(Base):
    """Single responsibility: Represent location promotion request data"""
    __tablename__ = "location_promotion_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    promotion_id = Column(Integer, ForeignKey("promotions.id"), nullable=False)
    latitude = Column(Numeric(9, 6), nullable=False)
    longitude = Column(Numeric(9, 6), nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"))
    city = Column(String(100))
    region_name = Column(String(100))
    region_code = Column(String(10))
    postcode = Column(String(20))
    time_zone = Column(String(50))
    radius_km = Column(Integer, default=50)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships only - no business logic
    business = relationship("Business", back_populates="location_promotion_requests")
    promotion = relationship("Promotion", back_populates="location_requests")
    country = relationship("Country")
