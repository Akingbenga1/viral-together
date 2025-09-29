"""
Task Queue Service for distributed processing with Celery + Redis
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from celery.result import AsyncResult
from celery.exceptions import CeleryError

from app.core.celery_app import celery_app
from app.schemas.task_status import TaskStatus, TaskStatusEnum
from app.db.models.task_status import TaskStatus as TaskStatusModel
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class TaskQueueService:
    """Service for managing distributed task processing with Celery"""
    
    def __init__(self):
        self.celery_app = celery_app
    
    async def create_task(
        self,
        task_type: str,
        user_id: int,
        task_data: Dict[str, Any],
        db_session: AsyncSession
    ) -> str:
        """Create a new task and return task ID"""
        try:
            task_id = f"{task_type}_{user_id}_{int(datetime.now().timestamp() * 1000)}"
            
            # Create task record in database
            task_status = TaskStatusModel(
                task_id=task_id,
                user_id=user_id,
                task_type=task_type,
                status=TaskStatusEnum.PROCESSING,
                message="Task created",
                created_at=datetime.now(),
                task_data=task_data
            )
            
            db_session.add(task_status)
            await db_session.commit()
            
            logger.info(f"Created task {task_id} of type {task_type} for user {user_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            raise e
    
    async def submit_recommendation_generation_task(
        self,
        user_id: int,
        db_session: AsyncSession
    ) -> str:
        """Submit recommendation generation task to Celery queue"""
        try:
            task_id = await self.create_task(
                task_type="recommendation_generation",
                user_id=user_id,
                task_data={"user_id": user_id},
                db_session=db_session
            )
            
            # Submit task to Celery
            celery_task = celery_app.send_task(
                "process_recommendation_generation",
                args=[task_id, user_id],
                queue="celery"
            )
            
            # Update task with Celery task ID
            await self._update_task_celery_id(task_id, celery_task.id, db_session)
            
            logger.info(f"Submitted recommendation generation task {task_id} to Celery queue")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to submit recommendation generation task: {e}")
            raise e
    
    async def submit_custom_text_analysis_task(
        self,
        text_content: str,
        user_id: Optional[int],
        db_session: AsyncSession
    ) -> str:
        """Submit custom text analysis task to Celery queue"""
        try:
            task_id = await self.create_task(
                task_type="custom_text_analysis",
                user_id=user_id or 0,
                task_data={"text_content": text_content, "user_id": user_id},
                db_session=db_session
            )
            
            # Submit task to Celery
            celery_task = celery_app.send_task(
                "process_custom_text_analysis",
                args=[task_id, text_content, user_id],
                queue="celery"
            )
            
            # Update task with Celery task ID
            await self._update_task_celery_id(task_id, celery_task.id, db_session)
            
            logger.info(f"Submitted custom text analysis task {task_id} to Celery queue")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to submit custom text analysis task: {e}")
            raise e
    
    async def submit_ai_agent_execution_task(
        self,
        agent_id: int,
        prompt: str,
        context: Dict[str, Any],
        real_time_data: Dict[str, Any],
        db_session: AsyncSession
    ) -> str:
        """Submit AI agent execution task to Celery queue"""
        try:
            user_id = context.get("user_id", 0)
            task_id = await self.create_task(
                task_type="ai_agent_execution",
                user_id=user_id,
                task_data={
                    "agent_id": agent_id,
                    "prompt": prompt,
                    "context": context,
                    "real_time_data": real_time_data
                },
                db_session=db_session
            )
            
            # Use synchronous execution for now (Celery has compatibility issues)
            logger.info(f"Executing AI agent task {task_id} synchronously")
            
            try:
                # Import and execute the task function directly
                from app.tasks.ai_agent_tasks import process_ai_agent_execution_task
                
                # Execute task synchronously
                result = process_ai_agent_execution_task(
                    task_id, agent_id, prompt, context, real_time_data
                )
                
                # Update task status to completed
                await self._update_task_status(task_id, TaskStatusEnum.COMPLETED, "Task completed synchronously", result, db_session)
                
                logger.info(f"Completed AI agent execution task {task_id} synchronously")
                return task_id
                
            except Exception as sync_error:
                logger.error(f"Synchronous execution failed: {sync_error}")
                await self._update_task_status(task_id, TaskStatusEnum.FAILED, f"Task failed: {sync_error}", None, db_session)
                raise sync_error
            
        except Exception as e:
            logger.error(f"Failed to submit AI agent execution task: {e}")
            raise e
    
    async def submit_enhanced_recommendations_task(
        self,
        user_id: int,
        agent_type: str,
        real_time_context: Dict[str, Any],
        db_session: AsyncSession
    ) -> str:
        """Submit enhanced recommendations task to Celery queue"""
        try:
            task_id = await self.create_task(
                task_type="enhanced_recommendations",
                user_id=user_id,
                task_data={
                    "user_id": user_id,
                    "agent_type": agent_type,
                    "real_time_context": real_time_context
                },
                db_session=db_session
            )
            
            # Submit task to Celery
            celery_task = celery_app.send_task(
                "process_enhanced_recommendations",
                args=[task_id, user_id, agent_type, real_time_context],
                queue="celery"
            )
            
            # Update task with Celery task ID
            await self._update_task_celery_id(task_id, celery_task.id, db_session)
            
            logger.info(f"Submitted enhanced recommendations task {task_id} to Celery queue")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to submit enhanced recommendations task: {e}")
            raise e
    
    async def get_task_status(self, task_id: str, db_session: AsyncSession) -> Optional[TaskStatus]:
        """Get task status from database"""
        try:
            # Get task from database
            task_record = await db_session.get(TaskStatusModel, task_id)
            if not task_record:
                return None
            
            # Check Celery task status if available
            if task_record.celery_task_id:
                try:
                    celery_result = AsyncResult(task_record.celery_task_id, app=celery_app)
                    if celery_result.state == "SUCCESS":
                        await self._update_task_status(
                            task_id, TaskStatusEnum.COMPLETED, 
                            "Task completed successfully", 
                            celery_result.result, db_session
                        )
                    elif celery_result.state == "FAILURE":
                        await self._update_task_status(
                            task_id, TaskStatusEnum.FAILED, 
                            f"Task failed: {celery_result.result}", 
                            None, db_session
                        )
                except CeleryError as e:
                    logger.warning(f"Failed to check Celery task status: {e}")
            
            return TaskStatus(
                task_id=task_record.task_id,
                user_id=task_record.user_id,
                task_type=task_record.task_type,
                status=task_record.status,
                message=task_record.message,
                created_at=task_record.created_at,
                completed_at=task_record.completed_at,
                result=task_record.result,
                error_details=task_record.error_details
            )
            
        except Exception as e:
            logger.error(f"Failed to get task status: {e}")
            return None
    
    async def get_user_tasks(
        self, 
        user_id: int, 
        db_session: AsyncSession,
        task_type: Optional[str] = None
    ) -> List[TaskStatus]:
        """Get all tasks for a user"""
        try:
            from sqlalchemy import select
            
            query = select(TaskStatusModel).where(TaskStatusModel.user_id == user_id)
            
            if task_type:
                query = query.where(TaskStatusModel.task_type == task_type)
            
            query = query.order_by(TaskStatusModel.created_at.desc())
            tasks = await db_session.execute(query)
            task_records = tasks.scalars().all()
            
            return [
                TaskStatus(
                    task_id=task.task_id,
                    user_id=task.user_id,
                    task_type=task.task_type,
                    status=task.status,
                    message=task.message,
                    created_at=task.created_at,
                    completed_at=task.completed_at,
                    result=task.result,
                    error_details=task.error_details
                )
                for task in task_records
            ]
            
        except Exception as e:
            logger.error(f"Failed to get user tasks: {e}")
            return []
    
    async def get_tasks_by_status(
        self, 
        status: TaskStatusEnum, 
        db_session: AsyncSession
    ) -> List[TaskStatus]:
        """Get tasks by status"""
        try:
            from sqlalchemy import select
            
            query = select(TaskStatusModel).where(TaskStatusModel.status == status)
            query = query.order_by(TaskStatusModel.created_at.desc())
            tasks = await db_session.execute(query)
            task_records = tasks.scalars().all()
            
            return [
                TaskStatus(
                    task_id=task.task_id,
                    user_id=task.user_id,
                    task_type=task.task_type,
                    status=task.status,
                    message=task.message,
                    created_at=task.created_at,
                    completed_at=task.completed_at,
                    result=task.result,
                    error_details=task.error_details
                )
                for task in task_records
            ]
            
        except Exception as e:
            logger.error(f"Failed to get tasks by status: {e}")
            return []
    
    async def _update_task_celery_id(
        self, 
        task_id: str, 
        celery_task_id: str, 
        db_session: AsyncSession
    ):
        """Update task with Celery task ID"""
        try:
            task_record = await db_session.get(TaskStatusModel, task_id)
            if task_record:
                task_record.celery_task_id = celery_task_id
                await db_session.commit()
        except Exception as e:
            logger.error(f"Failed to update task Celery ID: {e}")
    
    async def _update_task_status(
        self,
        task_id: str,
        status: TaskStatusEnum,
        message: str,
        result: Optional[Dict[str, Any]],
        db_session: AsyncSession
    ):
        """Update task status in database"""
        try:
            task_record = await db_session.get(TaskStatusModel, task_id)
            if task_record:
                task_record.status = status
                task_record.message = message
                task_record.result = result
                if status in [TaskStatusEnum.COMPLETED, TaskStatusEnum.FAILED]:
                    task_record.completed_at = datetime.now()
                await db_session.commit()
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")

# Global instance
task_queue_service = TaskQueueService()
