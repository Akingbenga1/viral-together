"""
Enhanced AI Agents API endpoints with real-time data integration
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.core.dependencies import get_db
from app.services.enhanced_ai_agent_service import EnhancedAIAgentService
from app.services.ai_agent_service import AIAgentService

router = APIRouter(prefix="/api/enhanced-ai-agents", tags=["Enhanced AI Agents"])

# Initialize services
enhanced_ai_service = EnhancedAIAgentService()
legacy_ai_service = AIAgentService()


@router.post("/execute-with-real-time-data")
async def execute_agent_with_real_time_data(
    request: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Execute AI agent with real-time data integration"""
    try:
        # Extract request parameters
        agent_id = request.get('agent_id')
        prompt = request.get('prompt')
        context = request.get('context', {})
        real_time_data = request.get('real_time_data', {})
        
        if not agent_id or not prompt:
            raise HTTPException(status_code=400, detail="agent_id and prompt are required")
        
        # Execute enhanced agent
        result = await enhanced_ai_service.execute_with_real_time_data(
            agent_id=agent_id,
            prompt=prompt,
            context=context,
            real_time_data=real_time_data
        )
        
        return {
            "success": True,
            "result": result,
            "executed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute enhanced agent: {str(e)}")


@router.get("/enhanced-recommendations/{user_id}")
async def get_enhanced_recommendations(
    user_id: int,
    agent_type: str = Query(..., description="Type of AI agent"),
    real_time_context: Optional[str] = Query(None, description="Additional real-time context as JSON string"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get enhanced recommendations with real-time data"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        import json
        
        logger.info(f"Enhanced recommendations endpoint called for user {user_id} with agent type: {agent_type}")
        
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
        
        logger.info(f"Starting enhanced recommendations generation for user {user_id}")
        result = await enhanced_ai_service.get_enhanced_recommendations(
            user_id=user_id,
            agent_type=agent_type,
            real_time_context=real_time_context_dict
        )
        
        logger.info(f"Enhanced recommendations generated successfully for user {user_id}")
        return {
            "success": True,
            "recommendations": result,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get enhanced recommendations for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get enhanced recommendations: {str(e)}")


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
            'optimization_advisor',
            'content_creator'
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
                "brand_opportunities": True,
                "cli_tools_generation": True
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
    """Get recommendations from multiple AI agents in batch"""
    try:
        user_id = request.get('user_id')
        agent_types = request.get('agent_types', [])
        real_time_context = request.get('real_time_context', {})
        
        if not user_id or not agent_types:
            raise HTTPException(status_code=400, detail="user_id and agent_types are required")
        
        results = {}
        
        # Execute recommendations for each agent type
        for agent_type in agent_types:
            try:
                result = await enhanced_ai_service.get_enhanced_recommendations(
                    user_id=user_id,
                    agent_type=agent_type,
                    real_time_context=real_time_context
                )
                results[agent_type] = result
            except Exception as e:
                results[agent_type] = {"error": str(e)}
        
        return {
            "success": True,
            "user_id": user_id,
            "batch_results": results,
            "total_agents": len(agent_types),
            "successful_agents": len([r for r in results.values() if "error" not in r]),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get batch recommendations: {str(e)}")


@router.get("/recommendation-history/{user_id}")
async def get_recommendation_history(
    user_id: int,
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get recommendation history for a user"""
    try:
        # This would typically query the database for historical recommendations
        # For now, return mock data
        mock_history = [
            {
                "id": 1,
                "agent_type": "growth_advisor",
                "recommendation": "Focus on trending hashtags for audience growth",
                "created_at": datetime.now().isoformat(),
                "status": "implemented"
            },
            {
                "id": 2,
                "agent_type": "content_advisor", 
                "recommendation": "Create carousel posts for better engagement",
                "created_at": datetime.now().isoformat(),
                "status": "pending"
            }
        ]
        
        # Filter by agent type if specified
        if agent_type:
            mock_history = [h for h in mock_history if h['agent_type'] == agent_type]
        
        # Apply limit
        mock_history = mock_history[:limit]
        
        return {
            "success": True,
            "user_id": user_id,
            "recommendation_history": mock_history,
            "total_recommendations": len(mock_history),
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendation history: {str(e)}")
