"""
Celery tasks for recommendation processing
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from celery import Task
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.celery_session import SessionLocal
from app.services.cron_scheduler import CronJobScheduler
from app.services.user_profile_analyzer import UserProfileAnalyzer
from app.services.ai_agent_orchestrator import AIAgentOrchestrator
from app.services.influencer_plan_recommender import InfluencerPlanRecommender
from app.schemas.influencer_recommendations import InfluencerRecommendationsCreate
from app.db.models.influencer_recommendations import InfluencerRecommendations
from app.schemas.task_status import TaskStatusEnum

logger = logging.getLogger(__name__)

# Use minimal database session for Celery workers

class BaseTask(Task):
    """Base task class with error handling and retry logic"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        logger.error(f"Task {task_id} failed: {exc}")
        # Update task status in database
        self._update_task_status(task_id, TaskStatusEnum.FAILED, str(exc))
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success"""
        logger.info(f"Task {task_id} completed successfully")
        self._update_task_status(task_id, TaskStatusEnum.COMPLETED, "Task completed successfully", retval)
    
    def _update_task_status(self, task_id: str, status: TaskStatusEnum, message: str, result: Optional[Dict[str, Any]] = None):
        """Update task status in database using raw SQL"""
        try:
            import psycopg2
            import json
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            DATABASE_URL = os.getenv('DATABASE_URL', '')
            psycopg2_url = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
            
            conn = psycopg2.connect(psycopg2_url)
            cur = conn.cursor()
            
            # Prepare update SQL
            if status in [TaskStatusEnum.COMPLETED, TaskStatusEnum.FAILED, TaskStatusEnum.CANCELLED]:
                # Set completion time for finished tasks
                cur.execute('''
                    UPDATE task_status 
                    SET status = %s, message = %s, result = %s, completed_at = NOW() 
                    WHERE task_id = %s
                ''', (status.value, message, json.dumps(result) if result else None, task_id))
            else:
                # Update without completion time
                cur.execute('''
                    UPDATE task_status 
                    SET status = %s, message = %s, result = %s 
                    WHERE task_id = %s
                ''', (status.value, message, json.dumps(result) if result else None, task_id))
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"Updated task {task_id} status to {status.value}")
            
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")

@celery_app.task(bind=True, name="process_recommendation_generation")
def process_recommendation_generation_task(self, task_id: str, user_id: int):
    """
    Celery task for recommendation generation
    Runs in separate worker process - completely isolated from main application
    """
    try:
        logger.info(f"Starting recommendation generation task {task_id} for user {user_id}")
        
        # Create new event loop for this process
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize services
            scheduler = CronJobScheduler()
            profile_analyzer = UserProfileAnalyzer()
            ai_orchestrator = AIAgentOrchestrator()
            plan_recommender = InfluencerPlanRecommender()
            
            # Get comprehensive user profile
            user_profile = loop.run_until_complete(
                scheduler.get_comprehensive_user_profile(user_id)
            )
            
            if not user_profile:
                raise Exception(f"User with ID {user_id} not found")
            
            # Analyze user profile
            analysis_result = profile_analyzer.analyze_user_profile(user_profile)
            
            # Get AI agent recommendations (heavy processing)
            ai_recommendations = loop.run_until_complete(
                ai_orchestrator.get_agent_recommendations(
                    user_profile=user_profile,
                    analysis_result=analysis_result,
                    db_session=None  # Will be handled by worker process
                )
            )
            
            # Generate influencer plan recommendations
            plan_recommendations = plan_recommender.generate_monthly_plans(
                user_profile=user_profile,
                ai_recommendations=ai_recommendations,
                analysis_result=analysis_result
            )
            
            # Save to database using worker's database connection
            db_session = SessionLocal()
            try:
                # Create recommendation record
                recommendation_data = InfluencerRecommendationsCreate(
                    user_id=user_id,
                    user_level=plan_recommendations["user_level"],
                    base_plan=plan_recommendations["base_plan"],
                    enhanced_plan=plan_recommendations["enhanced_plan"],
                    monthly_schedule=plan_recommendations["monthly_schedule"],
                    performance_goals=plan_recommendations["performance_goals"],
                    pricing_recommendations=plan_recommendations["pricing_recommendations"],
                    ai_insights=plan_recommendations["ai_insights"],
                    coordination_uuid=ai_recommendations.get("coordination_uuid")
                )
                
                # Save to database
                recommendation = InfluencerRecommendations(**recommendation_data.dict())
                db_session.add(recommendation)
                db_session.commit()
                db_session.refresh(recommendation)
                
                result = {
                    "recommendation_id": recommendation.id,
                    "user_level": plan_recommendations["user_level"],
                    "coordination_uuid": ai_recommendations.get("coordination_uuid"),
                    "generated_at": datetime.now().isoformat()
                }
                
                logger.info(f"Successfully completed recommendation generation task {task_id}")
                return result
                
            finally:
                db_session.close()
                
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in recommendation generation task {task_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)

@celery_app.task(bind=True, name="process_custom_text_analysis")
def process_custom_text_analysis_task(self, task_id: str, text_content: str, user_id: Optional[int]):
    """
    Celery task for custom text analysis
    Runs in separate worker process - completely isolated from main application
    """
    try:
        logger.info(f"Starting custom text analysis task {task_id}")
        
        # Create new event loop for this process
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize services
            ai_orchestrator = AIAgentOrchestrator()
            
            # Get user profile if user_id is provided
            user_profile = None
            if user_id:
                scheduler = CronJobScheduler()
                user_profile = loop.run_until_complete(
                    scheduler.get_comprehensive_user_profile(user_id)
                )
                
                if not user_profile:
                    raise Exception(f"User with ID {user_id} not found")
            
            # Get custom text recommendations
            custom_recommendations = loop.run_until_complete(
                ai_orchestrator.get_custom_text_recommendations(
                    text_content=text_content,
                    user_profile=user_profile,
                    db_session=None  # Will be handled by worker process
                )
            )
            
            # Check for errors
            if custom_recommendations.get("error"):
                raise Exception(custom_recommendations["error"])
            
            result = {
                "coordination_uuid": custom_recommendations.get("coordination_uuid"),
                "available_agents": custom_recommendations.get("available_agents", 0),
                "agent_responses": custom_recommendations.get("agent_responses", []),
                "custom_prompt": custom_recommendations.get("custom_prompt", ""),
                "text_content_length": custom_recommendations.get("text_content_length", 0),
                "timestamp": custom_recommendations.get("timestamp", datetime.now()).isoformat()
            }
            
            logger.info(f"Successfully completed custom text analysis task {task_id}")
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in custom text analysis task {task_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)
