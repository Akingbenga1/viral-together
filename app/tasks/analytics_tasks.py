"""
Celery tasks for analytics processing
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from celery import Task
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.celery_session import SessionLocal
from app.services.analytics.real_time_analytics import RealTimeAnalyticsService
from app.services.social_media.social_media_factory import SocialMediaFactory
from app.services.web_search.web_search_factory import WebSearchFactory
from app.schemas.task_status import TaskStatusEnum

logger = logging.getLogger(__name__)

# Use minimal database session for Celery workers

class BaseTask(Task):
    """Base task class with error handling and retry logic"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        logger.error(f"Task {task_id} failed: {exc}")
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

@celery_app.task(bind=True, name="process_trending_content_analysis")
def process_trending_content_analysis_task(self, task_id: str, platforms: List[str], user_id: int):
    """
    Celery task for trending content analysis
    Runs in separate worker process - completely isolated from main application
    """
    try:
        logger.info(f"Starting trending content analysis task {task_id} for platforms {platforms}")
        
        # Create new event loop for this process
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize analytics service
            analytics_service = RealTimeAnalyticsService()
            
            # Gather trending content from multiple platforms
            trending_data = {}
            for platform in platforms:
                try:
                    content = loop.run_until_complete(
                        analytics_service.get_trending_content(platform)
                    )
                    trending_data[platform] = content
                    logger.info(f"Successfully gathered trending content from {platform}")
                except Exception as e:
                    logger.warning(f"Failed to get trending content from {platform}: {e}")
                    trending_data[platform] = []
            
            result = {
                "trending_data": trending_data,
                "platforms_analyzed": platforms,
                "user_id": user_id,
                "analyzed_at": datetime.now().isoformat()
            }
            
            logger.info(f"Successfully completed trending content analysis task {task_id}")
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in trending content analysis task {task_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)

@celery_app.task(bind=True, name="process_market_analysis")
def process_market_analysis_task(self, task_id: str, platforms: List[str], content_types: List[str]):
    """
    Celery task for market analysis
    Runs in separate worker process - completely isolated from main application
    """
    try:
        logger.info(f"Starting market analysis task {task_id} for platforms {platforms}")
        
        # Create new event loop for this process
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize analytics service
            analytics_service = RealTimeAnalyticsService()
            
            # Gather market data from multiple platforms
            market_data = {}
            for platform in platforms:
                for content_type in content_types:
                    try:
                        rates = loop.run_until_complete(
                            analytics_service.get_market_rates(platform, content_type)
                        )
                        market_data[f"{platform}_{content_type}"] = rates
                        logger.info(f"Successfully gathered market rates for {platform} {content_type}")
                    except Exception as e:
                        logger.warning(f"Failed to get market rates for {platform} {content_type}: {e}")
                        market_data[f"{platform}_{content_type}"] = []
            
            result = {
                "market_data": market_data,
                "platforms_analyzed": platforms,
                "content_types_analyzed": content_types,
                "analyzed_at": datetime.now().isoformat()
            }
            
            logger.info(f"Successfully completed market analysis task {task_id}")
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in market analysis task {task_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)

@celery_app.task(bind=True, name="process_engagement_trends_analysis")
def process_engagement_trends_analysis_task(self, task_id: str, user_id: int, days: int = 30):
    """
    Celery task for engagement trends analysis
    Runs in separate worker process - completely isolated from main application
    """
    try:
        logger.info(f"Starting engagement trends analysis task {task_id} for user {user_id}")
        
        # Create new event loop for this process
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Initialize analytics service
            analytics_service = RealTimeAnalyticsService()
            
            # Get engagement trends
            trends = loop.run_until_complete(
                analytics_service.get_engagement_trends(user_id, days=days)
            )
            
            result = {
                "engagement_trends": trends,
                "user_id": user_id,
                "analysis_period_days": days,
                "analyzed_at": datetime.now().isoformat()
            }
            
            logger.info(f"Successfully completed engagement trends analysis task {task_id}")
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in engagement trends analysis task {task_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)
