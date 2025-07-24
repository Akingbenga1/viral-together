from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PromotionInterestBase(BaseModel):
    promotion_id: int
    influencer_id: int
    status: Optional[str] = 'pending'
    notes: Optional[str]

class PromotionInterestCreate(PromotionInterestBase):
    pass

class PromotionInterest(PromotionInterestBase):
    id: int
    expressed_interest: datetime

    class Config:
        from_attributes = True 