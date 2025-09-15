import asyncio
import schedule
import time
import logging
from datetime import datetime
from typing import Dict, Any
from sqlalchemy import select
from app.services.user_profile_analyzer import UserProfileAnalyzer
from app.services.ai_agent_orchestrator import AIAgentOrchestrator
from app.services.influencer_plan_recommender import InfluencerPlanRecommender
from app.core.dependencies import get_db, get_vector_db, get_agent_coordinator_service
from app.db.models.user import User
from app.db.models.influencer import Influencer
from app.db.models.rate_card import RateCard
from app.db.models.user_subscription import UserSubscription

# Configure logging
logger = logging.getLogger(__name__)


class CronJobScheduler:
    def __init__(self):
        self.profile_analyzer = UserProfileAnalyzer()
        self.ai_orchestrator = AIAgentOrchestrator()
        self.plan_recommender = InfluencerPlanRecommender()
        print("🕐 CronJobScheduler initialized successfully")
        logger.info("🕐 CronJobScheduler initialized successfully")
        
    async def start_scheduler(self):
        """Start the cron job scheduler"""
        print("🚀 Starting cron job scheduler")
        logger.info("🚀 Starting cron job scheduler")
        schedule.every(2).minutes.do(self.run_user_analysis_job)
        
        while True:
            try:
                schedule.run_pending()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                print(f"❌ Error in scheduler loop: {str(e)}")
                logger.error(f"❌ Error in scheduler loop: {str(e)}", exc_info=True)
                await asyncio.sleep(60)  # Continue after error
            
    async def run_user_analysis_job(self):
        """Main cron job that runs every 2 minutes"""
        try:
            print(f"🕐 Starting user analysis job at {datetime.now()}")
            logger.info(f"🕐 Starting user analysis job at {datetime.now()}")
            
            # Get user with ID = 1
            user_profile = await self.get_comprehensive_user_profile(user_id=1)
            
            if not user_profile:
                print("❌ User with ID 1 not found")
                logger.warning("❌ User with ID 1 not found")
                return
                
            print(f"📊 Retrieved user profile for user ID 1")
            logger.info(f"📊 Retrieved user profile for user ID 1")
            
            # Analyze user profile
            analysis_result = self.profile_analyzer.analyze_user_profile(user_profile)
            print(f"📈 User profile analysis completed")
            logger.info(f"📈 User profile analysis completed")
            
            # Get AI agent recommendations using coordination service
            from app.db.session import SessionLocal
            async with SessionLocal() as db:
                ai_recommendations = await self.ai_orchestrator.get_agent_recommendations(
                    user_profile=user_profile,
                    analysis_result=analysis_result,
                    db_session=db
                )
            print(f"🤖 AI agent recommendations generated")
            logger.info(f"🤖 AI agent recommendations generated")
            
            # Generate influencer plan recommendations
            plan_recommendations = self.plan_recommender.generate_monthly_plans(
                user_profile=user_profile,
                ai_recommendations=ai_recommendations,
                analysis_result=analysis_result
            )
            print(f"📋 Influencer plan recommendations generated")
            logger.info(f"📋 Influencer plan recommendations generated")
            
            # Debug: Print the structure of plan_recommendations
            print(f"🔍 Plan recommendations keys: {list(plan_recommendations.keys())}")
            logger.info(f"🔍 Plan recommendations keys: {list(plan_recommendations.keys())}")
            
            # Store recommendations
            await self.store_recommendations(user_id=1, recommendations=plan_recommendations)
            
            print(f"✅ User analysis job completed successfully at {datetime.now()}")
            logger.info(f"✅ User analysis job completed successfully at {datetime.now()}")
            
        except Exception as e:
            print(f"❌ Error in user analysis job: {str(e)}")
            logger.error(f"❌ Error in user analysis job: {str(e)}", exc_info=True)
            
    async def get_comprehensive_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user profile from multiple tables"""
        try:
            print(f"🔍 Fetching comprehensive user profile for user ID {user_id}")
            logger.info(f"🔍 Fetching comprehensive user profile for user ID {user_id}")
            
            # Use proper async database session
            from app.db.session import SessionLocal
            async with SessionLocal() as db:
                # Get user basic info
                    user_result = await db.execute(
                        select(User).where(User.id == user_id)
                    )
                    user = user_result.unique().scalars().first()
                    
                    if not user:
                        print(f"❌ User with ID {user_id} not found in database")
                        logger.warning(f"❌ User with ID {user_id} not found in database")
                        return None
                    
                    print(f"👤 Retrieved user: {user.username} ({user.email})")
                    logger.info(f"👤 Retrieved user: {user.username} ({user.email})")
                    
                    # Get influencer profile
                    influencer_result = await db.execute(
                        select(Influencer).where(Influencer.user_id == user_id).order_by(Influencer.created_at.desc())
                    )
                    influencer = influencer_result.unique().scalars().first()
                    
                    if influencer:
                        print(f"📱 Retrieved influencer profile for user {user_id}")
                        logger.info(f"📱 Retrieved influencer profile for user {user_id}")
                    else:
                        print(f"⚠️ No influencer profile found for user {user_id}")
                        logger.warning(f"⚠️ No influencer profile found for user {user_id}")
                    
                    # Get rate cards
                    rate_cards_result = await db.execute(
                        select(RateCard).where(RateCard.influencer_id == user_id)
                    )
                    rate_cards = rate_cards_result.unique().scalars().all()
                    
                    print(f"💰 Retrieved {len(rate_cards)} rate cards for user {user_id}")
                    logger.info(f"💰 Retrieved {len(rate_cards)} rate cards for user {user_id}")
                    
                    # Get operational locations
                    operational_locations = []
                    if influencer:
                        from app.db.models.location import InfluencerOperationalLocation
                        locations_result = await db.execute(
                            select(InfluencerOperationalLocation).where(InfluencerOperationalLocation.influencer_id == influencer.id)
                        )
                        operational_locations = locations_result.unique().scalars().all()
                        print(f"📍 Retrieved {len(operational_locations)} operational locations for user {user_id}")
                        logger.info(f"📍 Retrieved {len(operational_locations)} operational locations for user {user_id}")
                    
                    # Get coaching groups (as coach)
                    coaching_groups_as_coach = []
                    if influencer:
                        from app.db.models.influencer_coaching import InfluencerCoachingGroup
                        coaching_groups_result = await db.execute(
                            select(InfluencerCoachingGroup).where(InfluencerCoachingGroup.coach_influencer_id == influencer.id)
                        )
                        coaching_groups_as_coach = coaching_groups_result.unique().scalars().all()
                        print(f"👥 Retrieved {len(coaching_groups_as_coach)} coaching groups as coach for user {user_id}")
                        logger.info(f"👥 Retrieved {len(coaching_groups_as_coach)} coaching groups as coach for user {user_id}")
                    
                    # Get coaching groups (as member)
                    coaching_groups_as_member = []
                    if influencer:
                        from app.db.models.influencer_coaching import InfluencerCoachingMember
                        member_groups_result = await db.execute(
                            select(InfluencerCoachingGroup)
                            .join(InfluencerCoachingMember)
                            .where(InfluencerCoachingMember.member_influencer_id == influencer.id)
                        )
                        coaching_groups_as_member = member_groups_result.unique().scalars().all()
                        print(f"👥 Retrieved {len(coaching_groups_as_member)} coaching groups as member for user {user_id}")
                        logger.info(f"👥 Retrieved {len(coaching_groups_as_member)} coaching groups as member for user {user_id}")
                    
                    # Get collaboration countries
                    collaboration_countries = []
                    if influencer:
                        from app.db.models.influencer_collaboration_country import influencer_collaboration_countries
                        from app.db.models.country import Country
                        collaboration_result = await db.execute(
                            select(Country)
                            .join(influencer_collaboration_countries)
                            .where(influencer_collaboration_countries.c.influencer_id == influencer.id)
                        )
                        collaboration_countries = collaboration_result.unique().scalars().all()
                        print(f"🌍 Retrieved {len(collaboration_countries)} collaboration countries for user {user_id}")
                        logger.info(f"🌍 Retrieved {len(collaboration_countries)} collaboration countries for user {user_id}")
                    
                    # Get social media platforms
                    from app.db.models.social_media_platform import SocialMediaPlatform
                    social_media_platforms_result = await db.execute(
                        select(SocialMediaPlatform)
                    )
                    social_media_platforms = social_media_platforms_result.unique().scalars().all()
                    print(f"📱 Retrieved {len(social_media_platforms)} social media platforms for user {user_id}")
                    logger.info(f"📱 Retrieved {len(social_media_platforms)} social media platforms for user {user_id}")
                    
                    # Get subscription info
                    subscription_result = await db.execute(
                        select(UserSubscription).where(UserSubscription.user_id == user_id).order_by(UserSubscription.created_at.desc())
                    )
                    subscription = subscription_result.unique().scalars().first()
                    
                    if subscription:
                        print(f"💳 Retrieved subscription info for user {user_id}")
                        logger.info(f"💳 Retrieved subscription info for user {user_id}")
                    else:
                        print(f"ℹ️ No subscription found for user {user_id}")
                        logger.info(f"ℹ️ No subscription found for user {user_id}")
                    
                    # Note: Promotion metrics are about promotion performance, not user performance
                    # We'll focus on user-specific metrics for now
                    metrics = []
                    
                    profile_data = {
                        "user": user,
                        "influencer": influencer,
                        "rate_cards": rate_cards,
                        "operational_locations": operational_locations,
                        "coaching_groups_as_coach": coaching_groups_as_coach,
                        "coaching_groups_as_member": coaching_groups_as_member,
                        "collaboration_countries": collaboration_countries,
                        "social_media_platforms": social_media_platforms,
                        "subscription": subscription,
                        "metrics": metrics,
                        "analysis_timestamp": datetime.now()
                    }
                    
                    print(f"✅ Comprehensive user profile assembled for user {user_id}")
                    logger.info(f"✅ Comprehensive user profile assembled for user {user_id}")
                    return profile_data
                    
        except Exception as e:
            print(f"❌ Error in get_comprehensive_user_profile for user {user_id}: {str(e)}")
            logger.error(f"❌ Error in get_comprehensive_user_profile for user {user_id}: {str(e)}", exc_info=True)
            raise
            
    async def store_recommendations(self, user_id: int, recommendations: Dict[str, Any]):
        """Store recommendations in database"""
        try:
            print(f"💾 Storing recommendations for user {user_id}")
            logger.info(f"💾 Storing recommendations for user {user_id}")
            
            # Debug: Print recommendations structure
            print(f"🔍 Recommendations data: {recommendations}")
            logger.info(f"🔍 Recommendations data: {recommendations}")
            
            # Import the model here to avoid circular imports
            from app.db.models.influencer_recommendations import InfluencerRecommendations
            from app.db.session import SessionLocal
            
            # Create a new session for this operation
            async with SessionLocal() as db:
                try:
                    # Create recommendation record
                    recommendation = InfluencerRecommendations(
                        user_id=user_id,
                        user_level=recommendations.get("user_level", "beginner"),
                        base_plan=recommendations.get("base_plan", {}),
                        enhanced_plan=recommendations.get("enhanced_plan", {}),
                        monthly_schedule=recommendations.get("monthly_schedule", {}),
                        performance_goals=recommendations.get("performance_goals", {}),
                        pricing_recommendations=recommendations.get("pricing_recommendations", {}),
                        ai_insights=recommendations.get("ai_insights", []),
                        coordination_uuid=recommendations.get("coordination_uuid"),
                        status="active"
                    )
                    
                    # Add to database
                    db.add(recommendation)
                    await db.commit()
                    await db.refresh(recommendation)
                    
                    print(f"✅ Recommendations stored successfully for user {user_id} with ID {recommendation.id}")
                    logger.info(f"✅ Recommendations stored successfully for user {user_id} with ID {recommendation.id}")
                    
                except Exception as e:
                    print(f"❌ Database error while storing recommendations for user {user_id}: {str(e)}")
                    logger.error(f"❌ Database error while storing recommendations for user {user_id}: {str(e)}", exc_info=True)
                    await db.rollback()
                    raise
                    
        except Exception as e:
            print(f"❌ Error storing recommendations for user {user_id}: {str(e)}")
            logger.error(f"❌ Error storing recommendations for user {user_id}: {str(e)}", exc_info=True)
            raise
