"""
Enhanced AI Agents API endpoints with real-time data integration
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.core.dependencies import get_db
from app.services.enhanced_ai_agent_service import EnhancedAIAgentService
from app.services.ai_agent_service import AIAgentService
from app.services.task_queue_service import task_queue_service
from app.schemas.task_status import TaskStatusResponse, TaskListResponse, TaskStatusEnum

router = APIRouter(prefix="/api/enhanced-ai-agents", tags=["Enhanced AI Agents"])

# Initialize services
enhanced_ai_service = EnhancedAIAgentService()
legacy_ai_service = AIAgentService()


@router.post("/execute-with-real-time-data")
async def execute_agent_with_real_time_data(
    request: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Execute AI agent with real-time data integration using distributed task queue"""
    try:
        # Extract request parameters
        agent_id = request.get('agent_id')
        prompt = request.get('prompt')
        context = request.get('context', {})
        real_time_data = request.get('real_time_data', {})
        
        if not agent_id or not prompt:
            raise HTTPException(status_code=400, detail="agent_id and prompt are required")
        
        # Submit task to Celery queue
        task_id = await task_queue_service.submit_ai_agent_execution_task(
            agent_id=agent_id,
            prompt=prompt,
            context=context,
            real_time_data=real_time_data,
            db_session=db
        )
        
        return {
            "task_id": task_id,
            "status": "processing",
            "message": "AI agent execution started in distributed queue",
            "agent_id": agent_id,
            "agent_type": context.get('agent_type', 'general'),
            "created_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start AI agent execution: {str(e)}")


@router.get("/enhanced-recommendations/{user_id}")
async def get_enhanced_recommendations(
    user_id: int,
    agent_type: str = Query(..., description="Type of AI agent"),
    real_time_context: Optional[str] = Query(None, description="Additional real-time context as JSON string"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get enhanced recommendations using distributed task queue"""
    import logging
    import json
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Enhanced recommendations endpoint called for user {user_id} with agent type: {agent_type}")
        
        # Parse real-time context
        if not real_time_context:
            real_time_context_dict = {}
            logger.info(f"No real-time context provided for user {user_id}")
        else:
            try:
                real_time_context_dict = json.loads(real_time_context)
                logger.info(f"Real-time context parsed successfully for user {user_id}: {list(real_time_context_dict.keys())}")
            except json.JSONDecodeError:
                real_time_context_dict = {}
                logger.warning(f"Failed to parse real-time context JSON for user {user_id}")
        
        # Submit task to distributed queue
        task_id = await task_queue_service.submit_enhanced_recommendations_task(
            user_id=user_id,
            agent_type=agent_type,
            real_time_context=real_time_context_dict,
            db_session=db
        )
        
        logger.info(f"Enhanced recommendations task submitted for user {user_id}")
        return {
            "task_id": task_id,
            "status": "processing",
            "message": "Enhanced recommendations generation started in distributed queue",
            "user_id": user_id,
            "agent_type": agent_type,
            "created_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start enhanced recommendations for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start enhanced recommendations: {str(e)}")


@router.get("/agent-capabilities")
async def get_agent_capabilities(
    agent_type: Optional[str] = Query(None, description="Specific agent type to get capabilities for"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get AI agent capabilities and real-time data integration status"""
    try:
        agent_types = [
            'growth_advisor',
            'business_advisor', 
            'content_advisor',
            'analytics_advisor',
            'collaboration_advisor',
            'pricing_advisor',
            'platform_advisor',
            'compliance_advisor',
            'engagement_advisor',
            'optimization_advisor'
        ]
        
        if agent_type and agent_type not in agent_types:
            raise HTTPException(status_code=400, detail=f"Invalid agent type: {agent_type}")
        
        capabilities = {
            "real_time_data_integration": {
                "web_search": True,
                "social_media_apis": True,
                "market_analysis": True,
                "trending_content": True,
                "competitor_analysis": True,
                "engagement_tracking": True,
                "brand_opportunities": True
            },
            "supported_platforms": [
                "twitter",
                "instagram", 
                "youtube",
                "tiktok"
            ],
            "data_sources": [
                "DuckDuckGo Search API",
                "Google Custom Search API",
                "Twitter API v2",
                "Instagram Basic Display API",
                "YouTube Data API v3",
                "TikTok for Business API"
            ],
            "agent_capabilities": {}
        }
        
        # Define capabilities for each agent type
        agent_capabilities = {
            'growth_advisor': {
                "real_time_data": ["trending_content", "engagement_trends", "competitor_analysis"],
                "capabilities": ["audience_growth", "trend_analysis", "engagement_optimization"],
                "data_freshness": "real-time"
            },
            'content_advisor': {
                "real_time_data": ["trending_content", "content_recommendations", "platform_insights"],
                "capabilities": ["content_strategy", "trend_identification", "format_optimization"],
                "data_freshness": "real-time"
            },
            'business_advisor': {
                "real_time_data": ["brand_opportunities", "market_analysis", "pricing_data"],
                "capabilities": ["monetization", "partnership_strategy", "business_development"],
                "data_freshness": "real-time"
            },
            'pricing_advisor': {
                "real_time_data": ["market_rates", "competitor_pricing", "engagement_metrics"],
                "capabilities": ["rate_optimization", "market_analysis", "pricing_strategy"],
                "data_freshness": "real-time"
            },
            'analytics_advisor': {
                "real_time_data": ["engagement_trends", "performance_metrics", "competitor_analysis"],
                "capabilities": ["data_analysis", "performance_optimization", "insights_generation"],
                "data_freshness": "real-time"
            },
            'collaboration_advisor': {
                "real_time_data": ["brand_opportunities", "market_insights", "partnership_trends"],
                "capabilities": ["partnership_matching", "collaboration_strategy", "relationship_building"],
                "data_freshness": "real-time"
            },
            'platform_advisor': {
                "real_time_data": ["platform_trends", "algorithm_insights", "feature_updates"],
                "capabilities": ["platform_optimization", "cross_platform_strategy", "feature_utilization"],
                "data_freshness": "real-time"
            },
            'engagement_advisor': {
                "real_time_data": ["engagement_trends", "audience_insights", "interaction_patterns"],
                "capabilities": ["engagement_optimization", "community_building", "interaction_strategy"],
                "data_freshness": "real-time"
            },
            'optimization_advisor': {
                "real_time_data": ["performance_metrics", "growth_strategies", "optimization_opportunities"],
                "capabilities": ["performance_optimization", "efficiency_improvement", "strategy_refinement"],
                "data_freshness": "real-time"
            },
            'compliance_advisor': {
                "real_time_data": ["regulatory_updates", "platform_policies", "legal_guidelines"],
                "capabilities": ["compliance_monitoring", "policy_guidance", "risk_assessment"],
                "data_freshness": "near_real_time"
            }
        }
        
        if agent_type:
            capabilities["agent_capabilities"] = {agent_type: agent_capabilities.get(agent_type, {})}
        else:
            capabilities["agent_capabilities"] = agent_capabilities
        
        return {
            "success": True,
            "capabilities": capabilities,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent capabilities: {str(e)}")


@router.get("/data-sources/status")
async def get_data_sources_status(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get status of real-time data sources"""
    try:
        # This would typically check the actual status of APIs
        # For now, return mock status
        data_sources_status = {
            "web_search": {
                "duckduckgo": {"status": "active", "rate_limit": "unlimited", "last_check": datetime.now().isoformat()},
                "google": {"status": "active", "rate_limit": "100/day", "last_check": datetime.now().isoformat()}
            },
            "social_media_apis": {
                "twitter": {"status": "active", "rate_limit": "300/hour", "last_check": datetime.now().isoformat()},
                "instagram": {"status": "active", "rate_limit": "200/hour", "last_check": datetime.now().isoformat()},
                "youtube": {"status": "active", "rate_limit": "10000/day", "last_check": datetime.now().isoformat()},
                "tiktok": {"status": "active", "rate_limit": "1000/hour", "last_check": datetime.now().isoformat()}
            },
            "analytics_services": {
                "engagement_tracking": {"status": "active", "data_freshness": "real-time"},
                "market_analysis": {"status": "active", "data_freshness": "real-time"},
                "trending_content": {"status": "active", "data_freshness": "real-time"},
                "competitor_analysis": {"status": "active", "data_freshness": "real-time"}
            }
        }
        
        return {
            "success": True,
            "data_sources_status": data_sources_status,
            "overall_status": "operational",
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get data sources status: {str(e)}")


@router.post("/batch-recommendations")
async def get_batch_recommendations(
    request: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get recommendations from multiple AI agents using distributed task queue"""
    try:
        user_id = request.get('user_id')
        agent_types = request.get('agent_types', [])
        real_time_context = request.get('real_time_context', {})
        
        if not user_id or not agent_types:
            raise HTTPException(status_code=400, detail="user_id and agent_types are required")
        
        # Submit multiple tasks to distributed queue
        task_ids = []
        for agent_type in agent_types:
            try:
                task_id = await task_queue_service.submit_enhanced_recommendations_task(
                    user_id=user_id,
                    agent_type=agent_type,
                    real_time_context=real_time_context,
                    db_session=db
                )
                task_ids.append({
                    "agent_type": agent_type,
                    "task_id": task_id,
                    "status": "processing"
                })
            except Exception as e:
                task_ids.append({
                    "agent_type": agent_type,
                    "task_id": None,
                    "status": "failed",
                    "error": str(e)
                })
        
        return {
            "success": True,
            "user_id": user_id,
            "batch_tasks": task_ids,
            "total_agents": len(agent_types),
            "successful_submissions": len([t for t in task_ids if t["status"] == "processing"]),
            "message": "Batch recommendations started in distributed queue",
            "created_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start batch recommendations: {str(e)}")



# Task Status Tracking Endpoints (reusing existing infrastructure)

@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Get status of a distributed task"""
    task_status = await task_queue_service.get_task_status(task_id, db)
    
    if not task_status:
        raise HTTPException(
            status_code=404,
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
    db: Session = Depends(get_db)
):
    """Get all tasks for a user, optionally filtered by task type"""
    user_tasks = await task_queue_service.get_user_tasks(user_id, db, task_type)
    
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
    db: Session = Depends(get_db)
):
    """Get all tasks with a specific status"""
    from app.schemas.task_status import TaskStatusEnum
    
    try:
        status_enum = TaskStatusEnum(status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    tasks = await task_queue_service.get_tasks_by_status(status_enum, db)
    
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
        for task in tasks
    ]
    
    return TaskListResponse(
        tasks=task_responses,
        total=len(task_responses),
        page=1,
        page_size=len(task_responses)
    )
