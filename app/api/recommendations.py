from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.core.dependencies import get_db, get_current_user
from app.db.models.influencer_recommendations import InfluencerRecommendations
from app.schemas.influencer_recommendations import (
    InfluencerRecommendations as InfluencerRecommendationsSchema, 
    InfluencerRecommendationsCreate,
    CustomTextAnalysisRequest,
    CustomTextAnalysisResponse
)
from app.schemas.task_status import TaskStatusResponse, TaskListResponse, TaskStatusEnum
from app.services.cron_scheduler import CronJobScheduler
from app.services.user_profile_analyzer import UserProfileAnalyzer
from app.services.ai_agent_orchestrator import AIAgentOrchestrator
from app.services.influencer_plan_recommender import InfluencerPlanRecommender
from app.services.task_queue_service import task_queue_service
from app.services.data_transformer import transform_recommendation_for_ui
from app.core.query_helpers import safe_scalar_one_or_none
from datetime import datetime

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.post("/generate/{user_id}")
async def generate_recommendations(
    user_id: int,
    db: AsyncSession = Depends(get_db)
    # Temporarily removed authentication for testing
    # current_user = Depends(get_current_user)
):
    """Generate AI recommendations using Enhanced AI Agents with Celery background tasks"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"🚀 GENERATE_RECOMMENDATIONS_START: Processing generate recommendations request for user {user_id}")
        
        # Submit task to Celery queue using Enhanced AI Agent service
        logger.info(f"📤 SUBMITTING_ENHANCED_TASK: Submitting enhanced recommendations task for user {user_id} with agent_type=growth_advisor")
        
        task_id = await task_queue_service.submit_enhanced_analysis_task(
            user_id=user_id,
            agent_type="growth_advisor",  # Use growth_advisor for comprehensive recommendations
            real_time_context={},
            db_session=db
        )
        
        logger.info(f"✅ ENHANCED_TASK_SUBMITTED: Enhanced recommendations task {task_id} submitted successfully for user {user_id}")
        
        response_data = {
            "task_id": task_id,
            "status": "processing",
            "message": f"Enhanced AI recommendations generation triggered for user {user_id}",
            "user_id": user_id,
            "created_at": datetime.now()
        }
        
        logger.info(f"📋 GENERATE_RESPONSE_SENT: Returning response for user {user_id}: {response_data}")
        return response_data
        
    except Exception as e:
        logger.error(f"❌ GENERATE_RECOMMENDATIONS_ERROR: Failed to trigger enhanced recommendations for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting enhanced recommendation generation: {str(e)}"
        )

@router.post("/custom-text-analysis")
async def analyze_custom_text(
    request: CustomTextAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Analyze custom text content using AI agents in distributed queue"""
    try:
        # Submit task to Celery queue
        task_id = await task_queue_service.submit_custom_text_analysis_task(
            text_content=request.text_content,
            user_id=request.user_id,
            db_session=db
        )
        
        return {
            "task_id": task_id,
            "status": "processing",
            "message": "Custom text analysis started in distributed queue",
            "user_id": request.user_id,
            "text_content_length": len(request.text_content),
            "created_at": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting custom text analysis: {str(e)}"
        )

@router.get("/user/{user_id}", response_model=List[InfluencerRecommendationsSchema])
async def get_user_recommendations(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    transform_for_ui: bool = True
):
    """Get all recommendations for a specific user with optional UI transformation"""
    query = select(InfluencerRecommendations).where(
        InfluencerRecommendations.user_id == user_id
    ).order_by(InfluencerRecommendations.created_at.desc())
    
    result = await db.execute(query)
    recommendations = result.scalars().all()
    
    # Apply transformation if enabled
    if transform_for_ui:
        transformed_recommendations = []
        for recommendation in recommendations:
            # Convert SQLAlchemy model to dict for transformation
            recommendation_dict = {
                "id": recommendation.id,
                "uuid": recommendation.uuid,
                "user_id": recommendation.user_id,
                "user_level": recommendation.user_level,
                "base_plan": recommendation.base_plan,
                "enhanced_plan": recommendation.enhanced_plan,
                "monthly_schedule": recommendation.monthly_schedule,
                "performance_goals": recommendation.performance_goals,
                "pricing_recommendations": recommendation.pricing_recommendations,
                "ai_insights": recommendation.ai_insights,
                "coordination_uuid": recommendation.coordination_uuid,
                "status": recommendation.status,
                "created_at": recommendation.created_at,
                "updated_at": recommendation.updated_at
            }
            
            # Transform the recommendation
            transformed = transform_recommendation_for_ui(recommendation_dict, enable_transformation=True)
            transformed_recommendations.append(transformed)
        
        return transformed_recommendations
    
    return recommendations

@router.get("/{recommendation_id}", response_model=InfluencerRecommendationsSchema)
async def get_recommendation(
    recommendation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    transform_for_ui: bool = True
):
    """Get a specific recommendation by ID with optional UI transformation"""
    query = select(InfluencerRecommendations).where(
        InfluencerRecommendations.id == recommendation_id
    )
    
    result = await db.execute(query)
    recommendation = await safe_scalar_one_or_none(result)
    
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found"
        )
    
    # Apply transformation if enabled
    if transform_for_ui:
        # Convert SQLAlchemy model to dict for transformation
        recommendation_dict = {
            "id": recommendation.id,
            "uuid": recommendation.uuid,
            "user_id": recommendation.user_id,
            "user_level": recommendation.user_level,
            "base_plan": recommendation.base_plan,
            "enhanced_plan": recommendation.enhanced_plan,
            "monthly_schedule": recommendation.monthly_schedule,
            "performance_goals": recommendation.performance_goals,
            "pricing_recommendations": recommendation.pricing_recommendations,
            "ai_insights": recommendation.ai_insights,
            "coordination_uuid": recommendation.coordination_uuid,
            "status": recommendation.status,
            "created_at": recommendation.created_at,
            "updated_at": recommendation.updated_at
        }
        
        # Transform the recommendation
        transformed = transform_recommendation_for_ui(recommendation_dict, enable_transformation=True)
        return transformed
    
    return recommendation

@router.put("/{recommendation_id}", response_model=InfluencerRecommendationsSchema)
async def update_recommendation(
    recommendation_id: int,
    recommendation_update: InfluencerRecommendationsCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a recommendation"""
    query = select(InfluencerRecommendations).where(
        InfluencerRecommendations.id == recommendation_id
    )
    
    result = await db.execute(query)
    recommendation = await safe_scalar_one_or_none(result)
    
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found"
        )
    
    # Update fields
    update_data = recommendation_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(recommendation, field, value)
    
    await db.commit()
    await db.refresh(recommendation)
    
    return recommendation

@router.delete("/{recommendation_id}")
async def delete_recommendation(
    recommendation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a recommendation"""
    query = select(InfluencerRecommendations).where(
        InfluencerRecommendations.id == recommendation_id
    )
    
    result = await db.execute(query)
    recommendation = await safe_scalar_one_or_none(result)
    
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found"
        )
    
    await db.delete(recommendation)
    await db.commit()
    
    return {"message": "Recommendation deleted successfully"}

# Task Status Tracking Endpoints

@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get status of a distributed task"""
    task_status = await task_queue_service.get_task_status(task_id, db)
    
    if not task_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return TaskStatusResponse(
        task_id=task_status.task_id,
        status=task_status.status,
        message=task_status.message,
        created_at=task_status.created_at,
        completed_at=task_status.completed_at,
        result=task_status.result,
        error_details=task_status.error_details,
        user_id=task_status.user_id,
        task_type=task_status.task_type
    )

@router.get("/tasks/user/{user_id}", response_model=TaskListResponse)
async def get_user_tasks(
    user_id: int,
    task_type: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Get all tasks for a user, optionally filtered by task type"""
    user_tasks = await recommendation_bg_task_service.get_user_tasks(user_id, task_type)
    
    task_responses = [
        TaskStatusResponse(
            task_id=task.task_id,
            status=task.status,
            message=task.message,
            created_at=task.created_at,
            completed_at=task.completed_at,
            result=task.result,
            error_details=task.error_details,
            user_id=task.user_id,
            task_type=task.task_type
        )
        for task in user_tasks
    ]
    
    return TaskListResponse(
        tasks=task_responses,
        total=len(task_responses),
        page=1,
        page_size=len(task_responses)
    )

@router.get("/tasks/status/{status}")
async def get_tasks_by_status(
    status: str,
    current_user = Depends(get_current_user)
):
    """Get all tasks with a specific status"""
    all_tasks = recommendation_bg_task_service.task_store.values()
    filtered_tasks = [task for task in all_tasks if task.status.value == status]
    
    task_responses = [
        TaskStatusResponse(
            task_id=task.task_id,
            status=task.status,
            message=task.message,
            created_at=task.created_at,
            completed_at=task.completed_at,
            result=task.result,
            error_details=task.error_details,
            user_id=task.user_id,
            task_type=task.task_type
        )
        for task in filtered_tasks
    ]
    
    return {
        "tasks": task_responses,
        "total": len(task_responses),
        "status": status
    }

@router.post("/trigger-analysis/{user_id}")
async def trigger_analysis(
    user_id: int,
    db: AsyncSession = Depends(get_db)
    # Temporarily removed authentication for testing
    # current_user = Depends(get_current_user)
):
    """Manually trigger orchestrated analysis using AIAgentOrchestrator with MCP data sources"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"🚀 TRIGGER_ANALYSIS_START: Processing orchestrated multi-agent analysis for influencer {user_id}")
        
        # Submit task to Celery queue for orchestrated multi-agent analysis
        logger.info(f"📤 SUBMITTING_ORCHESTRATED_ANALYSIS: Submitting orchestrated analysis task for influencer {user_id}")
        
        task_id = await task_queue_service.submit_orchestrated_analysis_task(
            influencer_id=user_id,
            db_session=db
        )
        
        logger.info(f"✅ ORCHESTRATED_ANALYSIS_SUBMITTED: Orchestrated analysis task {task_id} submitted successfully for influencer {user_id}")
        
        response_data = {
            "task_id": task_id,
            "status": "processing",
            "message": f"Orchestrated multi-agent analysis triggered for influencer {user_id}",
            "influencer_id": user_id,
            "created_at": datetime.now()
        }
        
        logger.info(f"📋 RESPONSE_SENT: Returning response for influencer {user_id}: {response_data}")
        return response_data
        
    except Exception as e:
        logger.error(f"❌ TRIGGER_ANALYSIS_ERROR: Failed to trigger orchestrated analysis for influencer {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error triggering orchestrated analysis: {str(e)}"
        )

