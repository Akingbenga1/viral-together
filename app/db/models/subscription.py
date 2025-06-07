from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ARRAY, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.db.base import Base

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price_id = Column(String, nullable=False)  # Stripe price ID
    tier = Column(String, nullable=False)
    price_per_month = Column(Float, nullable=False)
    features = Column(ARRAY(String), nullable=False, default=[])
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    # subscriptions = relationship("UserSubscription", back_populates="plan")