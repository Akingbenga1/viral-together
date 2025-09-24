"""
Web Search API endpoints for testing DuckDuckGo functionality
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.core.dependencies import get_db
from app.services.web_search.web_search_factory import WebSearchFactory
from app.core.config import settings

router = APIRouter(prefix="/api/analytics/web-search", tags=["Web Search"])

# Initialize web search factory
web_search_factory = WebSearchFactory()


@router.get("/status")
async def get_web_search_status() -> Dict[str, Any]:
    """Get web search service status"""
    try:
        status = {
            "web_search_enabled": settings.WEB_SEARCH_ENABLED,
            "search_engine": settings.WEB_SEARCH_ENGINE,
            "api_key_configured": bool(settings.WEB_SEARCH_API_KEY),
            "engine_id_configured": bool(settings.WEB_SEARCH_ENGINE_ID),
            "timestamp": datetime.now().isoformat()
        }
        
        if settings.WEB_SEARCH_ENGINE == "duckduckgo":
            status["duckduckgo"] = {
                "status": "active",
                "rate_limit": "unlimited",
                "api_key_required": False
            }
        elif settings.WEB_SEARCH_ENGINE == "google":
            status["google"] = {
                "status": "active" if settings.WEB_SEARCH_API_KEY else "inactive",
                "rate_limit": "100/day",
                "api_key_required": True
            }
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get web search status: {str(e)}")


@router.get("/market-rates")
async def search_market_rates(
    platform: str = Query(..., description="Social media platform"),
    content_type: str = Query(..., description="Type of content (sponsored_post, story, reel, etc.)")
) -> Dict[str, Any]:
    """Search for market rates using web search"""
    try:
        if not settings.WEB_SEARCH_ENABLED:
            raise HTTPException(status_code=400, detail="Web search is disabled")
        
        # Create search service
        search_service = web_search_factory.create_search_service()
        
        # Construct search query
        query = f"{platform} influencer rates {content_type} 2024"
        
        async with search_service:
            results = await search_service.search(query, max_results=10)
        
        # Parse and structure results
        market_rates = []
        for result in results:
            market_rates.append({
                "platform": platform,
                "content_type": content_type,
                "rate_range": getattr(result, "rate_range", "N/A"),
                "source": getattr(result, "source", "N/A"),
                "url": getattr(result, "url", ""),
                "snippet": getattr(result, "snippet", ""),
                "timestamp": datetime.now().isoformat()
            })
        
        return {
            "query": query,
            "platform": platform,
            "content_type": content_type,
            "market_rates": market_rates,
            "total_results": len(market_rates),
            "search_engine": settings.WEB_SEARCH_ENGINE,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search market rates: {str(e)}")


@router.get("/trending-content")
async def search_trending_content(
    platform: str = Query(..., description="Social media platform"),
    category: Optional[str] = Query(None, description="Content category")
) -> Dict[str, Any]:
    """Search for trending content using web search"""
    try:
        if not settings.WEB_SEARCH_ENABLED:
            raise HTTPException(status_code=400, detail="Web search is disabled")
        
        # Create search service
        search_service = web_search_factory.create_search_service()
        
        # Construct search query
        if category:
            query = f"trending {category} {platform} 2024"
        else:
            query = f"trending content {platform} 2024"
        
        async with search_service:
            results = await search_service.search(query, max_results=15)
        
        # Parse and structure results
        trending_content = []
        for result in results:
            trending_content.append({
                "platform": platform,
                "category": category or "general",
                "hashtag": getattr(result, "hashtag", "N/A"),
                "trend_score": getattr(result, "trend_score", 0.0),
                "source": getattr(result, "source", "N/A"),
                "url": getattr(result, "url", ""),
                "snippet": getattr(result, "snippet", ""),
                "timestamp": datetime.now().isoformat()
            })
        
        return {
            "query": query,
            "platform": platform,
            "category": category,
            "trending_content": trending_content,
            "total_results": len(trending_content),
            "search_engine": settings.WEB_SEARCH_ENGINE,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search trending content: {str(e)}")


@router.post("/custom-search")
async def custom_search(
    request: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Perform custom web search"""
    try:
        if not settings.WEB_SEARCH_ENABLED:
            raise HTTPException(status_code=400, detail="Web search is disabled")
        
        query = request.get("query", "")
        max_results = request.get("max_results", 10)
        search_type = request.get("search_type", "general")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # Create search service
        search_service = web_search_factory.create_search_service()
        
        async with search_service:
            results = await search_service.search(query, max_results=max_results)
        
        # Structure results based on search type
        structured_results = []
        for result in results:
            structured_results.append({
                "title": getattr(result, "title", ""),
                "url": getattr(result, "url", ""),
                "snippet": getattr(result, "snippet", ""),
                "source": getattr(result, "source", "N/A"),
                "search_type": search_type,
                "timestamp": datetime.now().isoformat()
            })
        
        return {
            "query": query,
            "search_type": search_type,
            "results": structured_results,
            "total_results": len(structured_results),
            "search_engine": settings.WEB_SEARCH_ENGINE,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform custom search: {str(e)}")


@router.post("/batch-search")
async def batch_search(
    request: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Perform multiple web searches in batch"""
    try:
        if not settings.WEB_SEARCH_ENABLED:
            raise HTTPException(status_code=400, detail="Web search is disabled")
        
        queries = request.get("queries", [])
        if not queries:
            raise HTTPException(status_code=400, detail="Queries list is required")
        
        # Create search service
        search_service = web_search_factory.create_search_service()
        
        batch_results = []
        
        async with search_service:
            for query_data in queries:
                query = query_data.get("query", "")
                search_type = query_data.get("search_type", "general")
                
                if query:
                    results = await search_service.search(query, max_results=5)
                    
                    structured_results = []
                    for result in results:
                        structured_results.append({
                            "title": getattr(result, "title", ""),
                            "url": getattr(result, "url", ""),
                            "snippet": getattr(result, "snippet", ""),
                            "source": getattr(result, "source", "N/A"),
                            "search_type": search_type
                        })
                    
                    batch_results.append({
                        "query": query,
                        "search_type": search_type,
                        "results": structured_results,
                        "total_results": len(structured_results)
                    })
        
        return {
            "batch_results": batch_results,
            "total_queries": len(queries),
            "search_engine": settings.WEB_SEARCH_ENGINE,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform batch search: {str(e)}")


@router.get("/platform-analysis")
async def platform_analysis(
    platform: str = Query(..., description="Social media platform"),
    analysis_type: str = Query(..., description="Type of analysis (trends, rates, insights)")
) -> Dict[str, Any]:
    """Perform platform-specific analysis using web search"""
    try:
        if not settings.WEB_SEARCH_ENABLED:
            raise HTTPException(status_code=400, detail="Web search is disabled")
        
        # Create search service
        search_service = web_search_factory.create_search_service()
        
        # Construct analysis query based on type
        if analysis_type == "trends":
            query = f"{platform} trends 2024 social media"
        elif analysis_type == "rates":
            query = f"{platform} influencer rates 2024"
        elif analysis_type == "insights":
            query = f"{platform} social media insights 2024"
        else:
            query = f"{platform} social media analysis 2024"
        
        async with search_service:
            results = await search_service.search(query, max_results=10)
        
        # Structure analysis results
        analysis_results = []
        for result in results:
            analysis_results.append({
                "platform": platform,
                "analysis_type": analysis_type,
                "title": getattr(result, "title", ""),
                "url": getattr(result, "url", ""),
                "snippet": getattr(result, "snippet", ""),
                "source": getattr(result, "source", "N/A"),
                "timestamp": datetime.now().isoformat()
            })
        
        return {
            "platform": platform,
            "analysis_type": analysis_type,
            "query": query,
            "analysis_results": analysis_results,
            "total_results": len(analysis_results),
            "search_engine": settings.WEB_SEARCH_ENGINE,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform platform analysis: {str(e)}")


@router.get("/industry-analysis")
async def industry_analysis(
    industry: str = Query(..., description="Industry to analyze"),
    analysis_type: str = Query(..., description="Type of analysis (market_rates, trends, insights)")
) -> Dict[str, Any]:
    """Perform industry-specific analysis using web search"""
    try:
        if not settings.WEB_SEARCH_ENABLED:
            raise HTTPException(status_code=400, detail="Web search is disabled")
        
        # Create search service
        search_service = web_search_factory.create_search_service()
        
        # Construct industry analysis query
        if analysis_type == "market_rates":
            query = f"{industry} influencer marketing rates 2024"
        elif analysis_type == "trends":
            query = f"{industry} social media trends 2024"
        elif analysis_type == "insights":
            query = f"{industry} social media marketing insights 2024"
        else:
            query = f"{industry} social media analysis 2024"
        
        async with search_service:
            results = await search_service.search(query, max_results=10)
        
        # Structure industry analysis results
        industry_results = []
        for result in results:
            industry_results.append({
                "industry": industry,
                "analysis_type": analysis_type,
                "title": getattr(result, "title", ""),
                "url": getattr(result, "url", ""),
                "snippet": getattr(result, "snippet", ""),
                "source": getattr(result, "source", "N/A"),
                "timestamp": datetime.now().isoformat()
            })
        
        return {
            "industry": industry,
            "analysis_type": analysis_type,
            "query": query,
            "industry_results": industry_results,
            "total_results": len(industry_results),
            "search_engine": settings.WEB_SEARCH_ENGINE,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform industry analysis: {str(e)}")


@router.post("/competitor-research")
async def competitor_research(
    request: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Perform competitor research using web search"""
    try:
        if not settings.WEB_SEARCH_ENABLED:
            raise HTTPException(status_code=400, detail="Web search is disabled")
        
        competitors = request.get("competitors", [])
        platform = request.get("platform", "instagram")
        research_type = request.get("research_type", "engagement_analysis")
        
        if not competitors:
            raise HTTPException(status_code=400, detail="Competitors list is required")
        
        # Create search service
        search_service = web_search_factory.create_search_service()
        
        competitor_results = []
        
        async with search_service:
            for competitor in competitors:
                # Construct competitor research query
                query = f"{competitor} {platform} engagement analysis"
                
                results = await search_service.search(query, max_results=5)
                
                competitor_data = {
                    "competitor": competitor,
                    "platform": platform,
                    "research_type": research_type,
                    "results": []
                }
                
                for result in results:
                    competitor_data["results"].append({
                        "title": getattr(result, "title", ""),
                        "url": getattr(result, "url", ""),
                        "snippet": getattr(result, "snippet", ""),
                        "source": getattr(result, "source", "N/A"),
                        "timestamp": datetime.now().isoformat()
                    })
                
                competitor_results.append(competitor_data)
        
        return {
            "competitors": competitors,
            "platform": platform,
            "research_type": research_type,
            "competitor_results": competitor_results,
            "total_competitors": len(competitors),
            "search_engine": settings.WEB_SEARCH_ENGINE,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform competitor research: {str(e)}")


@router.get("/real-time-trends")
async def real_time_trends(
    platform: str = Query(..., description="Social media platform"),
    category: Optional[str] = Query(None, description="Content category")
) -> Dict[str, Any]:
    """Get real-time trends using web search"""
    try:
        if not settings.WEB_SEARCH_ENABLED:
            raise HTTPException(status_code=400, detail="Web search is disabled")
        
        # Create search service
        search_service = web_search_factory.create_search_service()
        
        # Construct real-time trends query
        if category:
            query = f"trending {category} {platform} today"
        else:
            query = f"trending {platform} today"
        
        async with search_service:
            results = await search_service.search(query, max_results=15)
        
        # Structure real-time trends
        trends = []
        for result in results:
            trends.append({
                "platform": platform,
                "category": category or "general",
                "trend": getattr(result, "trend", "N/A"),
                "hashtag": getattr(result, "hashtag", "N/A"),
                "trend_score": getattr(result, "trend_score", 0.0),
                "source": getattr(result, "source", "N/A"),
                "url": getattr(result, "url", ""),
                "snippet": getattr(result, "snippet", ""),
                "timestamp": datetime.now().isoformat()
            })
        
        return {
            "platform": platform,
            "category": category,
            "query": query,
            "trends": trends,
            "total_trends": len(trends),
            "search_engine": settings.WEB_SEARCH_ENGINE,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get real-time trends: {str(e)}")


@router.get("/performance-metrics")
async def get_performance_metrics() -> Dict[str, Any]:
    """Get web search performance metrics"""
    try:
        metrics = {
            "web_search_enabled": settings.WEB_SEARCH_ENABLED,
            "search_engine": settings.WEB_SEARCH_ENGINE,
            "api_key_configured": bool(settings.WEB_SEARCH_API_KEY),
            "engine_id_configured": bool(settings.WEB_SEARCH_ENGINE_ID),
            "rate_limits": {
                "duckduckgo": "unlimited",
                "google": "100/day",
                "bing": "1000/month"
            },
            "supported_engines": ["duckduckgo", "google", "bing"],
            "current_engine_status": "active" if settings.WEB_SEARCH_ENABLED else "disabled",
            "timestamp": datetime.now().isoformat()
        }
        
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")
