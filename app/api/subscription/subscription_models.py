from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
from uuid import UUID

class SubscriptionPlanBase(BaseModel):
    name: str
    description: Optional[str] = None
    price_id: str  # Stripe price ID
    tier: str
    price_per_month: float
    features: List[str] = []

class SubscriptionPlanCreate(SubscriptionPlanBase):
    pass

class SubscriptionPlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price_id: Optional[str] = None
    tier: Optional[str] = None
    price_per_month: Optional[float] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None

class SubscriptionPlanRead(SubscriptionPlanBase):
    id: int
    uuid: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class UserSubscriptionBase(BaseModel):
    user_id: int
    plan_id: int
    stripe_subscription_id: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool = False

class UserSubscriptionCreate(BaseModel):
    plan_id: int
    payment_method_id: str

class UserSubscriptionUpdate(BaseModel):
    status: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: Optional[bool] = None

class UserSubscriptionRead(UserSubscriptionBase):
    id: int
    uuid: UUID
    created_at: datetime
    updated_at: datetime
    plan: SubscriptionPlanRead

    class Config:
        orm_mode = True

class CreateCheckoutSessionRequest(BaseModel):
    plan_id: int
    success_url: str
    cancel_url: str

class CheckoutSessionResponse(BaseModel):
    checkout_url: str

class CreatePortalSessionRequest(BaseModel):
    return_url: str

class PortalSessionResponse(BaseModel):
    portal_url: str

class WebhookEvent(BaseModel):
    event_type: str
    data: dict 