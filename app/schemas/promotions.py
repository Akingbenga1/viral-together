from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PromotionBase(BaseModel):
    business_id: int
    promotion_name: str
    promotion_item: str
    start_date: datetime
    end_date: datetime
    discount: Optional[float]
    budget: Optional[float]
    target_audience: Optional[str]
    social_media_platform_id: int

class PromotionCreate(PromotionBase):
    pass

class Promotion(PromotionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True 