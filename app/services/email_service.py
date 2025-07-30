import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime
import smtplib
import time
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings
from app.db.models.notification import Notification
from app.db.models.user import User

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.jinja_env = Environment(
            loader=FileSystemLoader('app/templates/email'),
            autoescape=select_autoescape(['html', 'xml'])
        )
        self._validate_config()

    def _validate_config(self):
        """Validate email configuration and log setup details"""
        logger.info(f"📧 EMAIL_SERVICE_INIT: Initializing email service")
        logger.info(f"📧 EMAIL_CONFIG: backend={settings.EMAIL_BACKEND}, enabled={settings.EMAIL_NOTIFICATIONS_ENABLED}")
        
        if not settings.EMAIL_NOTIFICATIONS_ENABLED:
            logger.warning(f"⚠️ EMAIL_DISABLED: Email notifications are disabled in configuration")
            return
            
        if settings.EMAIL_BACKEND == "smtp":
            logger.info(f"📧 SMTP_CONFIG: host={settings.SMTP_HOST}, port={settings.SMTP_PORT}, user={settings.SMTP_USERNAME}")
        elif settings.EMAIL_BACKEND == "sendgrid":
            logger.info(f"📧 SENDGRID_CONFIG: API key configured={bool(settings.SENDGRID_API_KEY)}")
        elif settings.EMAIL_BACKEND == "mailgun":
            logger.info(f"📧 MAILGUN_CONFIG: domain={settings.MAILGUN_DOMAIN}, API key configured={bool(settings.MAILGUN_API_KEY)}")

    async def send_notification_email(self, notification: Notification, user: User):
        """Send notification email with comprehensive monitoring"""
        start_time = time.time()
        
        logger.info(f"📧 EMAIL_SEND_START: notification={notification.id}, recipient={user.email}, event_type={notification.event_type}")
        logger.debug(f"📧 EMAIL_CONTEXT: title='{notification.title}', backend={settings.EMAIL_BACKEND}")
        
        if not settings.EMAIL_NOTIFICATIONS_ENABLED:
            logger.warning(f"⚠️ EMAIL_SKIPPED: Email notifications disabled, skipping notification {notification.id}")
            return

        try:
            # Generate email content
            content_start_time = time.time()
            logger.debug(f"📧 EMAIL_CONTENT_START: Generating email content for {notification.event_type}")
            
            subject = await self._generate_email_subject(notification)
            html_content = await self._generate_html_content(notification, user)
            plain_content = await self._generate_plain_content(notification, user)
            
            content_time = time.time() - content_start_time
            logger.debug(f"📧 EMAIL_CONTENT_COMPLETE: time={content_time:.3f}s, subject='{subject}', html_length={len(html_content) if html_content else 0}")

            # Send via configured backend
            send_start_time = time.time()
            
            if settings.EMAIL_BACKEND == "smtp":
                logger.info(f"📧 EMAIL_SMTP_START: Sending via SMTP for notification {notification.id}")
                await self._send_via_smtp(user.email, subject, html_content, plain_content)
                
            elif settings.EMAIL_BACKEND == "sendgrid":
                logger.info(f"📧 EMAIL_SENDGRID_START: Sending via SendGrid for notification {notification.id}")
                await self._send_via_sendgrid(user.email, subject, html_content, plain_content)
                
            elif settings.EMAIL_BACKEND == "mailgun":
                logger.info(f"📧 EMAIL_MAILGUN_START: Sending via Mailgun for notification {notification.id}")
                await self._send_via_mailgun(user.email, subject, html_content, plain_content)
                
            else:
                raise ValueError(f"Unsupported email backend: {settings.EMAIL_BACKEND}")

            send_time = time.time() - send_start_time
            total_time = time.time() - start_time
            
            logger.info(f"✅ EMAIL_SEND_SUCCESS: notification={notification.id}, recipient={user.email}, backend={settings.EMAIL_BACKEND}")
            logger.info(f"📊 EMAIL_METRICS: send_time={send_time:.3f}s, total_time={total_time:.3f}s, subject='{subject}'")

        except Exception as e:
            total_time = time.time() - start_time
            error_msg = str(e)
            
            logger.error(f"❌ EMAIL_SEND_FAILURE: notification={notification.id}, recipient={user.email}, backend={settings.EMAIL_BACKEND}, time={total_time:.3f}s")
            logger.error(f"Email error details: {error_msg}")
            logger.error(f"Email stack trace: {traceback.format_exc()}")
            raise

    async def _send_via_smtp(self, to_email: str, subject: str, html_content: str, plain_content: str):
        """Send email via SMTP with detailed logging"""
        logger.debug(f"📧 SMTP_CONNECT_START: Connecting to {settings.SMTP_HOST}:{settings.SMTP_PORT}")
        logger.debug(f"📧 SMTP_CONFIG USERNAME: user={settings.SMTP_USERNAME}")
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.DEFAULT_EMAIL_FROM
            msg['To'] = to_email

            # Add content
            if plain_content:
                msg.attach(MIMEText(plain_content, 'plain'))
            if html_content:
                msg.attach(MIMEText(html_content, 'html'))

            # Connect and send
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                logger.debug(f"📧 SMTP_AUTH: Authenticating with {settings.SMTP_USERNAME}")
                
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.starttls()
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                
                logger.debug(f"📧 SMTP_SEND: Sending message to {to_email}")
                server.send_message(msg)
                
            logger.info(f"✅ SMTP_SUCCESS: Email sent to {to_email}")

        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP_ERROR: SMTP specific error sending to {to_email}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"❌ SMTP_FAILURE: General error sending to {to_email}: {str(e)}")
            raise

    async def _send_via_sendgrid(self, to_email: str, subject: str, html_content: str, plain_content: str):
        """Send email via SendGrid with detailed logging"""
        logger.debug(f"📧 SENDGRID_PREPARE: Preparing SendGrid message for {to_email}")
        
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail
            
            logger.debug(f"📧 SENDGRID_CLIENT: Initializing SendGrid client")
            sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
            
            message = Mail(
                from_email=settings.DEFAULT_EMAIL_FROM,
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=plain_content
            )
            
            logger.debug(f"📧 SENDGRID_SEND: Sending message via SendGrid API")
            response = sg.send(message)
            
            logger.info(f"✅ SENDGRID_SUCCESS: Email sent with status {response.status_code}")
            logger.debug(f"SendGrid response headers: {dict(response.headers)}")
            
        except ImportError:
            logger.error(f"❌ SENDGRID_IMPORT_ERROR: SendGrid library not available")
            raise Exception("SendGrid library not installed. Install with: pip install sendgrid")
        except Exception as e:
            logger.error(f"❌ SENDGRID_FAILURE: SendGrid API error: {str(e)}")
            raise

    async def _send_via_mailgun(self, to_email: str, subject: str, html_content: str, plain_content: str):
        """Send email via Mailgun with detailed logging"""
        logger.debug(f"📧 MAILGUN_PREPARE: Preparing Mailgun request for {to_email}")
        
        try:
            import requests
            
            logger.debug(f"📧 MAILGUN_API: Making API request to Mailgun")
            
            response = requests.post(
                f"https://api.mailgun.net/v3/{settings.MAILGUN_DOMAIN}/messages",
                auth=("api", settings.MAILGUN_API_KEY),
                data={
                    "from": settings.DEFAULT_EMAIL_FROM,
                    "to": [to_email],
                    "subject": subject,
                    "text": plain_content,
                    "html": html_content
                }
            )
            
            if response.status_code == 200:
                logger.info(f"✅ MAILGUN_SUCCESS: Email sent via Mailgun")
                logger.debug(f"Mailgun response: {response.json()}")
            else:
                raise Exception(f"Mailgun API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ MAILGUN_FAILURE: Mailgun API error: {str(e)}")
            raise

    async def _generate_email_subject(self, notification: Notification) -> str:
        """Generate email subject with logging"""
        logger.debug(f"📧 SUBJECT_GENERATE: Generating subject for {notification.event_type}")
        
        try:
            subject_templates = {
                'promotion_created': "🎯 New Promotion Available: {{event_metadata.promotion_name}}",
                'collaboration_created': "🤝 New Collaboration Request from {{event_metadata.business_name}}",
                'collaboration_approved': "✅ Collaboration Approved: {{event_metadata.promotion_name}}",
                'influencer_interest': "💡 Influencer Interest in {{event_metadata.promotion_name}}"
            }
            
            template_str = subject_templates.get(notification.event_type, notification.title)
            template = self.jinja_env.from_string(template_str)
            
            subject = template.render(
                notification=notification,
                event_metadata=notification.event_metadata or {}
            )
            
            logger.debug(f"📧 SUBJECT_SUCCESS: Generated subject '{subject}'")
            return subject
            
        except Exception as e:
            logger.warning(f"⚠️ SUBJECT_FALLBACK: Failed to generate subject, using title: {str(e)}")
            return notification.title

    async def _generate_html_content(self, notification: Notification, user: User) -> Optional[str]:
        """Generate HTML email content with logging"""
        logger.debug(f"📧 HTML_GENERATE: Generating HTML content for {notification.event_type}")
        
        try:
            template_name = f"{notification.event_type}.html"
            template = self.jinja_env.get_template(template_name)
            
            html_content = template.render(
                user=user,
                notification=notification,
                event_metadata=notification.event_metadata or {},
                current_year=datetime.now().year
            )
            
            logger.debug(f"📧 HTML_SUCCESS: Generated HTML content ({len(html_content)} chars)")
            return html_content
            
        except Exception as e:
            logger.warning(f"⚠️ HTML_TEMPLATE_ERROR: Failed to render HTML template {notification.event_type}.html: {str(e)}")
            return None

    async def _generate_plain_content(self, notification: Notification, user: User) -> str:
        """Generate plain text email content with logging"""
        logger.debug(f"📧 PLAIN_GENERATE: Generating plain text content for {notification.event_type}")
        
        try:
            # Try to load plain text template
            template_name = f"{notification.event_type}.txt"
            template = self.jinja_env.get_template(template_name)
            
            plain_content = template.render(
                user=user,
                notification=notification,
                event_metadata=notification.event_metadata or {}
            )
            
            logger.debug(f"📧 PLAIN_SUCCESS: Generated plain text content ({len(plain_content)} chars)")
            return plain_content
            
        except Exception as e:
            logger.debug(f"📧 PLAIN_FALLBACK: No plain template found, using notification message: {str(e)}")
            # Fallback to notification message
            return f"Hello {user.email},\n\n{notification.message}\n\nBest regards,\nViral Together Team"

# Global service instance
email_service = EmailService() 