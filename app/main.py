from fastapi import FastAPI
from app.api import auth
from app.api.profile.profiles import router as profile_router
from app.api.influencer.influencer import router as influencer_router
from app.api.business.business import router as business_router

app = FastAPI()

# Register routers
app.include_router(auth.router, prefix="/auth")
app.include_router(profile_router, prefix="/profile")
app.include_router(influencer_router, prefix="/influencer")
app.include_router(business_router, prefix="/business")