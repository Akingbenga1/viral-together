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
    id: UUID
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

# Notification preferences schemas
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
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Twitter post schemas
class TwitterPostBase(BaseModel):
    event_type: str
    tweet_content: str
    event_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class TwitterPostCreate(TwitterPostBase):
    notification_id: Optional[UUID] = None

class TwitterPostResponse(TwitterPostBase):
    id: UUID
    notification_id: Optional[UUID]
    tweet_id: Optional[str]
    status: str
    error_message: Optional[str]
    posted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# API request/response schemas
class NotificationListRequest(BaseModel):
    event_type: Optional[str] = None
    read_status: Optional[bool] = None  # None=all, True=read, False=unread
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)

class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total_count: int
    unread_count: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool

class NotificationStatsResponse(BaseModel):
    total_notifications: int
    unread_count: int
    email_sent_count: int
    twitter_posted_count: int
    failed_emails: int
    failed_twitter_posts: int

# Bulk operations
class BulkNotificationRequest(BaseModel):
    notification_ids: List[UUID]

class BulkMarkReadRequest(BulkNotificationRequest):
    pass

class BulkDeleteRequest(BulkNotificationRequest):
    pass

# User preference management
class UserPreferencesUpdate(BaseModel):
    preferences: List[NotificationPreferenceUpdate]
    
class UserPreferencesResponse(BaseModel):
    user_id: int
    preferences: List[NotificationPreferenceResponse]

# WebSocket schemas
class WebSocketNotification(BaseModel):
    type: str = "notification"
    data: NotificationResponse

class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]

# Event-specific notification data schemas
class PromotionCreatedNotificationData(BaseModel):
    promotion_id: int
    promotion_name: str
    business_id: int
    business_name: str
    industry: Optional[str] = None
    budget: Optional[float] = None

class CollaborationCreatedNotificationData(BaseModel):
    collaboration_id: int
    collaboration_type: str
    promotion_id: int
    promotion_name: str
    business_id: int
    business_name: str
    influencer_id: int
    influencer_name: str
    proposed_amount: Optional[float] = None

class CollaborationApprovedNotificationData(BaseModel):
    collaboration_id: int
    collaboration_type: str
    promotion_id: int
    promotion_name: str
    business_id: int
    business_name: str
    influencer_id: int
    influencer_name: str
    approved_amount: Optional[float] = None

class InfluencerInterestNotificationData(BaseModel):
    collaboration_id: int
    promotion_id: int
    promotion_name: str
    business_id: int
    business_name: str
    influencer_id: int
    influencer_name: str
    proposed_amount: Optional[float] = None
    message: Optional[str] = None 