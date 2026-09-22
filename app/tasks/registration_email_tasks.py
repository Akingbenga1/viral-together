from celery import Celery
from app.core.celery_app import celery_app
from app.services.email_service import email_service
from app.db.celery_session import SessionLocal
from sqlalchemy import text
import logging
import asyncio
from datetime import datetime
import json
import uuid

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="send_user_registration_email")
def send_user_registration_email(self, user_id: int, username: str, email: str):
    """
    Celery task to send welcome email for user registration
    """
    try:
        logger.info(f"Sending user registration email for user {user_id}")

        # Use synchronous database session for Celery workers
        with SessionLocal() as db:
            # Fetch user from database using raw SQL
            user_query = text("SELECT id, email, first_name, last_name, username FROM users WHERE id = :user_id")
            user_result = db.execute(user_query, {"user_id": user_id})
            user_row = user_result.fetchone()

            if not user_row:
                raise Exception(f"User {user_id} not found")

            logger.info(f"Found user: {user_row.email} for registration email")

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
                "username": username,
                "registration_date": datetime.utcnow().isoformat()
            }

            notification_result = db.execute(notification_query, {
                "uuid": str(uuid.uuid4()),
                "event_type": "user_registration",
                "title": "Welcome to Viral Together!",
                "message": "Thank you for joining Viral Together. Your account has been successfully created.",
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

            logger.info(f"Created notification {notification_id} for user registration")

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
                "event_type": "user_registration",
                "title": "Welcome to Viral Together!",
                "message": "Thank you for joining Viral Together. Your account has been successfully created.",
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
                    self.uuid = f"user-{user_data['id']}"
                    self.created_at = datetime.utcnow()

            class SimpleNotification:
                def __init__(self, notification_data):
                    self.id = notification_data['id']
                    self.event_type = notification_data['event_type']
                    self.title = notification_data['title']
                    self.message = notification_data['message']
                    self.event_metadata = notification_data['event_metadata']
                    self.recipient_user_id = notification_data['recipient_user_id']
                    self.recipient_type = notification_data['recipient_type']
                    self.email_enabled = True
                    self.email_sent = False
                    self.created_at = datetime.utcnow()

            # Create simple objects
            simple_user = SimpleUser(user_dict)
            simple_notification = SimpleNotification(notification_dict)

            # Send email using the existing email service
            try:
                asyncio.run(email_service.send_notification_email(simple_notification, simple_user))

                # Update notification as sent
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

                logger.info(f"User registration email sent successfully to {user_row.email}")
                return {"status": "success", "message": "User registration email sent successfully"}

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
        logger.error(f"Failed to send user registration email for user {user_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(bind=True, name="send_influencer_registration_email")
def send_influencer_registration_email(self, user_id: int, username: str, email: str, first_name: str, last_name: str):
    """
    Celery task to send welcome email for influencer registration
    """
    try:
        logger.info(f"Sending influencer registration email for user {user_id}")

        with SessionLocal() as db:
            # Fetch user from database
            user_query = text("SELECT id, email, first_name, last_name, username FROM users WHERE id = :user_id")
            user_result = db.execute(user_query, {"user_id": user_id})
            user_row = user_result.fetchone()

            if not user_row:
                raise Exception(f"User {user_id} not found")

            logger.info(f"Found influencer: {user_row.email} for registration email")

            # Create notification
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
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "registration_date": datetime.utcnow().isoformat(),
                "account_type": "influencer"
            }

            notification_result = db.execute(notification_query, {
                "uuid": str(uuid.uuid4()),
                "event_type": "influencer_registration",
                "title": "Welcome to Viral Together, Influencer!",
                "message": "Thank you for joining Viral Together as an influencer. Your profile has been successfully created.",
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

            logger.info(f"Created notification {notification_id} for influencer registration")

            # Create simple objects for email service
            user_dict = {
                "id": user_row.id,
                "email": user_row.email,
                "first_name": user_row.first_name or first_name,
                "last_name": user_row.last_name or last_name,
                "username": user_row.username
            }

            notification_dict = {
                "id": notification_id,
                "event_type": "influencer_registration",
                "title": "Welcome to Viral Together, Influencer!",
                "message": "Thank you for joining Viral Together as an influencer. Your profile has been successfully created.",
                "event_metadata": event_metadata,
                "recipient_user_id": user_id,
                "recipient_type": "user"
            }

            class SimpleUser:
                def __init__(self, user_data):
                    self.id = user_data['id']
                    self.email = user_data['email']
                    self.first_name = user_data.get('first_name', '')
                    self.last_name = user_data.get('last_name', '')
                    self.username = user_data['username']
                    self.uuid = f"user-{user_data['id']}"
                    self.created_at = datetime.utcnow()

            class SimpleNotification:
                def __init__(self, notification_data):
                    self.id = notification_data['id']
                    self.event_type = notification_data['event_type']
                    self.title = notification_data['title']
                    self.message = notification_data['message']
                    self.event_metadata = notification_data['event_metadata']
                    self.recipient_user_id = notification_data['recipient_user_id']
                    self.recipient_type = notification_data['recipient_type']
                    self.email_enabled = True
                    self.email_sent = False
                    self.created_at = datetime.utcnow()

            simple_user = SimpleUser(user_dict)
            simple_notification = SimpleNotification(notification_dict)

            # Send email
            try:
                asyncio.run(email_service.send_notification_email(simple_notification, simple_user))

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

                logger.info(f"Influencer registration email sent successfully to {user_row.email}")
                return {"status": "success", "message": "Influencer registration email sent successfully"}

            except Exception as email_error:
                logger.error(f"Failed to send email: {str(email_error)}")
                update_query = text("""
                    UPDATE notifications
                    SET email_sent = false, email_sent_at = NULL
                    WHERE id = :notification_id
                """)
                db.execute(update_query, {"notification_id": notification_id})
                db.commit()
                raise email_error

    except Exception as e:
        logger.error(f"Failed to send influencer registration email for user {user_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(bind=True, name="send_business_registration_email")
def send_business_registration_email(self, user_id: int, username: str, email: str, business_name: str, first_name: str, last_name: str):
    """
    Celery task to send welcome email for business registration
    """
    try:
        logger.info(f"Sending business registration email for user {user_id}")

        with SessionLocal() as db:
            # Fetch user from database
            user_query = text("SELECT id, email, first_name, last_name, username FROM users WHERE id = :user_id")
            user_result = db.execute(user_query, {"user_id": user_id})
            user_row = user_result.fetchone()

            if not user_row:
                raise Exception(f"User {user_id} not found")

            logger.info(f"Found business user: {user_row.email} for registration email")

            # Create notification
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
                "username": username,
                "business_name": business_name,
                "first_name": first_name,
                "last_name": last_name,
                "registration_date": datetime.utcnow().isoformat(),
                "account_type": "business"
            }

            notification_result = db.execute(notification_query, {
                "uuid": str(uuid.uuid4()),
                "event_type": "business_registration",
                "title": f"Welcome to Viral Together, {business_name}!",
                "message": f"Thank you for joining Viral Together as a business. Your business profile for {business_name} has been successfully created.",
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

            logger.info(f"Created notification {notification_id} for business registration")

            # Create simple objects for email service
            user_dict = {
                "id": user_row.id,
                "email": user_row.email,
                "first_name": user_row.first_name or first_name,
                "last_name": user_row.last_name or last_name,
                "username": user_row.username
            }

            notification_dict = {
                "id": notification_id,
                "event_type": "business_registration",
                "title": f"Welcome to Viral Together, {business_name}!",
                "message": f"Thank you for joining Viral Together as a business. Your business profile for {business_name} has been successfully created.",
                "event_metadata": event_metadata,
                "recipient_user_id": user_id,
                "recipient_type": "user"
            }

            class SimpleUser:
                def __init__(self, user_data):
                    self.id = user_data['id']
                    self.email = user_data['email']
                    self.first_name = user_data.get('first_name', '')
                    self.last_name = user_data.get('last_name', '')
                    self.username = user_data['username']
                    self.uuid = f"user-{user_data['id']}"
                    self.created_at = datetime.utcnow()

            class SimpleNotification:
                def __init__(self, notification_data):
                    self.id = notification_data['id']
                    self.event_type = notification_data['event_type']
                    self.title = notification_data['title']
                    self.message = notification_data['message']
                    self.event_metadata = notification_data['event_metadata']
                    self.recipient_user_id = notification_data['recipient_user_id']
                    self.recipient_type = notification_data['recipient_type']
                    self.email_enabled = True
                    self.email_sent = False
                    self.created_at = datetime.utcnow()

            simple_user = SimpleUser(user_dict)
            simple_notification = SimpleNotification(notification_dict)

            # Send email
            try:
                asyncio.run(email_service.send_notification_email(simple_notification, simple_user))

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

                logger.info(f"Business registration email sent successfully to {user_row.email}")
                return {"status": "success", "message": "Business registration email sent successfully"}

            except Exception as email_error:
                logger.error(f"Failed to send email: {str(email_error)}")
                update_query = text("""
                    UPDATE notifications
                    SET email_sent = false, email_sent_at = NULL
                    WHERE id = :notification_id
                """)
                db.execute(update_query, {"notification_id": notification_id})
                db.commit()
                raise email_error

    except Exception as e:
        logger.error(f"Failed to send business registration email for user {user_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)
