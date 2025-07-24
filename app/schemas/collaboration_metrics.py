from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CollaborationMetricBase(BaseModel):
    collaboration_id: int
    initial_rate_proposed: Optional[float]
    final_rate_agreed: Optional[float]
    negotiation_rounds: Optional[int]
    time_to_agreement_hours: Optional[int]
    deliverables_submitted: Optional[int]
    deliverables_approved: Optional[int]
    deliverables_rejected: Optional[int]
    revision_requests: Optional[int]
    agreed_completion_date: Optional[datetime]
    actual_completion_date: Optional[datetime]
    days_early_or_late: Optional[int]
    business_rating: Optional[float]
    influencer_rating: Optional[float]
    collaboration_success: Optional[bool]
    payment_status: Optional[str]
    payment_completed_date: Optional[datetime]
    days_to_payment: Optional[int]

class CollaborationMetricCreate(CollaborationMetricBase):
    pass

class CollaborationMetric(CollaborationMetricBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 