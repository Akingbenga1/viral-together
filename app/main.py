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
from app.api.chat import router as chat_router
from app.api.role_management import router as role_management_router
from app.api.ai_agent import router as ai_agent_router
from app.api.recommendations import router as recommendations_router
from app.api.influencers_targets import router as influencers_targets_router
from app.api.influencer_coaching import router as influencer_coaching_router
from app.api.location import router as location_router
from app.api.location_search import router as location_search_router
from app.api.location_promotion_requests import router as location_promotion_router
from app.api.users.user_profile import router as user_profile_router
from app.api.admin.admin_users import router as admin_users_router
from app.api.analytics.analytics import router as analytics_router
from app.api.unified_influencer_profile import router as unified_influencer_profile_router
from app.api.real_time_analytics import router as real_time_analytics_router
from app.api.influencer_marketing import router as influencer_marketing_router
from app.api.enhanced_ai_agents import router as enhanced_ai_agents_router
from app.api.web_search import router as web_search_router
from app.api.cli_tools import router as cli_tools_router

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
app.include_router(chat_router)  # Add chat router
app.include_router(role_management_router)  # Add role management router
app.include_router(ai_agent_router)
app.include_router(recommendations_router)  # Add AI agent router
app.include_router(influencers_targets_router, tags=["influencers-targets"])
app.include_router(influencer_coaching_router, tags=["influencer-coaching"])
app.include_router(location_router, tags=["location"])
app.include_router(location_search_router, tags=["location-search"])
app.include_router(location_promotion_router, tags=["location-promotion-requests"])
app.include_router(user_profile_router, tags=["user-profile"])
app.include_router(admin_users_router, tags=["admin-users"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["analytics"])
app.include_router(unified_influencer_profile_router, tags=["unified-influencer-profile"])
app.include_router(real_time_analytics_router, tags=["real-time-analytics"])
app.include_router(influencer_marketing_router, tags=["influencer-marketing"])
app.include_router(enhanced_ai_agents_router, tags=["enhanced-ai-agents"])
app.include_router(web_search_router, tags=["web-search"])
app.include_router(cli_tools_router, prefix="/api", tags=["cli-tools"])