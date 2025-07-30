import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func, or_
from fastapi import BackgroundTasks
import time
import traceback

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
from app.services.email_service import EmailService
from app.services.twitter_service import TwitterService
from app.services.websocket_service import WebSocketService

logger = logging.getLogger(__name__)

class NotificationService:
    """Core service for handling all notification operations"""
    
    def __init__(self):
        self.email_service = EmailService()
        self.twitter_service = TwitterService()
        self.websocket_service = WebSocketService()
    
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
        start_time = time.time()
        
        logger.info(f"🚀 NOTIFICATION_START: Creating {notification_data.event_type} notification for user {notification_data.recipient_user_id}")
        logger.debug(f"Notification payload: title='{notification_data.title}', email_enabled={notification_data.email_enabled}, twitter_enabled={notification_data.twitter_enabled}")
        
        try:
            # Get user preferences
            user_prefs = await self._get_user_preferences(db, notification_data.recipient_user_id, notification_data.event_type)
            
            # Apply user preferences to notification
            email_enabled = notification_data.email_enabled and user_prefs.get('email_enabled', True)
            twitter_enabled = notification_data.twitter_enabled and user_prefs.get('twitter_enabled', True)
            
            logger.debug(f"User preferences applied: email_enabled={email_enabled}, twitter_enabled={twitter_enabled}")
            
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
            
            creation_time = time.time() - start_time
            logger.info(f"✅ NOTIFICATION_CREATED: ID={db_notification.id}, UUID={db_notification.uuid}, user={notification_data.recipient_user_id}, type={notification_data.event_type}, time={creation_time:.3f}s")
            
            # Schedule background processing
            logger.info(f"📤 NOTIFICATION_DISPATCH: Scheduling background processing for notification {db_notification.id}")
            background_tasks.add_task(self._process_notification_background, db_notification.id)
            
            return db_notification
            
        except Exception as e:
            creation_time = time.time() - start_time
            logger.error(f"❌ NOTIFICATION_CREATION_FAILED: user={notification_data.recipient_user_id}, type={notification_data.event_type}, time={creation_time:.3f}s")
            logger.error(f"Exception details: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            raise
    
    async def _process_notification_background(self, notification_id: int):
        """Background task to process notification (email, Twitter, WebSocket)"""
        start_time = time.time()
        logger.info(f"🔄 NOTIFICATION_PROCESSING_START: Processing notification {notification_id} in background")
        
        channels_attempted = []
        channels_successful = []
        channels_failed = []
        
        try:
            from app.db.database import get_db_session
            async with get_db_session() as db:
                # Get notification
                result = await db.execute(
                    select(Notification).where(Notification.id == notification_id)
                )
                notification = result.scalar_one_or_none()
                
                if not notification:
                    logger.error(f"❌ NOTIFICATION_NOT_FOUND: Notification {notification_id} not found for background processing")
                    return
                
                # Get user
                user_result = await db.execute(
                    select(User).where(User.id == notification.recipient_user_id)
                )
                user = user_result.scalar_one_or_none()
                
                if not user:
                    logger.error(f"❌ USER_NOT_FOUND: User {notification.recipient_user_id} not found for notification {notification_id}")
                    return
                
                logger.info(f"📧 EMAIL_CHANNEL: Processing email for notification {notification_id} (enabled: {notification.email_enabled})")
                # Process email notification
                if notification.email_enabled:
                    channels_attempted.append("email")
                    try:
                        await self._send_email_notification(db, notification, user)
                        channels_successful.append("email")
                        logger.info(f"✅ EMAIL_SUCCESS: Email sent for notification {notification_id}")
                    except Exception as e:
                        channels_failed.append("email")
                        logger.error(f"❌ EMAIL_FAILED: Email failed for notification {notification_id}: {str(e)}")
                        logger.error(f"Email exception trace: {traceback.format_exc()}")
                
                logger.info(f"🐦 TWITTER_CHANNEL: Processing Twitter for notification {notification_id} (enabled: {notification.twitter_enabled})")
                # Process Twitter notification
                if notification.twitter_enabled:
                    channels_attempted.append("twitter")
                    try:
                        await self._send_twitter_notification(db, notification)
                        channels_successful.append("twitter")
                        logger.info(f"✅ TWITTER_SUCCESS: Tweet posted for notification {notification_id}")
                    except Exception as e:
                        channels_failed.append("twitter")
                        logger.error(f"❌ TWITTER_FAILED: Twitter failed for notification {notification_id}: {str(e)}")
                        logger.error(f"Twitter exception trace: {traceback.format_exc()}")
                
                logger.info(f"🔌 WEBSOCKET_CHANNEL: Processing WebSocket for notification {notification_id}")
                # Process WebSocket notification
                channels_attempted.append("websocket")
                try:
                    await self._send_websocket_notification(notification, user)
                    channels_successful.append("websocket")
                    logger.info(f"✅ WEBSOCKET_SUCCESS: WebSocket sent for notification {notification_id}")
                except Exception as e:
                    channels_failed.append("websocket")
                    logger.error(f"❌ WEBSOCKET_FAILED: WebSocket failed for notification {notification_id}: {str(e)}")
                    logger.error(f"WebSocket exception trace: {traceback.format_exc()}")
                
                processing_time = time.time() - start_time
                success_rate = len(channels_successful) / len(channels_attempted) if channels_attempted else 0
                
                logger.info(f"🏁 NOTIFICATION_PROCESSING_COMPLETE: ID={notification_id}")
                logger.info(f"📊 PROCESSING_METRICS: time={processing_time:.3f}s, attempted={channels_attempted}, successful={channels_successful}, failed={channels_failed}, success_rate={success_rate:.2%}")
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"💥 NOTIFICATION_PROCESSING_EXCEPTION: Critical failure processing notification {notification_id} after {processing_time:.3f}s")
            logger.error(f"Critical exception: {str(e)}")
            logger.error(f"Full stack trace: {traceback.format_exc()}")

    async def _send_email_notification(self, db: AsyncSession, notification: Notification, user: User):
        """Send email notification with comprehensive logging (single attempt)"""
        start_time = time.time()
        logger.info(f"📧 EMAIL_START: Sending email for notification {notification.id} to {user.email}")
        
        try:
            logger.debug(f"📧 EMAIL_ATTEMPT: Single attempt for notification {notification.id}")
            
            await self.email_service.send_notification_email(notification, user)
            
            # Update notification status
            notification.email_sent = True
            notification.email_sent_at = datetime.utcnow()
            await db.commit()
            
            send_time = time.time() - start_time
            logger.info(f"✅ EMAIL_SENT_SUCCESS: notification={notification.id}, recipient={user.email}, time={send_time:.3f}s")
            return
                
        except Exception as e:
            send_time = time.time() - start_time
            error_msg = str(e)
            
            # Single attempt failure
            notification.email_error = error_msg
            await db.commit()
            
            logger.error(f"❌ EMAIL_FAILURE: notification={notification.id}, recipient={user.email}, time={send_time:.3f}s")
            logger.error(f"Email error: {error_msg}")
            logger.error(f"Email stack trace: {traceback.format_exc()}")
            raise

    async def _send_twitter_notification(self, db: AsyncSession, notification: Notification):
        """Send Twitter notification with comprehensive logging (single attempt)"""
        start_time = time.time()
        logger.info(f"🐦 TWITTER_START: Posting tweet for notification {notification.id}")
        
        try:
            logger.debug(f"🐦 TWITTER_ATTEMPT: Single attempt for notification {notification.id}")
            
            tweet_id = await self.twitter_service.post_notification_tweet(notification)
            
            if tweet_id:
                # Update notification status
                notification.twitter_posted = True
                notification.twitter_posted_at = datetime.utcnow()
                notification.twitter_post_id = tweet_id
                await db.commit()
                
                post_time = time.time() - start_time
                logger.info(f"✅ TWITTER_POST_SUCCESS: notification={notification.id}, tweet_id={tweet_id}, time={post_time:.3f}s")
                return
            else:
                raise Exception("Tweet ID not returned from Twitter service")
                
        except Exception as e:
            post_time = time.time() - start_time
            error_msg = str(e)
            
            # Single attempt failure
            notification.twitter_error = error_msg
            await db.commit()
            
            logger.error(f"❌ TWITTER_FAILURE: notification={notification.id}, time={post_time:.3f}s")
            logger.error(f"Twitter error: {error_msg}")
            logger.error(f"Twitter stack trace: {traceback.format_exc()}")
            raise

    async def _send_websocket_notification(self, notification: Notification, user: User):
        """Send WebSocket notification with comprehensive logging"""
        start_time = time.time()
        logger.info(f"🔌 WEBSOCKET_START: Sending WebSocket notification {notification.id} to user {user.id}")
        
        try:
            await self.websocket_service.send_notification_to_user(notification, user.id)
            
            send_time = time.time() - start_time
            logger.info(f"✅ WEBSOCKET_SENT_SUCCESS: notification={notification.id}, user={user.id}, time={send_time:.3f}s")
            
        except Exception as e:
            send_time = time.time() - start_time
            logger.error(f"❌ WEBSOCKET_SEND_FAILURE: notification={notification.id}, user={user.id}, time={send_time:.3f}s")
            logger.error(f"WebSocket error: {str(e)}")
            logger.error(f"WebSocket stack trace: {traceback.format_exc()}")
            raise
    
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
    ) -> Notification:
        """Create notifications for new promotion (to relevant influencers)"""
        logger.info(f"🎯 PROMOTION_NOTIFICATION: Creating promotion_created notification for promotion {data.promotion_id}")
        logger.debug(f"Promotion details: name='{data.promotion_name}', business='{data.business_name}', budget={data.budget}")
        
        # Find all influencers to notify
        from app.db.models.influencer import Influencer
        result = await db.execute(select(Influencer))
        influencers = result.scalars().all()
        
        notifications_created = []
        
        for influencer in influencers:
            if influencer.user_id:
                notification_data = NotificationCreate(
                    event_type="promotion_created",
                    recipient_user_id=influencer.user_id,
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
                notifications_created.append(notification.id)
        
        logger.info(f"✅ PROMOTION_NOTIFICATIONS_CREATED: promotion={data.promotion_id}, notifications_count={len(notifications_created)}, notification_ids={notifications_created}")
        return notifications_created[0] if notifications_created else None
    
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
            .join(Business, User.id == Business.owner_id)
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
    
    async def mark_notification_read(self, db: AsyncSession, notification_id: int, user_id: int) -> Optional[Notification]:
        """Mark a notification as read"""
        logger.info(f"📖 MARK_READ_START: Marking notification {notification_id} as read for user {user_id}")
        
        try:
            result = await db.execute(
                select(Notification)
                .where(and_(
                    Notification.id == notification_id,
                    Notification.recipient_user_id == user_id
                ))
            )
            notification = result.scalar_one_or_none()
            
            if notification:
                notification.read_at = datetime.utcnow()
                await db.commit()
                await db.refresh(notification)
                
                logger.info(f"✅ MARK_READ_SUCCESS: notification={notification_id}, user={user_id}")
                return notification
            else:
                logger.warning(f"⚠️ MARK_READ_NOT_FOUND: notification={notification_id}, user={user_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ MARK_READ_FAILURE: notification={notification_id}, user={user_id}")
            logger.error(f"Mark read error: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            raise

    async def delete_notification(self, db: AsyncSession, notification_id: int, user_id: int) -> bool:
        """Delete a notification (soft delete by setting read_at)"""
        logger.info(f"🗑️ DELETE_START: Deleting notification {notification_id} for user {user_id}")
        
        try:
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
                logger.info(f"✅ DELETE_SUCCESS: notification={notification_id}, user={user_id}")
                return True
            else:
                logger.warning(f"⚠️ DELETE_NOT_FOUND: notification={notification_id}, user={user_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ DELETE_FAILURE: notification={notification_id}, user={user_id}")
            logger.error(f"Delete error: {str(e)}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            raise

# Global notification service instance
notification_service = NotificationService() 