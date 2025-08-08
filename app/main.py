from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure detailed logging for MCP debugging - logs to app.log file only
logging.basicConfig(
    level=logging.INFO,
    filename='app.log',
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Enable debug logging for MCP client specifically
logging.getLogger('app.services.mcp_client').setLevel(logging.DEBUG)
logging.getLogger('app.services.twitter_service').setLevel(logging.DEBUG)

from app.api import auth
from app.api.profile.profiles import router as profile_router
from app.api.influencer.influencer import router as influencer_router, public_router as influencer_public_router
from app.api.business.business import router as business_router, public_router as business_public_router
from app.api.rate_card.rate_card import router as rate_card_router
from app.api.subscription.subscription import router as subscription_router
from app.api.user_subscription.user_subscription import router as user_subscription_router
from app.api.documents import documents
from app.api.document_templates.document_templates import router as document_templates_router
from app.api.promotion.promotion import router as promotion_router
from app.api.collaboration.collaboration import router as collaboration_router
from app.api.social_media_platform.social_media_platform import router as social_media_platform_router
from app.api.promotion_interest.promotion_interest import router as promotion_interest_router
from app.api.blog.blog import router as blog_router, public_router as blog_public_router
from app.api.notification.notification import router as notification_router
from app.api.countries.countries import router as countries_router

# Import and initialize notification services
from app.services.notification_service import notification_service
from app.services.email_service import email_service
from app.services.twitter_service import twitter_service
from app.services.websocket_service import websocket_service

app = FastAPI(swagger_ui_parameters={
    "syntaxHighlight": {"theme": "obsidian"},
    "deepLinking": False
})

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

# Initialize notification services
@app.on_event("startup")
async def startup_event():
    """Initialize services on app startup"""
    # Inject services into notification service
    notification_service.set_services(
        email_service=email_service,
        twitter_service=twitter_service,
        websocket_service=websocket_service
    )
    logger.info("Notification system initialized successfully")

# Register routers
app.include_router(auth.router, prefix="/auth")
app.include_router(profile_router, prefix="/profile")
app.include_router(influencer_router, prefix="/influencer")
app.include_router(influencer_public_router, prefix="/influencer")
app.include_router(business_router, prefix="/business")
app.include_router(business_public_router, prefix="/business")
app.include_router(rate_card_router, prefix="/rate_card")
app.include_router(subscription_router, prefix="/subscription")
app.include_router(user_subscription_router, prefix="/user_subscription")
app.include_router(documents.router)
app.include_router(document_templates_router)
app.include_router(promotion_router)
app.include_router(collaboration_router)
app.include_router(social_media_platform_router, prefix="/social-media-platforms")
app.include_router(promotion_interest_router)
app.include_router(notification_router)  # Add notification router
app.include_router(countries_router, prefix="/api/countries", tags=["countries"])
app.include_router(blog_router, prefix="/blog")
app.include_router(blog_public_router, prefix="/blog")