import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, Template
from pathlib import Path
import os

from app.core.config import settings
from app.db.models.notification import Notification
from app.db.models.user import User

logger = logging.getLogger(__name__)

class EmailService:
    """Email service supporting SMTP and transactional email providers"""
    
    def __init__(self):
        self.smtp_server = getattr(settings, 'SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_username = getattr(settings, 'SMTP_USERNAME', '')
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', '')
        self.default_from_email = getattr(settings, 'DEFAULT_EMAIL_FROM', 'noreply@viral-together.com')
        self.email_backend = getattr(settings, 'EMAIL_BACKEND', 'smtp')  # 'smtp', 'sendgrid', 'mailgun'
        
        # Setup Jinja2 for email templates
        template_dir = Path(__file__).parent.parent / "templates" / "email"
        if template_dir.exists():
            self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))
        else:
            self.jinja_env = None
        
        # Email templates configuration
        self.email_templates = {
            "promotion_created": {
                "subject": "🚀 New Promotion Available: {promotion_name}",
                "template": "promotion_created.html",
                "plain_fallback": self._promotion_created_plain_template
            },
            "collaboration_created": {
                "subject": "🤝 New Collaboration Request from {influencer_name}",
                "template": "collaboration_created.html", 
                "plain_fallback": self._collaboration_created_plain_template
            },
            "collaboration_approved": {
                "subject": "🎉 Your Collaboration Request Approved!",
                "template": "collaboration_approved.html",
                "plain_fallback": self._collaboration_approved_plain_template
            },
            "influencer_interest": {
                "subject": "👀 New Interest in {promotion_name}",
                "template": "influencer_interest.html",
                "plain_fallback": self._influencer_interest_plain_template
            }
        }
    
    async def send_notification_email(self, to_email: str, notification: Notification, user: User):
        """Send notification email using configured backend"""
        try:
            # Get email template configuration
            template_config = self.email_templates.get(notification.event_type)
            if not template_config:
                logger.warning(f"No email template configured for event type: {notification.event_type}")
                return
            
            # Prepare email content
            subject = self._render_subject(template_config["subject"], notification.event_metadata, user)
            html_content = await self._render_html_content(template_config, notification, user)
            plain_content = self._render_plain_content(template_config, notification, user)
            
            # Send email based on backend
            if self.email_backend == 'smtp':
                await self._send_smtp_email(to_email, subject, html_content, plain_content)
            elif self.email_backend == 'sendgrid':
                await self._send_sendgrid_email(to_email, subject, html_content, plain_content)
            elif self.email_backend == 'mailgun':
                await self._send_mailgun_email(to_email, subject, html_content, plain_content)
            else:
                raise ValueError(f"Unsupported email backend: {self.email_backend}")
            
            logger.info(f"Email sent successfully to {to_email} for notification {notification.id}")
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email} for notification {notification.id}: {str(e)}")
            raise
    
    async def _send_smtp_email(self, to_email: str, subject: str, html_content: str, plain_content: str):
        """Send email using SMTP"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.default_from_email
        msg['To'] = to_email
        
        # Add plain text and HTML versions
        part1 = MIMEText(plain_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
    
    async def _send_sendgrid_email(self, to_email: str, subject: str, html_content: str, plain_content: str):
        """Send email using SendGrid API"""
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            sg = sendgrid.SendGridAPIClient(api_key=getattr(settings, 'SENDGRID_API_KEY', ''))
            
            from_email = Email(self.default_from_email)
            to_email_obj = To(to_email)
            
            mail = Mail(
                from_email=from_email,
                to_emails=to_email_obj,
                subject=subject,
                html_content=html_content,
                plain_text_content=plain_content
            )
            
            response = sg.send(mail)
            logger.info(f"SendGrid email sent with status code: {response.status_code}")
            
        except ImportError:
            logger.error("SendGrid library not installed. Install with: pip install sendgrid")
            raise
        except Exception as e:
            logger.error(f"SendGrid email failed: {str(e)}")
            raise
    
    async def _send_mailgun_email(self, to_email: str, subject: str, html_content: str, plain_content: str):
        """Send email using Mailgun API"""
        try:
            import requests
            
            domain = getattr(settings, 'MAILGUN_DOMAIN', '')
            api_key = getattr(settings, 'MAILGUN_API_KEY', '')
            
            response = requests.post(
                f"https://api.mailgun.net/v3/{domain}/messages",
                auth=("api", api_key),
                data={
                    "from": self.default_from_email,
                    "to": to_email,
                    "subject": subject,
                    "text": plain_content,
                    "html": html_content
                }
            )
            
            response.raise_for_status()
            logger.info(f"Mailgun email sent successfully")
            
        except Exception as e:
            logger.error(f"Mailgun email failed: {str(e)}")
            raise
    
    def _render_subject(self, subject_template: str, event_metadata: Dict[str, Any], user: User) -> str:
        """Render email subject with event_metadata"""
        try:
            # Combine event_metadata with user data
            context = {**event_metadata, 'user_name': f"{user.first_name} {user.last_name}"}
            return subject_template.format(**context)
        except Exception as e:
            logger.warning(f"Failed to render email subject: {str(e)}")
            return subject_template
    
    async def _render_html_content(self, template_config: Dict, notification: Notification, user: User) -> str:
        """Render HTML email content"""
        template_name = template_config["template"]
        
        if self.jinja_env:
            try:
                template = self.jinja_env.get_template(template_name)
                context = {
                    'notification': notification,
                    'user': user,
                    'metadata': notification.event_metadata,
                    'user_name': f"{user.first_name} {user.last_name}",
                    **notification.event_metadata
                }
                return template.render(context)
            except Exception as e:
                logger.warning(f"Failed to render HTML template {template_name}: {str(e)}")
        
        # Fallback to basic HTML
        return self._render_basic_html(notification, user)
    
    def _render_plain_content(self, template_config: Dict, notification: Notification, user: User) -> str:
        """Render plain text email content"""
        fallback_func = template_config.get("plain_fallback")
        if fallback_func:
            return fallback_func(notification, user)
        
        # Basic fallback
        return f"""
Hi {user.first_name},

{notification.message}

Best regards,
The Viral Together Team
        """.strip()
    
    def _render_basic_html(self, notification: Notification, user: User) -> str:
        """Basic HTML email template fallback"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{notification.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .footer {{ padding: 20px; text-align: center; color: #666; }}
        .button {{ 
            display: inline-block; 
            background-color: #4F46E5; 
            color: white; 
            padding: 12px 24px; 
            text-decoration: none; 
            border-radius: 4px; 
            margin: 10px 0; 
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{notification.title}</h1>
        </div>
        <div class="content">
            <p>Hi {user.first_name},</p>
            <p>{notification.message}</p>
            
            <a href="https://viral-together.com/dashboard" class="button">View Dashboard</a>
        </div>
        <div class="footer">
            <p>Best regards,<br>The Viral Together Team</p>
            <p><small>This is an automated message. Please do not reply to this email.</small></p>
        </div>
    </div>
</body>
</html>
        """
    
    # Plain text email templates
    def _promotion_created_plain_template(self, notification: Notification, user: User) -> str:
        event_metadata = notification.event_metadata
        return f"""
Hi {user.first_name},

🚀 New Promotion Available!

{event_metadata.get('business_name', 'A business')} has created a new promotion "{event_metadata.get('promotion_name', 'Untitled')}" that might interest you!

Promotion Details:
- Business: {event_metadata.get('business_name', 'N/A')}
- Industry: {event_metadata.get('industry', 'N/A')}
- Budget: ${event_metadata.get('budget', 'Not specified')}

Visit your dashboard to learn more and show your interest!

Best regards,
The Viral Together Team
        """.strip()
    
    def _collaboration_created_plain_template(self, notification: Notification, user: User) -> str:
        event_metadata = notification.event_metadata
        return f"""
Hi {user.first_name},

🤝 New Collaboration Request!

{event_metadata.get('influencer_name', 'An influencer')} is interested in your promotion "{event_metadata.get('promotion_name', 'Untitled')}" and has submitted a collaboration request.

Collaboration Details:
- Influencer: {event_metadata.get('influencer_name', 'N/A')}
- Promotion: {event_metadata.get('promotion_name', 'N/A')}
- Collaboration Type: {event_metadata.get('collaboration_type', 'N/A')}
- Proposed Amount: ${event_metadata.get('proposed_amount', 'Not specified')}

Visit your dashboard to review and approve this collaboration request!

Best regards,
The Viral Together Team
        """.strip()
    
    def _collaboration_approved_plain_template(self, notification: Notification, user: User) -> str:
        event_metadata = notification.event_metadata
        return f"""
Hi {user.first_name},

🎉 Congratulations! Your Collaboration Request Approved!

{event_metadata.get('business_name', 'A business')} has approved your collaboration request for the promotion "{event_metadata.get('promotion_name', 'Untitled')}".

Collaboration Details:
- Business: {event_metadata.get('business_name', 'N/A')}
- Promotion: {event_metadata.get('promotion_name', 'N/A')}
- Collaboration Type: {event_metadata.get('collaboration_type', 'N/A')}
- Approved Amount: ${event_metadata.get('approved_amount', 'TBD')}

Visit your dashboard to view the collaboration details and next steps!

Best regards,
The Viral Together Team
        """.strip()
    
    def _influencer_interest_plain_template(self, notification: Notification, user: User) -> str:
        event_metadata = notification.event_metadata
        return f"""
Hi {user.first_name},

👀 New Interest in Your Promotion!

{event_metadata.get('influencer_name', 'An influencer')} has shown interest in your promotion "{event_metadata.get('promotion_name', 'Untitled')}".

Interest Details:
- Influencer: {event_metadata.get('influencer_name', 'N/A')}
- Promotion: {event_metadata.get('promotion_name', 'N/A')}
- Proposed Amount: ${event_metadata.get('proposed_amount', 'Not specified')}
- Message: {event_metadata.get('message', 'No message provided')}

Visit your dashboard to review this interest and potentially start a collaboration!

Best regards,
The Viral Together Team
        """.strip()

# Global email service instance
email_service = EmailService() 