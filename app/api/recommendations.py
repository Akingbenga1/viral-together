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
from app.core.query_helpers import safe_scalar_one_or_none
from datetime import datetime

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.post("/generate/{user_id}")
async def generate_recommendations(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Generate AI recommendations for a specific user using distributed task queue"""
    try:
        # Submit task to Celery queue
        task_id = await task_queue_service.submit_recommendation_generation_task(
            user_id=user_id,
            db_session=db
        )
        
        return {
            "task_id": task_id,
            "status": "processing",
            "message": "Recommendation generation started in distributed queue",
            "user_id": user_id,
            "created_at": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting recommendation generation: {str(e)}"
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
    current_user = Depends(get_current_user)
):
    """Get all recommendations for a specific user"""
    query = select(InfluencerRecommendations).where(
        InfluencerRecommendations.user_id == user_id
    ).order_by(InfluencerRecommendations.created_at.desc())
    
    result = await db.execute(query)
    recommendations = result.scalars().all()
    
    return recommendations

@router.get("/{recommendation_id}", response_model=InfluencerRecommendationsSchema)
async def get_recommendation(
    recommendation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific recommendation by ID"""
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
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Manually trigger analysis for a specific user using background tasks"""
    try:
        # Create unique task ID
        task_id = f"analysis_trigger_{user_id}_{datetime.now().timestamp()}"
        
        # Create task in the task store
        await recommendation_bg_task_service.create_task(
            task_id=task_id,
            user_id=user_id,
            task_type="analysis_trigger",
            message="Analysis trigger task created"
        )
        
        # Add background task
        background_tasks.add_task(
            _process_analysis_trigger,
            task_id=task_id,
            user_id=user_id
        )
        
        return {
            "task_id": task_id,
            "status": "processing",
            "message": f"Analysis triggered for user {user_id} in background",
            "user_id": user_id,
            "created_at": datetime.now()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error triggering analysis: {str(e)}"
        )

async def _process_analysis_trigger(task_id: str, user_id: int):
    """Background task for analysis trigger"""
    try:
        scheduler = CronJobScheduler()
        await scheduler.run_user_analysis_job()
        
        await recommendation_bg_task_service.update_task_status(
            task_id=task_id,
            status=TaskStatusEnum.COMPLETED,
            message=f"Analysis completed for user {user_id}",
            result={"user_id": user_id, "analysis_completed": True}
        )
        
    except Exception as e:
        await recommendation_bg_task_service.update_task_status(
            task_id=task_id,
            status=TaskStatusEnum.FAILED,
            message=f"Error in analysis trigger: {str(e)}",
            error_details=str(e)
        )
