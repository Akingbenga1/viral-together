from celery import Celery
from app.core.celery_app import celery_app
from app.services.email_service import email_service
from app.db.celery_session import SessionLocal
from sqlalchemy import text
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="send_password_reset_email")
def send_password_reset_email(self, user_id: int, reset_token: str, reset_url: str):
    """
    Celery task to send password reset email using database session
    """
    try:
        logger.info(f"Sending password reset email for user {user_id}")
        
        # Use synchronous database session for Celery workers
        with SessionLocal() as db:
            # Fetch user from database using raw SQL
            user_query = text("SELECT id, email, first_name, last_name, username FROM users WHERE id = :user_id")
            user_result = db.execute(user_query, {"user_id": user_id})
            user_row = user_result.fetchone()
            
            if not user_row:
                raise Exception(f"User {user_id} not found")
            
            logger.info(f"Found user: {user_row.email} for password reset")
            
            # Create notification using raw SQL
            notification_query = text("""
                INSERT INTO notifications (
                    uuid, event_type, title, message, recipient_user_id, recipient_type,
                    event_metadata, email_enabled, email_sent, twitter_enabled, 
                    twitter_posted, created_at
                ) VALUES (
                    :uuid, :event_type, :title, :message, :recipient_user_id, :recipient_type,
                    :event_metadata, :email_enabled, :email_sent, :twitter_enabled,
                    :twitter_posted, :created_at
                ) RETURNING id
            """)
            
            event_metadata = {
                "reset_token": reset_token,
                "reset_url": reset_url,
                "expires_in_hours": 1
            }
            
            import json
            import uuid
            notification_result = db.execute(notification_query, {
                "uuid": str(uuid.uuid4()),
                "event_type": "password_reset",
                "title": "Password Reset Request",
                "message": "You requested a password reset for your Viral Together account",
                "recipient_user_id": user_id,
                "recipient_type": "user",
                "event_metadata": json.dumps(event_metadata),
                "email_enabled": True,
                "email_sent": False,
                "twitter_enabled": False,
                "twitter_posted": False,
                "created_at": datetime.utcnow()
            })
            
            notification_id = notification_result.scalar()
            db.commit()
            
            logger.info(f"Created notification {notification_id} for password reset")
            
            # Convert database rows to dictionaries
            user_dict = {
                "id": user_row.id,
                "email": user_row.email,
                "first_name": user_row.first_name or "",
                "last_name": user_row.last_name or "",
                "username": user_row.username
            }
            
            notification_dict = {
                "id": notification_id,
                "event_type": "password_reset",
                "title": "Password Reset Request",
                "message": "You requested a password reset for your Viral Together account",
                "event_metadata": event_metadata,
                "recipient_user_id": user_id,
                "recipient_type": "user"
            }
            
            # Create simple objects that mimic the required interface
            class SimpleUser:
                def __init__(self, user_data):
                    self.id = user_data['id']
                    self.email = user_data['email']
                    self.first_name = user_data.get('first_name', '')
                    self.last_name = user_data.get('last_name', '')
                    self.username = user_data['username']
                    self.uuid = f"user-{user_data['id']}"  # Add uuid for email service
                    self.created_at = datetime.utcnow()  # Add created_at for email service
            
            class SimpleNotification:
                def __init__(self, notification_data):
                    self.id = notification_data['id']
                    self.event_type = notification_data['event_type']
                    self.title = notification_data['title']
                    self.message = notification_data['message']
                    self.event_metadata = notification_data['event_metadata']
                    self.recipient_user_id = notification_data['recipient_user_id']
                    self.recipient_type = notification_data['recipient_type']
                    self.email_enabled = True  # Add email_enabled for email service
                    self.email_sent = False  # Add email_sent for email service
                    self.created_at = datetime.utcnow()  # Add created_at for email service
            
            # Create simple objects
            simple_user = SimpleUser(user_dict)
            simple_notification = SimpleNotification(notification_dict)
            
            # Send email using the existing email service with simple objects
            try:
                asyncio.run(email_service.send_notification_email(simple_notification, simple_user))
                
                # Update notification as sent using raw SQL
                update_query = text("""
                    UPDATE notifications 
                    SET email_sent = true, email_sent_at = :email_sent_at 
                    WHERE id = :notification_id
                """)
                db.execute(update_query, {
                    "email_sent_at": datetime.utcnow(),
                    "notification_id": notification_id
                })
                db.commit()
                
                logger.info(f"Password reset email sent successfully to {user_row.email}")
                return {"status": "success", "message": "Password reset email sent successfully"}
                
            except Exception as email_error:
                logger.error(f"Failed to send email: {str(email_error)}")
                # Update notification as failed
                update_query = text("""
                    UPDATE notifications 
                    SET email_sent = false, email_sent_at = NULL 
                    WHERE id = :notification_id
                """)
                db.execute(update_query, {"notification_id": notification_id})
                db.commit()
                raise email_error
        
    except Exception as e:
        logger.error(f"Failed to send password reset email for user {user_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)
