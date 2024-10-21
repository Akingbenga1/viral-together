from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, DateTime, Numeric, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    website_url = Column(String(255), nullable=True)
    location = Column(String(100), nullable=True)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(20), nullable=True)
    industry = Column(String(100), nullable=True)
    logo_url = Column(String(255), nullable=True)  # URL of the business logo
    rating = Column(Float(precision=2), nullable=True)  # Average rating for the business
    verified = Column(Boolean(), default=False)  # Indicates whether the business is verified
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(100), nullable=True)  # Business category (optional)
    founded_year = Column(Integer, nullable=True)  # The year the business was founded
    number_of_employees = Column(Integer, nullable=True)  # Number of employees (optional)
    annual_revenue = Column(Numeric(precision=15, scale=2), nullable=True)  # Annual revenue (optional)
    active = Column(Boolean(), default=True)  # Whether the business is currently active
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

