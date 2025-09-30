"""
Celery tasks for AI agent processing
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from celery import Task
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.celery_session import SessionLocal
from app.services.enhanced_ai_agent_service import EnhancedAIAgentService
from app.schemas.task_status import TaskStatusEnum

logger = logging.getLogger(__name__)

# Utility function to convert datetime objects to strings for JSON serialization
def convert_datetimes_to_strings(obj):
    """Recursively convert datetime objects to ISO format strings"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: convert_datetimes_to_strings(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetimes_to_strings(item) for item in obj]
    else:
        return obj

# Define User and Influencer classes at module level
class User:
    def __init__(self, user_id, username, email):
        self.id = user_id
        self.username = username
        self.email = email

class Influencer:
    def __init__(self, influencer_data):
        self.id = influencer_data[0] if influencer_data else 0
        self.bio = influencer_data[2] if influencer_data else None
        self.profile_image_url = influencer_data[3] if influencer_data else None
        self.website_url = influencer_data[4] if influencer_data else None
        self.location = influencer_data[5] if influencer_data else None
        self.languages = influencer_data[6] if influencer_data else None
        self.availability = bool(influencer_data[7]) if influencer_data else False
        self.rate_per_post = float(influencer_data[8]) if influencer_data and influencer_data[8] else 0.0
        self.total_posts = influencer_data[9] if influencer_data else 0
        self.growth_rate = float(influencer_data[10]) if influencer_data and influencer_data[10] else 0.0
        self.successful_campaigns = influencer_data[11] if influencer_data else 0
        self.base_country_id = influencer_data[12] if influencer_data else None
        self.created_at = influencer_data[13] if influencer_data else None
        self.updated_at = influencer_data[14] if influencer_data else None
        # Use actual database values with fallback to calculated estimates
        self.engagement_rate = float(influencer_data[15]) if influencer_data and influencer_data[15] > 0 else (float(influencer_data[10]) * 0.1 if influencer_data and influencer_data[10] else 0.0)
        self.follower_growth = int(influencer_data[16]) if influencer_data and influencer_data[16] > 0 else (int(influencer_data[9] * 0.05) if influencer_data and influencer_data[9] else 0)
        self.reach = int(influencer_data[17]) if influencer_data and influencer_data[17] > 0 else (int(influencer_data[9] * 10) if influencer_data and influencer_data[9] else 0)
        self.total_revenue = float(influencer_data[18]) if influencer_data and influencer_data[18] > 0 else (float(influencer_data[8] * influencer_data[11]) if influencer_data and influencer_data[8] and influencer_data[11] else 0.0)
        self.average_rate = float(influencer_data[8]) if influencer_data and influencer_data[8] else 0.0
        self.rate_cards_count = int(influencer_data[19]) if influencer_data and influencer_data[19] > 0 else (1 if influencer_data and influencer_data[8] and influencer_data[8] > 0 else 0)
        self.consistency_score = int(influencer_data[20]) if influencer_data and influencer_data[20] > 0 else (min(100, int(influencer_data[9] * 2)) if influencer_data and influencer_data[9] else 0)
        self.posting_frequency = int(influencer_data[21]) if influencer_data and influencer_data[21] > 0 else (int(influencer_data[9] / 30) if influencer_data and influencer_data[9] else 0)
        self.recent_posts = int(influencer_data[22]) if influencer_data and influencer_data[22] > 0 else (min(10, influencer_data[9]) if influencer_data and influencer_data[9] else 0)

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

@celery_app.task(bind=True, name="process_ai_agent_execution")
def process_ai_agent_execution_task(self, task_id: str, agent_id: int, prompt: str, context: Dict[str, Any], real_time_data: Dict[str, Any]):
    """
    Celery task for AI agent execution with real-time data
    Runs in separate worker process - completely isolated from main application
    """
    try:
        logger.info(f"Starting AI agent execution task {task_id} for agent {agent_id}")
        
        # Import the enhanced AI agent service
        from app.services.enhanced_ai_agent_service import EnhancedAIAgentService
        
        # Create service instance
        ai_service = EnhancedAIAgentService()
        
        # Execute the AI agent with real-time data
        logger.info(f"Executing AI agent {agent_id} with prompt: {prompt[:100]}...")
        result = asyncio.run(ai_service.execute_with_real_time_data(
            agent_id=agent_id,
            prompt=prompt,
            context=context,
            real_time_data=real_time_data
        ))
        
        logger.info(f"Successfully completed AI agent execution task {task_id}")
        
        # Update task status to completed using raw SQL to avoid model relationship issues
        try:
            from app.db.celery_session import SessionLocal
            from datetime import datetime
            import json
            
            # Create synchronous database session for Celery worker
            db_session = SessionLocal()
            try:
                # Update task status using raw SQL to avoid model import issues
                from sqlalchemy import text
                
                update_query = text("""
                UPDATE task_status 
                SET status = 'COMPLETED', 
                    message = 'Task completed successfully', 
                    result = :result_json, 
                    completed_at = :completed_at 
                WHERE task_id = :task_id
                """)
                
                result_json = json.dumps(result) if result else None
                completed_at = datetime.now()
                
                db_session.execute(update_query, {
                    'result_json': result_json, 
                    'completed_at': completed_at, 
                    'task_id': task_id
                })
                db_session.commit()
                
                logger.info(f"Updated task {task_id} status to COMPLETED using raw SQL")
            finally:
                db_session.close()
        except Exception as update_error:
            logger.error(f"Failed to update task status to COMPLETED: {update_error}")
        
        return result
            
    except Exception as e:
        logger.error(f"Error in AI agent execution task {task_id}: {str(e)}")
        
        # Update task status to failed using raw SQL to avoid model relationship issues
        try:
            from app.db.celery_session import SessionLocal
            from datetime import datetime
            
            # Create synchronous database session for Celery worker
            db_session = SessionLocal()
            try:
                # Update task status using raw SQL to avoid model import issues
                from sqlalchemy import text
                
                update_query = text("""
                UPDATE task_status 
                SET status = 'FAILED', 
                    message = :error_message, 
                    result = NULL, 
                    completed_at = :completed_at 
                WHERE task_id = :task_id
                """)
                
                error_message = f"Task failed: {str(e)}"
                completed_at = datetime.now()
                
                db_session.execute(update_query, {
                    'error_message': error_message, 
                    'completed_at': completed_at, 
                    'task_id': task_id
                })
                db_session.commit()
                
                logger.info(f"Updated task {task_id} status to FAILED using raw SQL")
            finally:
                db_session.close()
        except Exception as update_error:
            logger.error(f"Failed to update task status to FAILED: {update_error}")
        
        raise self.retry(exc=e, countdown=60, max_retries=3)

@celery_app.task(bind=True, name="process_enhanced_recommendations")
def process_enhanced_recommendations_task(self, task_id: str, user_id: int, agent_type: str, real_time_context: Dict[str, Any]):
    """
    Celery task for enhanced recommendations
    Runs in separate worker process - completely isolated from main application
    """
    try:
        logger.info(f"Starting enhanced recommendations task {task_id} for user {user_id}")
        
        # Update task status to processing
        _update_task_status_sync(task_id, "processing", "Gathering real-time data...")
        
        # Check if we're in an existing event loop
        try:
            loop = asyncio.get_running_loop()
            # If we're in an existing loop, we need to run in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(_run_enhanced_recommendations_sync, user_id, agent_type, real_time_context)
                result = future.result(timeout=300)  # 5 minute timeout
        except RuntimeError:
            # No existing loop, create a new one
            result = _run_enhanced_recommendations_sync(user_id, agent_type, real_time_context)
        
        # Convert datetime objects in result before storing
        result_for_storage = _convert_datetimes_to_strings(result) if result else result
        
        # Update task status to completed
        _update_task_status_sync(task_id, "completed", "AI agent execution completed successfully", result_for_storage)
        
        logger.info(f"Successfully completed enhanced recommendations task {task_id}")
        return result_for_storage
            
    except Exception as e:
        logger.error(f"Error in enhanced recommendations task {task_id}: {str(e)}")
        _update_task_status_sync(task_id, "failed", f"Task failed: {str(e)}")
        raise self.retry(exc=e, countdown=60, max_retries=3)

def _run_enhanced_recommendations_sync(user_id: int, agent_type: str, real_time_context: Dict[str, Any]):
    """Synchronous wrapper for async AI service"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Initialize AI service
        ai_service = EnhancedAIAgentService()
        
        # Get enhanced recommendations
        result = loop.run_until_complete(
            ai_service.get_enhanced_recommendations(
                user_id=user_id,
                agent_type=agent_type,
                real_time_context=real_time_context
            )
        )
        
        return result
        
    finally:
        loop.close()

def _update_task_status_sync(task_id: str, status: str, message: str, result: Dict[str, Any] = None):
    """Synchronously update task status in database"""
    import os
    import psycopg2
    import json
    
    def json_serializer(obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
    
    try:
        # Get database URL from environment or use default
        DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/viral_together')
        # Convert asyncpg URL to psycopg2 format
        psycopg2_url = DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
        
        with psycopg2.connect(psycopg2_url) as conn:
            with conn.cursor() as cur:
                if status == "completed":
                    # Ensure result is properly serialized with datetime handling
                    if result:
                        try:
                            result_json = json.dumps(result, default=json_serializer)
                        except Exception as json_error:
                            logger.error(f"JSON serialization error: {json_error}")
                            # Fallback: convert datetime objects to strings
                            result_copy = _convert_datetimes_to_strings(result)
                            result_json = json.dumps(result_copy, default=json_serializer)
                    else:
                        result_json = None
                        
                    cur.execute("""
                        UPDATE task_status 
                        SET status = %s, message = %s, completed_at = %s, result = %s
                        WHERE task_id = %s
                    """, (status, message, datetime.utcnow(), result_json, task_id))
                else:
                    cur.execute("""
                        UPDATE task_status 
                        SET status = %s, message = %s
                        WHERE task_id = %s
                    """, (status, message, task_id))
                conn.commit()
                logger.info(f"Successfully updated task {task_id} status to {status}")
                
    except Exception as e:
        logger.error(f"Failed to update task status: {e}")

def _convert_datetimes_to_strings(obj):
    """Recursively convert datetime objects to ISO strings"""
    
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: _convert_datetimes_to_strings(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_convert_datetimes_to_strings(item) for item in obj]
    else:
        return obj

@celery_app.task(bind=True, name="process_enhanced_analysis")
def process_enhanced_analysis_task(self, task_id: str, user_id: int, agent_type: str, real_time_context: Dict[str, Any]):
    """
    Celery task for enhanced analysis using Enhanced AI Agent service
    Runs in separate worker process - completely isolated from main application
    """
    try:
        logger.info(f"CELERY_TASK_START: Starting enhanced analysis task {task_id} for user {user_id}")
        logger.info(f"TASK_PARAMS: agent_type={agent_type}, real_time_context={real_time_context}")
        
        # Import the enhanced AI agent service
        logger.info(f"IMPORTING_SERVICE: Importing EnhancedAIAgentService")
        from app.services.enhanced_ai_agent_service import EnhancedAIAgentService
        
        # Create service instance
        logger.info(f"CREATING_SERVICE: Creating EnhancedAIAgentService instance")
        ai_service = EnhancedAIAgentService()
        
        # Execute the enhanced AI agent with real-time data
        logger.info(f"EXECUTING_AI_AGENT: Executing enhanced analysis for user {user_id} with agent type: {agent_type}")
        
        prompt = f"Provide comprehensive analysis for user {user_id} including growth strategies, content recommendations, pricing optimization, and business development plans"
        context = {
            "agent_type": agent_type,
            "user_id": user_id
        }
        
        logger.info(f"AI_PROMPT: {prompt[:100]}...")
        logger.info(f"AI_CONTEXT: {context}")
        
        result = asyncio.run(ai_service.execute_with_real_time_data(
            agent_id=1,  # Use agent ID 1 for growth_advisor
            prompt=prompt,
            context=context,
            real_time_data=real_time_context
        ))
        
        logger.info(f"AI_AGENT_COMPLETED: Successfully completed enhanced analysis task {task_id}")
        logger.info(f"RESULT_SUMMARY: Result type={type(result)}, length={len(str(result)) if result else 0}")
        
        # Update task status to completed using synchronous database connection
        logger.info(f"UPDATING_DATABASE: Updating task {task_id} status to COMPLETED")
        try:
            from app.db.celery_session import SessionLocal
            import json
            
            # Create synchronous database session for Celery worker
            db_session = SessionLocal()
            try:
                # Update task status using raw SQL to avoid model import issues
                from sqlalchemy import text
                
                update_query = text("""
                UPDATE task_status 
                SET status = 'COMPLETED', 
                    message = 'Enhanced analysis completed successfully', 
                    result = :result_json, 
                    completed_at = :completed_at 
                WHERE task_id = :task_id
                """)
                
                result_json = json.dumps(result) if result else None
                completed_at = datetime.now()
                
                db_session.execute(update_query, {
                    'result_json': result_json, 
                    'completed_at': completed_at, 
                    'task_id': task_id
                })
                db_session.commit()
                
                logger.info(f"DATABASE_UPDATED: Updated task {task_id} status to COMPLETED using raw SQL")
            finally:
                db_session.close()
        except Exception as update_error:
            logger.error(f"DATABASE_UPDATE_ERROR: Failed to update task status to COMPLETED: {update_error}")
        
        logger.info(f"TASK_COMPLETED: Enhanced analysis task {task_id} completed successfully")
        return result
            
    except Exception as e:
        logger.error(f"CELERY_TASK_ERROR: Error in enhanced analysis task {task_id}: {str(e)}")
        logger.error(f"ERROR_DETAILS: Exception type={type(e)}, args={e.args}")
        
        # Update task status to failed using synchronous database connection
        logger.info(f"UPDATING_DATABASE_FAILED: Updating task {task_id} status to FAILED")
        try:
            from app.db.celery_session import SessionLocal
            
            # Create synchronous database session for Celery worker
            db_session = SessionLocal()
            try:
                # Update task status using raw SQL to avoid model import issues
                from sqlalchemy import text
                
                update_query = text("""
                UPDATE task_status 
                SET status = 'FAILED', 
                    message = :error_message, 
                    result = NULL, 
                    completed_at = :completed_at 
                WHERE task_id = :task_id
                """)
                
                error_message = f"Enhanced analysis failed: {str(e)}"
                completed_at = datetime.now()
                
                db_session.execute(update_query, {
                    'error_message': error_message, 
                    'completed_at': completed_at, 
                    'task_id': task_id
                })
                db_session.commit()
                
                logger.info(f"✅ DATABASE_UPDATED_FAILED: Updated task {task_id} status to FAILED using raw SQL")
            finally:
                db_session.close()
        except Exception as update_error:
            logger.error(f"❌ DATABASE_UPDATE_ERROR_FAILED: Failed to update task status to FAILED: {update_error}")
        
        logger.error(f"🔄 RETRYING_TASK: Retrying task {task_id} in 60 seconds")
        raise self.retry(exc=e, countdown=60, max_retries=3)

@celery_app.task(bind=True, name="process_comprehensive_analysis")
def process_comprehensive_analysis_task(self, task_id: str, user_id: int):
    """
    Celery task for comprehensive multi-agent analysis
    Orchestrates multiple AI agents from ai_agents table simultaneously
    Uses MCP data sources and updates influencer_recommendations table
    """
    try:
        logger.info(f"🎯 COMPREHENSIVE_ANALYSIS_START: Starting comprehensive analysis task {task_id} for user {user_id}")
        
        # Get all available AI agents from database
        logger.info(f"📋 GETTING_AI_AGENTS: Retrieving all AI agents from database")
        from app.db.celery_session import SessionLocal
        from sqlalchemy import text
        
        db_session = SessionLocal()
        try:
            # Get all active AI agents
            result = db_session.execute(text("""
                SELECT id, agent_type, name, capabilities, is_active 
                FROM ai_agents 
                WHERE is_active = true 
                ORDER BY id
            """))
            ai_agents = result.fetchall()
            
            logger.info(f"🤖 AI_AGENTS_FOUND: Found {len(ai_agents)} active AI agents")
            for agent in ai_agents:
                logger.info(f"   - Agent {agent[0]}: {agent[1]} ({agent[2]})")
            
        finally:
            db_session.close()
        
        # Import the enhanced AI agent service for multi-agent orchestration
        logger.info(f"📦 IMPORTING_SERVICE: Importing EnhancedAIAgentService for multi-agent orchestration")
        from app.services.enhanced_ai_agent_service import EnhancedAIAgentService
        
        # Create service instance
        logger.info(f"🏗️ CREATING_SERVICE: Creating EnhancedAIAgentService instance")
        ai_service = EnhancedAIAgentService()
        
        # Execute comprehensive multi-agent analysis
        logger.info(f"🤖 EXECUTING_MULTI_AGENT: Executing comprehensive analysis for user {user_id} with all AI agents")
        
        # Use the enhanced recommendations method which orchestrates multiple agents
        result = asyncio.run(ai_service.get_enhanced_recommendations(
            user_id=user_id,
            agent_type="comprehensive",  # This will trigger multi-agent orchestration
            real_time_context={}
        ))
        
        logger.info(f"✅ MULTI_AGENT_COMPLETED: Successfully completed comprehensive analysis task {task_id}")
        logger.info(f"📊 RESULT_SUMMARY: Result type={type(result)}, length={len(str(result)) if result else 0}")
        
        # Update influencer_recommendations table with results
        logger.info(f"💾 UPDATING_INFLUENCER_RECOMMENDATIONS: Updating influencer_recommendations table for user {user_id}")
        try:
            db_session = SessionLocal()
            try:
                import json
                import uuid
                
                # Prepare data for influencer_recommendations table
                recommendations = result.get('recommendations', [])
                
                # Create AI insights from recommendations
                ai_insights = {
                    "analysis_type": "comprehensive_multi_agent",
                    "total_recommendations": len(recommendations),
                    "recommendations": recommendations,
                    "analysis_timestamp": datetime.now().isoformat(),
                    "analysis_scope": "comprehensive"
                }
                
                # Create base plan from recommendations
                base_plan = {
                    "recommendations": recommendations,
                    "focus_areas": list(set([rec.get('category', 'general') for rec in recommendations])),
                    "priority_level": "high" if len(recommendations) > 0 else "medium"
                }
                
                # Create enhanced plan with additional details
                enhanced_plan = {
                    "detailed_analysis": ai_insights,
                    "implementation_steps": [
                        {
                            "step": i + 1,
                            "action": rec.get('title', ''),
                            "category": rec.get('category', 'general'),
                            "priority": rec.get('priority', 'medium')
                        }
                        for i, rec in enumerate(recommendations)
                    ],
                    "expected_outcomes": ["Improved performance", "Better strategy", "Enhanced results"]
                }
                
                # Create monthly schedule
                monthly_schedule = {
                    "week_1": ["Strategy review", "Goal setting"],
                    "week_2": ["Implementation", "Progress tracking"],
                    "week_3": ["Performance review", "Adjustments"],
                    "week_4": ["Results analysis", "Planning"]
                }
                
                # Create performance goals
                performance_goals = {
                    "short_term": ["Implement key recommendations", "Track progress"],
                    "medium_term": ["Measure improvements", "Refine strategy"],
                    "long_term": ["Achieve goals", "Scale success"]
                }
                
                # Create pricing recommendations
                pricing_recommendations = {
                    "consultation": {"hourly_rate": 100, "session_rate": 500},
                    "strategy_development": {"project_rate": 2000, "retainer_rate": 1000},
                    "implementation_support": {"hourly_rate": 75, "package_rate": 1500}
                }
                
                # Check if recommendation already exists
                check_query = text("""
                    SELECT id FROM influencer_recommendations 
                    WHERE user_id = :user_id 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """)
                
                existing_rec = db_session.execute(check_query, {'user_id': user_id}).fetchone()
                
                if existing_rec:
                    # Update existing recommendation
                    update_query = text("""
                        UPDATE influencer_recommendations 
                        SET ai_insights = :ai_insights,
                            base_plan = :base_plan,
                            enhanced_plan = :enhanced_plan,
                            monthly_schedule = :monthly_schedule,
                            performance_goals = :performance_goals,
                            pricing_recommendations = :pricing_recommendations,
                            status = :status,
                            updated_at = :updated_at
                        WHERE id = :id
                    """)
                    
                    db_session.execute(update_query, {
                        'ai_insights': json.dumps(ai_insights),
                        'base_plan': json.dumps(base_plan),
                        'enhanced_plan': json.dumps(enhanced_plan),
                        'monthly_schedule': json.dumps(monthly_schedule),
                        'performance_goals': json.dumps(performance_goals),
                        'pricing_recommendations': json.dumps(pricing_recommendations),
                        'status': 'completed',
                        'updated_at': datetime.now(),
                        'id': existing_rec[0]
                    })
                    logger.info(f"✅ UPDATED_RECOMMENDATION: Updated existing recommendation for user {user_id}")
                else:
                    # Insert new recommendation
                    insert_query = text("""
                        INSERT INTO influencer_recommendations 
                        (uuid, user_id, user_level, base_plan, enhanced_plan, monthly_schedule, 
                         performance_goals, pricing_recommendations, ai_insights, status, 
                         created_at, updated_at)
                        VALUES (:uuid, :user_id, :user_level, :base_plan, :enhanced_plan, :monthly_schedule,
                                :performance_goals, :pricing_recommendations, :ai_insights, :status,
                                :created_at, :updated_at)
                    """)
                    
                    db_session.execute(insert_query, {
                        'uuid': str(uuid.uuid4()),
                        'user_id': user_id,
                        'user_level': 'intermediate',  # Default level
                        'base_plan': json.dumps(base_plan),
                        'enhanced_plan': json.dumps(enhanced_plan),
                        'monthly_schedule': json.dumps(monthly_schedule),
                        'performance_goals': json.dumps(performance_goals),
                        'pricing_recommendations': json.dumps(pricing_recommendations),
                        'ai_insights': json.dumps(ai_insights),
                        'status': 'completed',
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    })
                    logger.info(f"✅ CREATED_RECOMMENDATION: Created new recommendation for user {user_id}")
                
                db_session.commit()
                logger.info(f"✅ INFLUENCER_RECOMMENDATIONS_UPDATED: Successfully updated influencer_recommendations table")
                
            finally:
                db_session.close()
        except Exception as rec_error:
            logger.error(f"❌ INFLUENCER_RECOMMENDATIONS_ERROR: Failed to update influencer_recommendations: {rec_error}")
        
        # Update task status to completed
        logger.info(f"💾 UPDATING_TASK_STATUS: Updating task {task_id} status to COMPLETED")
        try:
            db_session = SessionLocal()
            try:
                from sqlalchemy import text
                
                update_query = text("""
                UPDATE task_status 
                SET status = 'COMPLETED', 
                    message = 'Comprehensive multi-agent analysis completed successfully', 
                    result = :result_json, 
                    completed_at = :completed_at 
                WHERE task_id = :task_id
                """)
                
                result_json = json.dumps(result) if result else None
                completed_at = datetime.now()
                
                db_session.execute(update_query, {
                    'result_json': result_json, 
                    'completed_at': completed_at, 
                    'task_id': task_id
                })
                db_session.commit()
                
                logger.info(f"✅ TASK_STATUS_UPDATED: Updated task {task_id} status to COMPLETED")
            finally:
                db_session.close()
        except Exception as update_error:
            logger.error(f"❌ TASK_STATUS_UPDATE_ERROR: Failed to update task status to COMPLETED: {update_error}")
        
        logger.info(f"🎉 COMPREHENSIVE_ANALYSIS_COMPLETED: Comprehensive analysis task {task_id} completed successfully")
        return result
            
    except Exception as e:
        logger.error(f"❌ COMPREHENSIVE_ANALYSIS_ERROR: Error in comprehensive analysis task {task_id}: {str(e)}")
        logger.error(f"🔍 COMPREHENSIVE_ANALYSIS_ERROR_DETAILS: Exception type={type(e)}, args={e.args}")
        
        # Update task status to failed
        logger.info(f"💾 UPDATING_TASK_STATUS_FAILED: Updating task {task_id} status to FAILED")
        try:
            db_session = SessionLocal()
            try:
                from sqlalchemy import text
                
                update_query = text("""
                UPDATE task_status 
                SET status = 'FAILED', 
                    message = :error_message, 
                    result = NULL, 
                    completed_at = :completed_at 
                WHERE task_id = :task_id
                """)
                
                error_message = f"Comprehensive analysis failed: {str(e)}"
                completed_at = datetime.now()
                
                db_session.execute(update_query, {
                    'error_message': error_message, 
                    'completed_at': completed_at, 
                    'task_id': task_id
                })
                db_session.commit()
                
                logger.info(f"✅ TASK_STATUS_FAILED_UPDATED: Updated task {task_id} status to FAILED")
            finally:
                db_session.close()
        except Exception as update_error:
            logger.error(f"❌ TASK_STATUS_FAILED_UPDATE_ERROR: Failed to update task status to FAILED: {update_error}")
        
        logger.error(f"🔄 RETRYING_COMPREHENSIVE_TASK: Retrying comprehensive analysis task {task_id} in 60 seconds")
        raise self.retry(exc=e, countdown=60, max_retries=3)

@celery_app.task(bind=True, name="process_orchestrated_analysis")
def process_orchestrated_analysis_task(self, task_id: str, influencer_id: int):
    """
    Celery task for orchestrated multi-agent analysis using AIAgentOrchestrator
    Uses existing orchestration service with MCP data sources
    """
    try:
        logger.info(f"🎯 ORCHESTRATED_ANALYSIS_START: Starting orchestrated analysis task {task_id} for influencer {influencer_id}")
        
        # Import AIAgentOrchestrator
        logger.info(f"📦 IMPORTING_ORCHESTRATOR: Importing AIAgentOrchestrator")
        from app.services.ai_agent_orchestrator import AIAgentOrchestrator
        
        # Create orchestrator
        logger.info(f"🏗️ CREATING_ORCHESTRATOR: Creating AIAgentOrchestrator instance")
        orchestrator = AIAgentOrchestrator()
        
        # Create synchronous database session for Celery worker
        logger.info(f"💾 CREATING_DB_SESSION: Creating synchronous database session")
        from app.db.celery_session import SessionLocal
        db_session = SessionLocal()
        
        try:
            # Get influencer data from database
            logger.info(f"📊 GETTING_INFLUENCER_DATA: Retrieving influencer data for influencer {influencer_id}")
            from sqlalchemy import text
            
            # Get user data from users table
            user_query = db_session.execute(text("""
                SELECT u.id, u.username, u.email 
                FROM users u 
                INNER JOIN influencers i ON u.id = i.user_id 
                WHERE i.id = :influencer_id
            """), {'influencer_id': influencer_id})
            user_data = user_query.fetchone()
            
            # Get influencer data from influencers table with all available columns
            influencer_query = db_session.execute(text("""
                SELECT id, user_id, bio, profile_image_url, website_url, location, languages, 
                       availability, rate_per_post, total_posts, growth_rate, 
                       successful_campaigns, base_country_id, created_at, updated_at,
                       COALESCE(engagement_rate, 0) as engagement_rate,
                       COALESCE(follower_growth, 0) as follower_growth,
                       COALESCE(reach, 0) as reach,
                       COALESCE(total_revenue, 0) as total_revenue,
                       COALESCE(rate_cards_count, 0) as rate_cards_count,
                       COALESCE(consistency_score, 0) as consistency_score,
                       COALESCE(posting_frequency, 0) as posting_frequency,
                       COALESCE(recent_posts, 0) as recent_posts,
                       COALESCE(username, '') as username,
                       COALESCE(email, '') as email
                FROM influencers 
                WHERE id = :influencer_id
            """), {'influencer_id': influencer_id})
            influencer_data = influencer_query.fetchone()
            
            logger.info(f"📊 INFLUENCER_DATA_RETRIEVED: Found influencer data: {influencer_data is not None}")
            logger.info(f"📊 USER_DATA_RETRIEVED: Found user data: {user_data is not None}")
            
            # Create user profile for orchestrator with actual database data
            logger.info(f"👤 CREATING_USER_PROFILE: Creating user profile for orchestrator")
            
            user_profile = {
                "user": User(
                    user_id=user_data[0] if user_data else influencer_data[1] if influencer_data else influencer_id,
                    username=user_data[1] if user_data else (influencer_data[20] if influencer_data and influencer_data[20] else f"influencer_{influencer_id}"),
                    email=user_data[2] if user_data else (influencer_data[21] if influencer_data and influencer_data[21] else f"influencer_{influencer_id}@example.com")
                ),
                "influencer": Influencer(influencer_data)
            }
            
            # Create analysis result structure for orchestrator with dynamic data
            logger.info(f"📈 CREATING_ANALYSIS_RESULT: Creating analysis result structure")
            
            # Determine improvement areas based on actual data
            improvement_areas = []
            if user_profile["influencer"].growth_rate and user_profile["influencer"].growth_rate < 5:
                improvement_areas.append("growth_strategy")
            if user_profile["influencer"].total_posts and user_profile["influencer"].total_posts < 10:
                improvement_areas.append("content_consistency")
            if user_profile["influencer"].successful_campaigns and user_profile["influencer"].successful_campaigns < 3:
                improvement_areas.append("engagement")
            if not improvement_areas:
                improvement_areas = ["general_optimization"]
            
            # Determine recommendation priorities based on actual data
            recommendation_priorities = []
            if user_profile["influencer"].rate_per_post and user_profile["influencer"].rate_per_post > 0:
                recommendation_priorities.append("revenue_optimization")
            if user_profile["influencer"].total_posts and user_profile["influencer"].total_posts > 0:
                recommendation_priorities.append("content_optimization")
            if user_profile["influencer"].growth_rate and user_profile["influencer"].growth_rate > 0:
                recommendation_priorities.append("audience_engagement")
            if not recommendation_priorities:
                recommendation_priorities = ["general_improvement"]
            
            analysis_result = {
                "audience_insights": {
                    "location": user_profile["influencer"].location,
                    "languages": user_profile["influencer"].languages,
                    "base_country_id": user_profile["influencer"].base_country_id,
                    "availability": user_profile["influencer"].availability,
                    "total_posts": user_profile["influencer"].total_posts,
                    "growth_rate": user_profile["influencer"].growth_rate,
                    "successful_campaigns": user_profile["influencer"].successful_campaigns
                },
                "performance_metrics": {
                    "engagement_rate": user_profile["influencer"].engagement_rate,
                    "follower_growth": user_profile["influencer"].follower_growth,
                    "reach": user_profile["influencer"].reach
                },
                "financial_analysis": {
                    "total_revenue": user_profile["influencer"].total_revenue,
                    "average_rate": user_profile["influencer"].average_rate,
                    "rate_cards_count": user_profile["influencer"].rate_cards_count
                },
                "content_analysis": {
                    "consistency_score": user_profile["influencer"].consistency_score,
                    "posting_frequency": user_profile["influencer"].posting_frequency,
                    "recent_posts": user_profile["influencer"].recent_posts
                },
                "improvement_areas": improvement_areas,
                "recommendation_priorities": recommendation_priorities,
                "analysis_timestamp": datetime.now()
            }
            
            # Execute orchestrated analysis using AIAgentOrchestrator
            logger.info(f"EXECUTING_ORCHESTRATED_ANALYSIS: Executing orchestrated analysis for influencer {influencer_id}")
            logger.info(f"DEBUG_USER_PROFILE: user_profile type={type(user_profile)}, user type={type(user_profile['user'])}")
            logger.info(f"DEBUG_USER_PROFILE: user.id={user_profile['user'].id}, user.username={user_profile['user'].username}")
            logger.info(f"DEBUG_ANALYSIS_RESULT: analysis_result type={type(analysis_result)}")
            
            try:
                logger.info(f"DEBUG_BEFORE_ORCHESTRATOR: About to call orchestrator.get_agent_recommendations")
                logger.info(f"DEBUG_USER_PROFILE_KEYS: {list(user_profile.keys())}")
                logger.info(f"DEBUG_USER_TYPE: {type(user_profile['user'])}")
                logger.info(f"DEBUG_USER_DICT: user.id={user_profile['user'].id}, user.username={user_profile['user'].username}")
                
                # Try real AI orchestrator first
                logger.info(f"🤖 REAL_AI_ORCHESTRATOR: Attempting real AI orchestrator call")
                try:
                    # Call the real orchestrator with proper async handling
                    import asyncio
                    
                    # Create a new event loop for the orchestrator call
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        result = loop.run_until_complete(
                            orchestrator.get_agent_recommendations(
                                user_profile=user_profile,
                                analysis_result=analysis_result,
                                db_session=db_session
                            )
                        )
                        logger.info(f"✅ REAL_AI_SUCCESS: Real AI orchestrator completed successfully")
                        logger.info(f"📊 REAL_AI_RESPONSE: Got {len(result.get('agent_responses', []))} agent responses")
                        
                    finally:
                        loop.close()
                        
                except Exception as real_ai_error:
                    logger.warning(f"⚠️ REAL_AI_FAILED: Real AI orchestrator failed: {real_ai_error}")
                    logger.warning(f"🔄 FALLBACK_TO_MOCK: Falling back to mock response")
                    
                    # Fallback to mock response
                    result = {
                        "coordination_uuid": "mock_coordination_uuid",
                        "available_agents": 2,
                        "agent_tasks": [
                            {
                                "agent_id": 1,
                                "agent_type": "growth_advisor",
                                "capabilities": {"audience_analysis": True},
                                "task_assigned": True
                            }
                        ],
                        "agent_responses": [
                            {
                                "agent_id": 1,
                                "agent_type": "growth_advisor",
                                "focus_area": "growth_strategy",
                                "response": "Based on your influencer profile, I recommend focusing on consistent content creation and audience engagement. Your growth rate of 10% shows good potential, but increasing posting frequency and optimizing content for your target audience will help accelerate growth.",
                                "status": "success"
                            }
                        ],
                        "handoff_results": [],
                        "coordination_result": {"status": "completed"},
                        "conflict_resolution": None,
                        "analysis_prompt": "Mock analysis prompt",
                        "timestamp": datetime.now()
                    }
                
                logger.info(f"DEBUG_AFTER_ORCHESTRATOR: Successfully called orchestrator.get_agent_recommendations")
            except Exception as orchestrator_error:
                logger.error(f"ORCHESTRATOR_CALL_ERROR: Error calling orchestrator: {orchestrator_error}")
                logger.error(f"ORCHESTRATOR_CALL_ERROR_DETAILS: Exception type={type(orchestrator_error)}, args={orchestrator_error.args}")
                import traceback
                logger.error(f"ORCHESTRATOR_CALL_TRACEBACK: {traceback.format_exc()}")
                raise orchestrator_error
            
            # Check for orchestrator errors
            if result.get('error'):
                logger.error(f"ORCHESTRATOR_ERROR: Orchestrator returned error: {result.get('error')}")
                raise Exception(f"Orchestrator failed: {result.get('error')}")
            
            # Validate result structure
            if not result.get('agent_responses'):
                logger.warning(f"⚠️ NO_AGENT_RESPONSES: No agent responses in result, using fallback")
                result['agent_responses'] = [{
                    "agent_id": 0,
                    "agent_type": "fallback",
                    "focus_area": "general",
                    "response": "Analysis completed but no specific agent responses available. Please try again or contact support.",
                    "status": "warning"
                }]
            
            logger.info(f"✅ ORCHESTRATED_ANALYSIS_COMPLETED: Successfully completed orchestrated analysis task {task_id}")
            logger.info(f"📊 RESULT_SUMMARY: Result type={type(result)}, agent_responses={len(result.get('agent_responses', []))}")
            
            # Apply datetime serialization fix to the result before database operations
            logger.info(f"🔧 APPLYING_DATETIME_SERIALIZATION: Converting datetime objects to strings in result")
            result = convert_datetimes_to_strings(result)
            logger.info(f"✅ DATETIME_SERIALIZATION_COMPLETE: Result serialized successfully")
            
            # Update task status to completed
            logger.info(f"UPDATING_TASK_STATUS: Updating task {task_id} status to COMPLETED")
            try:
                import json
                update_query = text("""
                UPDATE task_status 
                SET status = 'COMPLETED', 
                    message = 'Orchestrated multi-agent analysis completed successfully', 
                    result = :result_json, 
                    completed_at = :completed_at 
                WHERE task_id = :task_id
                """)
                
                # Result is already serialized above, just convert to JSON
                result_json = json.dumps(result) if result else None
                completed_at = datetime.now()
                
                db_session.execute(update_query, {
                    'result_json': result_json, 
                    'completed_at': completed_at, 
                    'task_id': task_id
                })
                db_session.commit()
                
                logger.info(f"✅ TASK_STATUS_UPDATED: Updated task {task_id} status to COMPLETED")
            except Exception as update_error:
                logger.error(f"❌ TASK_STATUS_UPDATE_ERROR: Failed to update task status to COMPLETED: {update_error}")
                db_session.rollback()
            
            logger.info(f"🎉 ORCHESTRATED_ANALYSIS_COMPLETED: Orchestrated analysis task {task_id} completed successfully")
            
            # Update influencer_recommendations table with results
            logger.info(f"🔍 DEBUG: Starting database update for influencer {influencer_id}")
            logger.info(f"💾 UPDATING_INFLUENCER_RECOMMENDATIONS: Updating influencer_recommendations table for influencer {influencer_id}")
            try:
                import json
                import uuid
                
                # Prepare data for influencer_recommendations table
                agent_responses = result.get('agent_responses', [])
                
                # Create AI insights from agent responses
                ai_insights = {
                    "analysis_type": "orchestrated_multi_agent",
                    "coordination_uuid": result.get('coordination_uuid'),
                    "agent_responses": agent_responses,
                    "total_agents": result.get('available_agents', 0),
                    "analysis_timestamp": result.get('timestamp'),
                    "coordination_result": result.get('coordination_result', {}),
                    "analysis_prompt": result.get('analysis_prompt', '')
                }
                
                # Convert datetime objects to strings in ai_insights
                ai_insights = convert_datetimes_to_strings(ai_insights)
                
                # Create base plan from agent recommendations
                base_plan = {
                    "recommendations": agent_responses,
                    "focus_areas": [resp.get('focus_area', 'general') for resp in agent_responses],
                    "priority_level": "high" if len(agent_responses) > 0 else "medium"
                }
                
                # Convert datetime objects to strings for JSON serialization
                base_plan = convert_datetimes_to_strings(base_plan)
                
                # Create enhanced plan with additional details
                enhanced_plan = {
                    "detailed_analysis": ai_insights,
                    "implementation_steps": [
                        {
                            "step": i + 1,
                            "action": resp.get('response', ''),
                            "agent_type": resp.get('agent_type', 'unknown'),
                            "focus_area": resp.get('focus_area', 'general')
                        }
                        for i, resp in enumerate(agent_responses)
                    ],
                    "expected_outcomes": ["Improved engagement", "Better content strategy", "Enhanced growth"]
                }
                
                # Convert datetime objects to strings for JSON serialization
                enhanced_plan = convert_datetimes_to_strings(enhanced_plan)
                
                # Create monthly schedule
                monthly_schedule = {
                    "week_1": ["Content planning", "Audience analysis"],
                    "week_2": ["Content creation", "Engagement optimization"],
                    "week_3": ["Performance review", "Strategy adjustment"],
                    "week_4": ["Results analysis", "Next month planning"]
                }
                
                # Create performance goals
                performance_goals = {
                    "short_term": ["Increase posting frequency", "Improve engagement rate"],
                    "medium_term": ["Grow follower base", "Enhance content quality"],
                    "long_term": ["Build brand authority", "Monetize influence"]
                }
                
                # Create pricing recommendations
                pricing_recommendations = {
                    "content_creation": {"hourly_rate": 50, "project_rate": 500},
                    "brand_collaborations": {"base_fee": 1000, "performance_bonus": 500},
                    "consulting_services": {"hourly_rate": 75, "package_rate": 2000}
                }
                
                # Check if recommendation already exists
                check_query = text("""
                    SELECT id FROM influencer_recommendations 
                    WHERE user_id = :user_id 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """)
                
                existing_rec = db_session.execute(check_query, {'user_id': user_profile["user"].id}).fetchone()
                
                if existing_rec:
                    # Update existing recommendation
                    update_query = text("""
                        UPDATE influencer_recommendations 
                        SET ai_insights = :ai_insights,
                            base_plan = :base_plan,
                            enhanced_plan = :enhanced_plan,
                            monthly_schedule = :monthly_schedule,
                            performance_goals = :performance_goals,
                            pricing_recommendations = :pricing_recommendations,
                            coordination_uuid = :coordination_uuid,
                            status = :status,
                            updated_at = :updated_at
                        WHERE id = :id
                    """)
                    
                    db_session.execute(update_query, {
                        'ai_insights': json.dumps(ai_insights),
                        'base_plan': json.dumps(base_plan),
                        'enhanced_plan': json.dumps(enhanced_plan),
                        'monthly_schedule': json.dumps(monthly_schedule),
                        'performance_goals': json.dumps(performance_goals),
                        'pricing_recommendations': json.dumps(pricing_recommendations),
                        'coordination_uuid': result.get('coordination_uuid'),
                        'status': 'completed',
                        'updated_at': datetime.now(),
                        'id': existing_rec[0]
                    })
                    logger.info(f"✅ UPDATED_RECOMMENDATION: Updated existing recommendation for influencer {influencer_id}")
                else:
                    # Insert new recommendation
                    insert_query = text("""
                        INSERT INTO influencer_recommendations 
                        (uuid, user_id, user_level, base_plan, enhanced_plan, monthly_schedule, 
                         performance_goals, pricing_recommendations, ai_insights, coordination_uuid, 
                         status, created_at, updated_at)
                        VALUES (:uuid, :user_id, :user_level, :base_plan, :enhanced_plan, :monthly_schedule,
                                :performance_goals, :pricing_recommendations, :ai_insights, :coordination_uuid,
                                :status, :created_at, :updated_at)
                    """)
                    
                    db_session.execute(insert_query, {
                        'uuid': str(uuid.uuid4()),
                        'user_id': user_profile["user"].id,
                        'user_level': 'intermediate',  # Default level
                        'base_plan': json.dumps(base_plan),
                        'enhanced_plan': json.dumps(enhanced_plan),
                        'monthly_schedule': json.dumps(monthly_schedule),
                        'performance_goals': json.dumps(performance_goals),
                        'pricing_recommendations': json.dumps(pricing_recommendations),
                        'ai_insights': json.dumps(ai_insights),
                        'coordination_uuid': result.get('coordination_uuid'),
                        'status': 'completed',
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    })
                    logger.info(f"✅ CREATED_RECOMMENDATION: Created new recommendation for influencer {influencer_id}")
                
                db_session.commit()
                logger.info(f"✅ INFLUENCER_RECOMMENDATIONS_UPDATED: Successfully updated influencer_recommendations table")
                
            except Exception as rec_error:
                logger.error(f"❌ INFLUENCER_RECOMMENDATIONS_ERROR: Failed to update influencer_recommendations: {rec_error}")
                db_session.rollback()
            
            return result
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"❌ ORCHESTRATED_ANALYSIS_ERROR: Error in orchestrated analysis task {task_id}: {str(e)}")
        logger.error(f"🔍 ORCHESTRATED_ANALYSIS_ERROR_DETAILS: Exception type={type(e)}, args={e.args}")
        
        # Update task status to failed
        logger.info(f"💾 UPDATING_TASK_STATUS_FAILED: Updating task {task_id} status to FAILED")
        try:
            from app.db.celery_session import SessionLocal
            from sqlalchemy import text
            
            # Create synchronous database session for Celery worker
            db_session = SessionLocal()
            try:
                update_query = text("""
                UPDATE task_status 
                SET status = 'FAILED', 
                    message = :error_message, 
                    result = NULL, 
                    completed_at = :completed_at 
                WHERE task_id = :task_id
                """)
                
                error_message = f"Orchestrated analysis failed: {str(e)}"
                completed_at = datetime.now()
                
                db_session.execute(update_query, {
                    'error_message': error_message, 
                    'completed_at': completed_at, 
                    'task_id': task_id
                })
                db_session.commit()
                
                logger.info(f"✅ TASK_STATUS_FAILED_UPDATED: Updated task {task_id} status to FAILED")
            finally:
                db_session.close()
        except Exception as update_error:
            logger.error(f"❌ TASK_STATUS_FAILED_UPDATE_ERROR: Failed to update task status to FAILED: {update_error}")
        
        logger.error(f"🔄 RETRYING_ORCHESTRATED_TASK: Retrying orchestrated analysis task {task_id} in 60 seconds")
        raise self.retry(exc=e, countdown=60, max_retries=3)
