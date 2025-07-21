from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CollaborationBase(BaseModel):
    influencer_id: int
    promotion_id: int
    status: Optional[str] = 'pending'
    proposed_amount: Optional[float]
    negotiated_amount: Optional[float]
    negotiable: Optional[bool] = False
    collaboration_type: str
    deliverables: Optional[str]
    deadline: Optional[datetime]
    terms_and_conditions: Optional[str]
    contract_signed: Optional[bool] = False
    payment_status: Optional[str] = 'pending'
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

class CollaborationCreate(CollaborationBase):
    pass

class Collaboration(CollaborationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True 