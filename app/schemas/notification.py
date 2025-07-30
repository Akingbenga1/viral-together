from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID

# Base notification schemas
class NotificationBase(BaseModel):
    event_type: str = Field(..., description="Type of event that triggered the notification")
    recipient_user_id: int = Field(..., description="ID of the user receiving the notification")
    recipient_type: str = Field(..., description="Type of recipient: influencer, business, admin")
    title: str = Field(..., max_length=255, description="Notification title")
    message: str = Field(..., description="Notification message content")
    event_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional event data")

class NotificationCreate(NotificationBase):
    email_enabled: Optional[bool] = True
    twitter_enabled: Optional[bool] = True

class NotificationUpdate(BaseModel):
    read_at: Optional[datetime] = None
    email_enabled: Optional[bool] = None
    twitter_enabled: Optional[bool] = None

class NotificationResponse(NotificationBase):
    id: int
    uuid: UUID
    email_sent: bool
    email_sent_at: Optional[datetime]
    email_error: Optional[str]
    twitter_posted: bool
    twitter_posted_at: Optional[datetime]
    twitter_error: Optional[str]
    twitter_post_id: Optional[str]
    read_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Notification preference schemas
class NotificationPreferenceBase(BaseModel):
    user_id: int
    event_type: str
    email_enabled: bool = True
    in_app_enabled: bool = True

class NotificationPreferenceCreate(NotificationPreferenceBase):
    pass

class NotificationPreferenceUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None

class NotificationPreferenceResponse(NotificationPreferenceBase):
    id: int
    uuid: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Twitter post schemas
class TwitterPostBase(BaseModel):
    notification_id: Optional[int] = None
    event_type: str
    tweet_content: str

class TwitterPostCreate(TwitterPostBase):
    pass

class TwitterPostResponse(TwitterPostBase):
    id: int
    uuid: UUID
    notification_id: Optional[int]
    tweet_id: Optional[str]
    status: str
    error_message: Optional[str]
    event_metadata: Optional[Dict[str, Any]]
    posted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# List and filter schemas
class NotificationListRequest(BaseModel):
    event_type: Optional[str] = None
    recipient_type: Optional[str] = None
    read: Optional[bool] = None
    email_sent: Optional[bool] = None
    twitter_posted: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)

class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    page: int
    limit: int
    total_pages: int

# Statistics schema
class NotificationStatsResponse(BaseModel):
    total_notifications: int
    unread_notifications: int
    email_sent_count: int
    twitter_posted_count: int
    by_event_type: Dict[str, int]
    by_recipient_type: Dict[str, int]

# Bulk operation schemas
class BulkNotificationRequest(BaseModel):
    notification_ids: List[int]

class BulkMarkReadRequest(BaseModel):
    notification_ids: List[int]
    read_at: Optional[datetime] = None

class BulkDeleteRequest(BaseModel):
    notification_ids: List[int]

# User preferences schemas
class UserPreferencesUpdate(BaseModel):
    promotion_created_email: Optional[bool] = None
    promotion_created_in_app: Optional[bool] = None
    collaboration_created_email: Optional[bool] = None
    collaboration_created_in_app: Optional[bool] = None
    collaboration_approved_email: Optional[bool] = None
    collaboration_approved_in_app: Optional[bool] = None
    influencer_interest_email: Optional[bool] = None
    influencer_interest_in_app: Optional[bool] = None

class UserPreferencesResponse(BaseModel):
    user_id: int
    preferences: Dict[str, Dict[str, bool]]  # {event_type: {email_enabled: bool, in_app_enabled: bool}}

# WebSocket schemas
class WebSocketNotification(BaseModel):
    id: int
    uuid: UUID
    event_type: str
    title: str
    message: str
    event_metadata: Optional[Dict[str, Any]]
    created_at: datetime

class WebSocketMessage(BaseModel):
    type: str  # 'notification', 'system', 'error'
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

# Event-specific notification data schemas (for internal service use)
class PromotionCreatedNotificationData(BaseModel):
    promotion_id: int
    promotion_name: str
    business_id: int
    business_name: str
    industry: Optional[str]
    budget: Optional[float]

class CollaborationCreatedNotificationData(BaseModel):
    collaboration_id: int
    promotion_id: int
    promotion_name: str
    influencer_id: int
    influencer_name: str
    business_id: int
    business_name: str
    collaboration_type: Optional[str] = None
    proposed_amount: Optional[float] = None

class CollaborationApprovedNotificationData(BaseModel):
    collaboration_id: int
    promotion_id: int
    promotion_name: str
    influencer_id: int
    influencer_name: str
    business_id: int
    business_name: str
    collaboration_type: Optional[str] = None
    approved_amount: Optional[float] = None

class InfluencerInterestNotificationData(BaseModel):
    collaboration_id: int
    promotion_id: int
    promotion_name: str
    influencer_id: int
    influencer_name: str
    business_id: int
    business_name: str
    proposed_amount: Optional[float] = None
    message: Optional[str] = None 