from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PromotionMetricBase(BaseModel):
    promotion_id: int
    total_views: Optional[int]
    total_applications: Optional[int]
    qualified_applications: Optional[int]
    collaborations_initiated: Optional[int]
    collaborations_completed: Optional[int]
    collaborations_cancelled: Optional[int]
    total_budget_allocated: Optional[float]
    total_amount_spent: Optional[float]
    average_rate_paid: Optional[float]
    budget_utilization_percentage: Optional[float]
    average_response_time_hours: Optional[int]
    average_completion_time_days: Optional[int]
    time_to_first_application_hours: Optional[int]
    promotion_completion_rate: Optional[float]
    business_satisfaction_score: Optional[float]
    countries_reached: Optional[int]
    platforms_covered: Optional[int]

class PromotionMetricCreate(PromotionMetricBase):
    pass

class PromotionMetric(PromotionMetricBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 