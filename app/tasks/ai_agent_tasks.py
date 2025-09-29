"""
Celery tasks for AI agent processing
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
from app.services.enhanced_ai_agent_service import EnhancedAIAgentService
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

@celery_app.task(name="process_ai_agent_execution")
def process_ai_agent_execution_task(task_id: str, agent_id: int, prompt: str, context: Dict[str, Any], real_time_data: Dict[str, Any]):
    """
    Celery task for AI agent execution with real-time data
    Runs in separate worker process - completely isolated from main application
    """
    try:
        logger.info(f"Starting AI agent execution task {task_id} for agent {agent_id}")
        
        # Simple test implementation for now
        formatted_result = {
            "agent_id": agent_id,
            "agent_type": context.get("agent_type", "general"),
            "response": f"Test response for prompt: {prompt}",
            "status": "success",
            "architecture_version": "v2_enhanced",
            "executed_at": datetime.now().isoformat()
        }
        
        logger.info(f"Successfully completed AI agent execution task {task_id}")
        return formatted_result
            
    except Exception as e:
        logger.error(f"Error in AI agent execution task {task_id}: {str(e)}")
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
    from datetime import datetime
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
    from datetime import datetime
    
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: _convert_datetimes_to_strings(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_convert_datetimes_to_strings(item) for item in obj]
    else:
        return obj
