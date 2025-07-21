from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base

class PromotionMetric(Base):
    __tablename__ = 'promotion_metrics'
    id = Column(Integer, primary_key=True)
    promotion_id = Column(Integer, ForeignKey('promotions.id'), nullable=False)
    total_views = Column(Integer)
    total_applications = Column(Integer)
    qualified_applications = Column(Integer)
    collaborations_initiated = Column(Integer)
    collaborations_completed = Column(Integer)
    collaborations_cancelled = Column(Integer)
    total_budget_allocated = Column(Numeric(12, 2))
    total_amount_spent = Column(Numeric(12, 2))
    average_rate_paid = Column(Numeric(10, 2))
    budget_utilization_percentage = Column(Numeric(5, 2))
    average_response_time_hours = Column(Integer)
    average_completion_time_days = Column(Integer)
    time_to_first_application_hours = Column(Integer)
    promotion_completion_rate = Column(Numeric(5, 2))
    business_satisfaction_score = Column(Numeric(3, 2))
    countries_reached = Column(Integer)
    platforms_covered = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now()) 