from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func
import uuid

from app.db.base import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False, index=True)  # 'promotion_created', 'collaboration_approved', etc.
    recipient_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    recipient_type = Column(String(20), nullable=False)  # 'influencer', 'business', 'admin'
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    event_metadata = Column(JSON, default=dict)  # Event-specific data
    
    # Email tracking
    email_enabled = Column(Boolean, default=True)
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime, nullable=True)
    email_error = Column(Text, nullable=True)
    
    # Twitter tracking
    twitter_enabled = Column(Boolean, default=True)
    twitter_posted = Column(Boolean, default=False)
    twitter_posted_at = Column(DateTime, nullable=True)
    twitter_error = Column(Text, nullable=True)
    twitter_post_id = Column(String(100), nullable=True)  # Twitter's tweet ID
    
    # Read status
    read_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    recipient = relationship("User", backref="notifications")

class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # 'promotion_created', 'collaboration_approved', etc.
    email_enabled = Column(Boolean, default=True)
    in_app_enabled = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", backref="notification_preferences")

class TwitterPost(Base):
    __tablename__ = "twitter_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True, default=uuid.uuid4)
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=True, index=True)
    event_type = Column(String(50), nullable=False)  # For standalone posts
    tweet_content = Column(Text, nullable=False)
    tweet_id = Column(String(100), nullable=True)  # Twitter's tweet ID
    status = Column(String(20), default='pending', index=True)  # 'pending', 'posted', 'failed'
    error_message = Column(Text, nullable=True)
    event_metadata = Column(JSON, default=dict)  # Event-specific data for tweet generation
    
    # Timestamps
    posted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    notification = relationship("Notification", backref="twitter_posts") 