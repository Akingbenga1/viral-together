import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func, or_
from fastapi import BackgroundTasks

from app.db.models.notification import Notification, NotificationPreference, TwitterPost
from app.db.models.user import User
from app.schemas.notification import (
    NotificationCreate, 
    NotificationResponse,
    PromotionCreatedNotificationData,
    CollaborationCreatedNotificationData,
    CollaborationApprovedNotificationData,
    InfluencerInterestNotificationData
)

logger = logging.getLogger(__name__)

class NotificationService:
    """Core service for handling all notification operations"""
    
    def __init__(self):
        self.email_service = None  # Will be injected
        self.twitter_service = None  # Will be injected
        self.websocket_service = None  # Will be injected
    
    def set_services(self, email_service=None, twitter_service=None, websocket_service=None):
        """Inject dependent services"""
        if email_service:
            self.email_service = email_service
        if twitter_service:
            self.twitter_service = twitter_service
        if websocket_service:
            self.websocket_service = websocket_service
    
    async def create_notification(
        self, 
        db: AsyncSession, 
        notification_data: NotificationCreate,
        background_tasks: BackgroundTasks
    ) -> Notification:
        """Create a new notification and trigger background processing"""
        
        # Check user preferences
        user_prefs = await self._get_user_preferences(db, notification_data.recipient_user_id, notification_data.event_type)
        
        # Apply user preferences to notification
        email_enabled = notification_data.email_enabled and user_prefs.get('email_enabled', True)
        twitter_enabled = notification_data.twitter_enabled and user_prefs.get('twitter_enabled', True)
        
        # Create notification record
        db_notification = Notification(
            event_type=notification_data.event_type,
            recipient_user_id=notification_data.recipient_user_id,
            recipient_type=notification_data.recipient_type,
            title=notification_data.title,
            message=notification_data.message,
            event_metadata=notification_data.event_metadata,
            email_enabled=email_enabled,
            twitter_enabled=twitter_enabled
        )
        
        db.add(db_notification)
        await db.commit()
        await db.refresh(db_notification)
        
        logger.info(f"Created notification {db_notification.id} for user {notification_data.recipient_user_id}: {notification_data.title}")
        
        # Schedule background processing
        background_tasks.add_task(self._process_notification_background, db_notification.id)
        
        return db_notification
    
    async def _process_notification_background(self, notification_id: UUID):
        """Background task to process notification (email, Twitter, WebSocket)"""
        try:
            from app.db.database import get_db_session
            async with get_db_session() as db:
                # Get notification
                result = await db.execute(
                    select(Notification, User)
                    .join(User, Notification.recipient_user_id == User.id)
                    .where(Notification.id == notification_id)
                )
                notification_data = result.first()
                
                if not notification_data:
                    logger.error(f"Notification {notification_id} not found for background processing")
                    return
                
                notification, user = notification_data
                
                # Process email if enabled
                if notification.email_enabled and self.email_service:
                    await self._send_email_notification(db, notification, user)
                
                # Process Twitter if enabled
                if notification.twitter_enabled and self.twitter_service:
                    await self._send_twitter_notification(db, notification)
                
                # Send WebSocket notification if connected
                if self.websocket_service:
                    await self._send_websocket_notification(notification, user)
                
        except Exception as e:
            logger.error(f"Error processing notification {notification_id}: {str(e)}")
    
    async def _send_email_notification(self, db: AsyncSession, notification: Notification, user: User):
        """Send email notification with retry logic"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                await self.email_service.send_notification_email(
                    to_email=user.email,
                    notification=notification,
                    user=user
                )
                
                # Update notification as sent
                notification.email_sent = True
                notification.email_sent_at = datetime.utcnow()
                notification.email_error = None
                await db.commit()
                
                logger.info(f"Email sent successfully for notification {notification.id} to {user.email}")
                break
                
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                logger.error(f"Email send failed (attempt {retry_count}/{max_retries}) for notification {notification.id}: {error_msg}")
                
                if retry_count >= max_retries:
                    notification.email_error = error_msg
                    await db.commit()
                else:
                    # Wait before retry (exponential backoff)
                    await asyncio.sleep(2 ** retry_count)
    
    async def _send_twitter_notification(self, db: AsyncSession, notification: Notification):
        """Send Twitter notification with retry logic"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                tweet_id = await self.twitter_service.post_notification_tweet(notification)
                
                # Update notification as posted
                notification.twitter_posted = True
                notification.twitter_posted_at = datetime.utcnow()
                notification.twitter_post_id = tweet_id
                notification.twitter_error = None
                await db.commit()
                
                logger.info(f"Twitter post successful for notification {notification.id}, tweet ID: {tweet_id}")
                break
                
            except Exception as e:
                retry_count += 1
                error_msg = str(e)
                logger.error(f"Twitter post failed (attempt {retry_count}/{max_retries}) for notification {notification.id}: {error_msg}")
                
                if retry_count >= max_retries:
                    notification.twitter_error = error_msg
                    await db.commit()
                else:
                    # Wait before retry
                    await asyncio.sleep(2 ** retry_count)
    
    async def _send_websocket_notification(self, notification: Notification, user: User):
        """Send real-time WebSocket notification"""
        try:
            await self.websocket_service.send_notification_to_user(
                user_id=user.id,
                notification=notification
            )
            logger.info(f"WebSocket notification sent for notification {notification.id} to user {user.id}")
        except Exception as e:
            logger.error(f"WebSocket notification failed for notification {notification.id}: {str(e)}")
    
    async def _get_user_preferences(self, db: AsyncSession, user_id: int, event_type: str) -> Dict[str, bool]:
        """Get user notification preferences for specific event type"""
        result = await db.execute(
            select(NotificationPreference)
            .where(and_(
                NotificationPreference.user_id == user_id,
                NotificationPreference.event_type == event_type
            ))
        )
        preference = result.scalar_one_or_none()
        
        if preference:
            return {
                'email_enabled': preference.email_enabled,
                'in_app_enabled': preference.in_app_enabled
            }
        
        # Default preferences if none set
        return {
            'email_enabled': True,
            'in_app_enabled': True
        }
    
    # Event-specific notification creation methods
    async def create_promotion_created_notification(
        self, 
        db: AsyncSession, 
        data: PromotionCreatedNotificationData,
        background_tasks: BackgroundTasks
    ) -> List[Notification]:
        """Create notifications for new promotion (to relevant influencers)"""
        notifications = []
        
        # Get influencers who might be interested (simplified - can be enhanced with targeting logic)
        influencer_users = await self._get_influencer_users(db)
        
        for user in influencer_users:
            notification_data = NotificationCreate(
                event_type="promotion_created",
                recipient_user_id=user.id,
                recipient_type="influencer",
                title=f"New Promotion: {data.promotion_name}",
                message=f"{data.business_name} has created a new promotion '{data.promotion_name}' that might interest you!",
                event_metadata={
                    "promotion_id": data.promotion_id,
                    "promotion_name": data.promotion_name,
                    "business_id": data.business_id,
                    "business_name": data.business_name,
                    "industry": data.industry,
                    "budget": data.budget
                }
            )
            
            notification = await self.create_notification(db, notification_data, background_tasks)
            notifications.append(notification)
        
        return notifications
    
    async def create_collaboration_created_notification(
        self, 
        db: AsyncSession, 
        data: CollaborationCreatedNotificationData,
        background_tasks: BackgroundTasks
    ) -> Notification:
        """Create notification for new collaboration"""
        # Notify business about new collaboration
        business_user = await self._get_business_user(db, data.business_id)
        
        if business_user:
            notification_data = NotificationCreate(
                event_type="collaboration_created",
                recipient_user_id=business_user.id,
                recipient_type="business",
                title=f"New Collaboration Request",
                message=f"{data.influencer_name} is interested in your promotion '{data.promotion_name}'",
                event_metadata={
                    "collaboration_id": data.collaboration_id,
                    "collaboration_type": data.collaboration_type,
                    "promotion_id": data.promotion_id,
                    "promotion_name": data.promotion_name,
                    "business_id": data.business_id,
                    "business_name": data.business_name,
                    "influencer_id": data.influencer_id,
                    "influencer_name": data.influencer_name,
                    "proposed_amount": data.proposed_amount
                }
            )
            
            return await self.create_notification(db, notification_data, background_tasks)
    
    async def create_collaboration_approved_notification(
        self, 
        db: AsyncSession, 
        data: CollaborationApprovedNotificationData,
        background_tasks: BackgroundTasks
    ) -> Notification:
        """Create notification for approved collaboration"""
        # Notify influencer about approval
        influencer_user = await self._get_influencer_user(db, data.influencer_id)
        
        if influencer_user:
            notification_data = NotificationCreate(
                event_type="collaboration_approved",
                recipient_user_id=influencer_user.id,
                recipient_type="influencer",
                title=f"Collaboration Approved!",
                message=f"{data.business_name} has approved your collaboration request for '{data.promotion_name}'",
                event_metadata={
                    "collaboration_id": data.collaboration_id,
                    "collaboration_type": data.collaboration_type,
                    "promotion_id": data.promotion_id,
                    "promotion_name": data.promotion_name,
                    "business_id": data.business_id,
                    "business_name": data.business_name,
                    "influencer_id": data.influencer_id,
                    "influencer_name": data.influencer_name,
                    "approved_amount": data.approved_amount
                }
            )
            
            return await self.create_notification(db, notification_data, background_tasks)
    
    async def create_influencer_interest_notification(
        self, 
        db: AsyncSession, 
        data: InfluencerInterestNotificationData,
        background_tasks: BackgroundTasks
    ) -> Notification:
        """Create notification when influencer shows interest"""
        # Notify business about influencer interest
        business_user = await self._get_business_user(db, data.business_id)
        
        if business_user:
            notification_data = NotificationCreate(
                event_type="influencer_interest",
                recipient_user_id=business_user.id,
                recipient_type="business",
                title=f"New Interest in {data.promotion_name}",
                message=f"{data.influencer_name} has shown interest in your promotion '{data.promotion_name}'",
                event_metadata={
                    "collaboration_id": data.collaboration_id,
                    "promotion_id": data.promotion_id,
                    "promotion_name": data.promotion_name,
                    "business_id": data.business_id,
                    "business_name": data.business_name,
                    "influencer_id": data.influencer_id,
                    "influencer_name": data.influencer_name,
                    "proposed_amount": data.proposed_amount,
                    "message": data.message
                }
            )
            
            return await self.create_notification(db, notification_data, background_tasks)
    
    # Helper methods for getting users
    async def _get_influencer_users(self, db: AsyncSession) -> List[User]:
        """Get all influencer users"""
        from app.db.models.influencer import Influencer
        result = await db.execute(
            select(User)
            .join(Influencer, User.id == Influencer.user_id)
        )
        return result.scalars().all()
    
    async def _get_business_user(self, db: AsyncSession, business_id: int) -> Optional[User]:
        """Get user associated with business"""
        from app.db.models.business import Business
        result = await db.execute(
            select(User)
            .join(Business, User.id == Business.user_id)
            .where(Business.id == business_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_influencer_user(self, db: AsyncSession, influencer_id: int) -> Optional[User]:
        """Get user associated with influencer"""
        from app.db.models.influencer import Influencer
        result = await db.execute(
            select(User)
            .join(Influencer, User.id == Influencer.user_id)
            .where(Influencer.id == influencer_id)
        )
        return result.scalar_one_or_none()
    
    # Notification management methods
    async def get_notifications(
        self, 
        db: AsyncSession, 
        user_id: int,
        event_type: Optional[str] = None,
        read_status: Optional[bool] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get paginated notifications for a user with filters"""
        
        # Build query filters
        filters = [Notification.recipient_user_id == user_id]
        
        if event_type:
            filters.append(Notification.event_type == event_type)
        
        if read_status is not None:
            if read_status:
                filters.append(Notification.read_at.isnot(None))
            else:
                filters.append(Notification.read_at.is_(None))
        
        if date_from:
            filters.append(Notification.created_at >= date_from)
        
        if date_to:
            filters.append(Notification.created_at <= date_to)
        
        # Get total count
        count_result = await db.execute(
            select(func.count(Notification.id))
            .where(and_(*filters))
        )
        total_count = count_result.scalar()
        
        # Get unread count
        unread_result = await db.execute(
            select(func.count(Notification.id))
            .where(and_(
                Notification.recipient_user_id == user_id,
                Notification.read_at.is_(None)
            ))
        )
        unread_count = unread_result.scalar()
        
        # Get notifications with pagination
        offset = (page - 1) * limit
        result = await db.execute(
            select(Notification)
            .where(and_(*filters))
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        notifications = result.scalars().all()
        
        return {
            "notifications": notifications,
            "total_count": total_count,
            "unread_count": unread_count,
            "page": page,
            "limit": limit,
            "has_next": total_count > (page * limit),
            "has_prev": page > 1
        }
    
    async def mark_notification_read(self, db: AsyncSession, notification_id: UUID, user_id: int) -> Optional[Notification]:
        """Mark a notification as read"""
        result = await db.execute(
            select(Notification)
            .where(and_(
                Notification.id == notification_id,
                Notification.recipient_user_id == user_id
            ))
        )
        notification = result.scalar_one_or_none()
        
        if notification and not notification.read_at:
            notification.read_at = datetime.utcnow()
            await db.commit()
            await db.refresh(notification)
            logger.info(f"Marked notification {notification_id} as read for user {user_id}")
        
        return notification
    
    async def delete_notification(self, db: AsyncSession, notification_id: UUID, user_id: int) -> bool:
        """Delete a notification (soft delete by setting read_at)"""
        result = await db.execute(
            select(Notification)
            .where(and_(
                Notification.id == notification_id,
                Notification.recipient_user_id == user_id
            ))
        )
        notification = result.scalar_one_or_none()
        
        if notification:
            await db.delete(notification)
            await db.commit()
            logger.info(f"Deleted notification {notification_id} for user {user_id}")
            return True
        
        return False

# Global notification service instance
notification_service = NotificationService() 