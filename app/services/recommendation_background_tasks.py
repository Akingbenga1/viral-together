from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.cron_scheduler import CronJobScheduler
from app.services.user_profile_analyzer import UserProfileAnalyzer
from app.services.ai_agent_orchestrator import AIAgentOrchestrator
from app.services.influencer_plan_recommender import InfluencerPlanRecommender
from app.services.enhanced_ai_agent_service import EnhancedAIAgentService
from app.schemas.influencer_recommendations import InfluencerRecommendationsCreate
from app.db.models.influencer_recommendations import InfluencerRecommendations
from app.schemas.task_status import TaskStatus, TaskStatusEnum
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

logger = logging.getLogger(__name__)

# In-memory task store (in production, this should be Redis or database)
task_store: Dict[str, TaskStatus] = {}

class RecommendationBackgroundTaskService:
    """Service for handling recommendation and AI agent background tasks"""
    
    def __init__(self):
        self.task_store = task_store
        self.enhanced_ai_service = EnhancedAIAgentService()
        # Thread pool for CPU-intensive tasks to avoid blocking the event loop
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ai_agent_worker")
    
    async def update_task_status(
        self, 
        task_id: str, 
        status: TaskStatusEnum, 
        message: str, 
        result: Optional[Dict[str, Any]] = None,
        error_details: Optional[str] = None
    ):
        """Update task status in the task store"""
        current_time = datetime.now()
        
        task_status = TaskStatus(
            task_id=task_id,
            status=status,
            message=message,
            created_at=self.task_store.get(task_id, TaskStatus(
                task_id=task_id,
                status=TaskStatusEnum.PROCESSING,
                message="Task created",
                created_at=current_time,
                task_type="unknown"
            )).created_at,
            completed_at=current_time if status in [TaskStatusEnum.COMPLETED, TaskStatusEnum.FAILED, TaskStatusEnum.CANCELLED] else None,
            result=result,
            error_details=error_details,
            user_id=self.task_store.get(task_id, TaskStatus(
                task_id=task_id,
                status=TaskStatusEnum.PROCESSING,
                message="Task created",
                created_at=current_time,
                task_type="unknown"
            )).user_id,
            task_type=self.task_store.get(task_id, TaskStatus(
                task_id=task_id,
                status=TaskStatusEnum.PROCESSING,
                message="Task created",
                created_at=current_time,
                task_type="unknown"
            )).task_type
        )
        
        self.task_store[task_id] = task_status
        logger.info(f"Task {task_id} status updated to {status}: {message}")
    
    async def create_task(
        self,
        task_id: str,
        user_id: int,
        task_type: str,
        message: str = "Task created"
    ):
        """Create a new task in the task store"""
        task_status = TaskStatus(
            task_id=task_id,
            status=TaskStatusEnum.PROCESSING,
            message=message,
            created_at=datetime.now(),
            user_id=user_id,
            task_type=task_type
        )
        
        self.task_store[task_id] = task_status
        logger.info(f"Created task {task_id} for user {user_id} of type {task_type}")
    
    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get task status by task ID"""
        return self.task_store.get(task_id)
    
    async def get_user_tasks(self, user_id: int, task_type: Optional[str] = None) -> list[TaskStatus]:
        """Get all tasks for a user, optionally filtered by task type"""
        user_tasks = [
            task for task in self.task_store.values() 
            if task.user_id == user_id
        ]
        
        if task_type:
            user_tasks = [task for task in user_tasks if task.task_type == task_type]
        
        return sorted(user_tasks, key=lambda x: x.created_at, reverse=True)
    
    async def process_recommendation_generation(
        self,
        task_id: str,
        user_id: int,
        db_session: AsyncSession
    ):
        """Background task for recommendation generation using thread pool"""
        try:
            logger.info(f"Starting recommendation generation for user {user_id}, task {task_id}")
            
            # Update status
            await self.update_task_status(
                task_id=task_id,
                status=TaskStatusEnum.PROCESSING,
                message="Starting recommendation generation..."
            )
            
            # Run heavy recommendation processing in separate thread
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._generate_recommendation_sync,
                task_id, user_id, db_session
            )
            
            # Update status with success
            await self.update_task_status(
                task_id=task_id,
                status=TaskStatusEnum.COMPLETED,
                message="Recommendation generated successfully",
                result=result
            )
            
            logger.info(f"Successfully completed recommendation generation for user {user_id}, task {task_id}")
            
        except Exception as e:
            logger.error(f"Error in recommendation generation task {task_id}: {str(e)}")
            await self.update_task_status(
                task_id=task_id,
                status=TaskStatusEnum.FAILED,
                message=f"Error generating recommendations: {str(e)}",
                error_details=str(e)
            )
    
    def _generate_recommendation_sync(self, task_id: str, user_id: int, db_session: AsyncSession):
        """Synchronous recommendation generation - runs in separate thread"""
        try:
            # Create a new event loop for this thread
            import asyncio
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
                        db_session=db_session
                    )
                )
                
                # Generate influencer plan recommendations
                plan_recommendations = plan_recommender.generate_monthly_plans(
                    user_profile=user_profile,
                    ai_recommendations=ai_recommendations,
                    analysis_result=analysis_result
                )
                
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
                
                return {
                    "recommendation_id": recommendation.id,
                    "user_level": plan_recommendations["user_level"],
                    "coordination_uuid": ai_recommendations.get("coordination_uuid"),
                    "generated_at": datetime.now().isoformat()
                }
                
            finally:
                loop.close()
            
        except Exception as e:
            logger.error(f"Error in sync recommendation generation: {str(e)}")
            raise e
    
    async def process_custom_text_analysis(
        self,
        task_id: str,
        text_content: str,
        user_id: Optional[int],
        db_session: AsyncSession
    ):
        """Background task for custom text analysis using thread pool"""
        try:
            logger.info(f"Starting custom text analysis for task {task_id}")
            
            # Update status
            await self.update_task_status(
                task_id=task_id,
                status=TaskStatusEnum.PROCESSING,
                message="Starting custom text analysis..."
            )
            
            # Run heavy text analysis processing in separate thread
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._analyze_custom_text_sync,
                task_id, text_content, user_id, db_session
            )
            
            # Update status with success
            await self.update_task_status(
                task_id=task_id,
                status=TaskStatusEnum.COMPLETED,
                message="Custom text analysis completed successfully",
                result=result
            )
            
            logger.info(f"Successfully completed custom text analysis for task {task_id}")
            
        except Exception as e:
            logger.error(f"Error in custom text analysis task {task_id}: {str(e)}")
            await self.update_task_status(
                task_id=task_id,
                status=TaskStatusEnum.FAILED,
                message=f"Error analyzing custom text: {str(e)}",
                error_details=str(e)
            )
    
    def _analyze_custom_text_sync(self, task_id: str, text_content: str, user_id: Optional[int], db_session: AsyncSession):
        """Synchronous custom text analysis - runs in separate thread"""
        try:
            # Create a new event loop for this thread
            import asyncio
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
                
                # Get custom text recommendations using the new function
                custom_recommendations = loop.run_until_complete(
                    ai_orchestrator.get_custom_text_recommendations(
                        text_content=text_content,
                        user_profile=user_profile,
                        db_session=db_session
                    )
                )
                
                # Check for errors
                if custom_recommendations.get("error"):
                    raise Exception(custom_recommendations["error"])
                
                return {
                    "coordination_uuid": custom_recommendations.get("coordination_uuid"),
                    "available_agents": custom_recommendations.get("available_agents", 0),
                    "agent_responses": custom_recommendations.get("agent_responses", []),
                    "custom_prompt": custom_recommendations.get("custom_prompt", ""),
                    "text_content_length": custom_recommendations.get("text_content_length", 0),
                    "timestamp": custom_recommendations.get("timestamp", datetime.now()).isoformat()
                }
                
            finally:
                loop.close()
            
        except Exception as e:
            logger.error(f"Error in sync custom text analysis: {str(e)}")
            raise e
    
    async def process_ai_agent_execution(
        self,
        task_id: str,
        agent_id: int,
        prompt: str,
        context: Dict[str, Any],
        real_time_data: Dict[str, Any],
        db_session: AsyncSession
    ):
        """Background task for AI agent execution using thread pool"""
        try:
            logger.info(f"Starting AI agent execution for task {task_id}, agent {agent_id}")
            
            # Update status
            await self.update_task_status(
                task_id=task_id,
                status=TaskStatusEnum.PROCESSING,
                message="Starting AI agent execution..."
            )
            
            # Run heavy AI agent processing in separate thread
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._execute_ai_agent_sync,
                task_id, agent_id, prompt, context, real_time_data, db_session
            )
            
            # Update status with success
            await self.update_task_status(
                task_id=task_id,
                status=TaskStatusEnum.COMPLETED,
                message="AI agent execution completed successfully",
                result=result
            )
            
            logger.info(f"Successfully completed AI agent execution for task {task_id}")
            
        except Exception as e:
            logger.error(f"Error in AI agent execution task {task_id}: {str(e)}")
            await self.update_task_status(
                task_id=task_id,
                status=TaskStatusEnum.FAILED,
                message=f"Error executing AI agent: {str(e)}",
                error_details=str(e)
            )
    
    def _execute_ai_agent_sync(self, task_id: str, agent_id: int, prompt: str, context: Dict[str, Any], real_time_data: Dict[str, Any], db_session: AsyncSession):
        """Synchronous AI agent execution - runs in separate thread"""
        try:
            # Create a new event loop for this thread
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Execute enhanced agent using the existing async method
                result = loop.run_until_complete(
                    self.enhanced_ai_service.execute_with_real_time_data(
                        agent_id=agent_id,
                        prompt=prompt,
                        context=context,
                        real_time_data=real_time_data
                    )
                )
                
                return {
                    "agent_id": agent_id,
                    "agent_type": context.get("agent_type", "general"),
                    "response": result.get("response", ""),
                    "status": result.get("status", "success"),
                    "architecture_version": result.get("architecture_version", "v2_enhanced"),
                    "executed_at": datetime.now().isoformat()
                }
                
            finally:
                loop.close()
            
        except Exception as e:
            logger.error(f"Error in sync AI agent execution: {str(e)}")
            raise e

# Global instance
recommendation_bg_task_service = RecommendationBackgroundTaskService()
