import asyncio
import schedule
import time
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


class CronJobScheduler:
    def __init__(self):
        self.profile_analyzer = UserProfileAnalyzer()
        self.ai_orchestrator = AIAgentOrchestrator()
        self.plan_recommender = InfluencerPlanRecommender()
        
    async def start_scheduler(self):
        """Start the cron job scheduler"""
        schedule.every(2).minutes.do(self.run_user_analysis_job)
        
        while True:
            schedule.run_pending()
            await asyncio.sleep(60)  # Check every minute
            
    async def run_user_analysis_job(self):
        """Main cron job that runs every 2 minutes"""
        try:
            print(f"🕐 Starting user analysis job at {datetime.now()}")
            
            # Get user with ID = 1
            user_profile = await self.get_comprehensive_user_profile(user_id=1)
            
            if not user_profile:
                print("❌ User with ID 1 not found")
                return
                
            # Analyze user profile
            analysis_result = await self.profile_analyzer.analyze_user_profile(user_profile)
            
            # Get AI agent recommendations using coordination service
            ai_recommendations = await self.ai_orchestrator.get_agent_recommendations(
                user_profile=user_profile,
                analysis_result=analysis_result
            )
            
            # Generate influencer plan recommendations
            plan_recommendations = await self.plan_recommender.generate_monthly_plans(
                user_profile=user_profile,
                ai_recommendations=ai_recommendations
            )
            
            # Store recommendations
            await self.store_recommendations(user_id=1, recommendations=plan_recommendations)
            
            print(f"✅ User analysis job completed successfully at {datetime.now()}")
            
        except Exception as e:
            print(f"❌ Error in user analysis job: {str(e)}")
            
    async def get_comprehensive_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user profile from multiple tables"""
        async with get_db() as db:
            # Get user basic info
            user = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user.scalar_one_or_none()
            
            if not user:
                return None
                
            # Get influencer profile
            influencer = await db.execute(
                select(Influencer).where(Influencer.user_id == user_id)
            )
            influencer = influencer.scalar_one_or_none()
            
            # Get rate cards
            rate_cards = await db.execute(
                select(RateCard).where(RateCard.influencer_id == user_id)
            )
            rate_cards = rate_cards.all()
            
            # Get subscription info
            subscription = await db.execute(
                select(UserSubscription).where(UserSubscription.user_id == user_id)
            )
            subscription = subscription.scalar_one_or_none()
            
            # Note: Promotion metrics are about promotion performance, not user performance
            # We'll focus on user-specific metrics for now
            metrics = []
            
            return {
                "user": user,
                "influencer": influencer,
                "rate_cards": rate_cards,
                "subscription": subscription,
                "metrics": metrics,
                "analysis_timestamp": datetime.now()
            }
            
    async def store_recommendations(self, user_id: int, recommendations: Dict[str, Any]):
        """Store recommendations in database"""
        # This would store the recommendations in a dedicated table
        print(f"💾 Storing recommendations for user {user_id}")
        # Implementation would go here
