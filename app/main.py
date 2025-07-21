from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.api import auth
from app.api.profile.profiles import router as profile_router
from app.api.influencer.influencer import router as influencer_router
from app.api.business.business import router as business_router
from app.api.rate_card.rate_card import router as rate_card_router
from app.api.subscription.subscription import router as subscription_router
from app.api.user_subscription.user_subscription import router as user_subscription_router
from app.api.documents import documents
from app.api.promotion_interest.promotion_interest import router as promotion_interest_router
app = FastAPI(swagger_ui_parameters={
    "syntaxHighlight": {"theme": "obsidian"},
    "deepLinking": False
})

app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])


# Configure logging
logging.basicConfig(
    filename='app.log',  # Log file name
    level=logging.INFO,   # Log level
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)

logger = logging.getLogger(__name__)

# Register routers
app.include_router(auth.router, prefix="/auth")
app.include_router(profile_router, prefix="/profile")
app.include_router(influencer_router, prefix="/influencer")
app.include_router(business_router, prefix="/business")
app.include_router(rate_card_router, prefix="/rate_card")
app.include_router(subscription_router, prefix="/subscription")
app.include_router(user_subscription_router, prefix="/user_subscription")
app.include_router(documents.router)
app.include_router(promotion_interest_router)