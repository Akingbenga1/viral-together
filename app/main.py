from fastapi import FastAPI
import logging
from app.api import auth
from app.api.profile.profiles import router as profile_router
from app.api.influencer.influencer import router as influencer_router
from app.api.business.business import router as business_router
from app.api.rate_card.rate_card import router as rate_card_router
from app.api.subscription.subscription import router as subscription_router
from app.api.user_subscription.user_subscription import router as user_subscription_router
app = FastAPI()


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