"""
Real-time analytics API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.core.dependencies import get_db
from app.services.analytics.real_time_analytics import RealTimeAnalyticsService
from app.services.influencer_marketing.influencer_marketing_service import InfluencerMarketingService
from app.core.interfaces import SocialMediaMetrics, MarketRate, CompetitorAnalysis, TrendingContent

router = APIRouter(prefix="/api/analytics", tags=["Real-time Analytics"])

# Initialize services
analytics_service = RealTimeAnalyticsService()
influencer_service = InfluencerMarketingService()


@router.get("/engagement-trends/{user_id}")
async def get_engagement_trends(
    user_id: int,
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get engagement trends for a user"""
    try:
        trends = await analytics_service.get_engagement_trends(user_id, days)
        
        return {
            "user_id": user_id,
            "days_analyzed": days,
            "engagement_trends": [
                {
                    "platform": trend.platform,
                    "followers": trend.followers,
                    "engagement_rate": trend.engagement_rate,
                    "reach": trend.reach,
                    "impressions": trend.impressions,
                    "likes": trend.likes,
                    "comments": trend.comments,
                    "shares": trend.shares,
                    "timestamp": trend.timestamp.isoformat()
                }
                for trend in trends
            ],
            "summary": {
                "total_platforms": len(trends),
                "average_engagement_rate": sum(t.engagement_rate for t in trends) / len(trends) if trends else 0,
                "total_followers": sum(t.followers for t in trends),
                "last_updated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get engagement trends: {str(e)}")


@router.get("/market-rates")
async def get_market_rates(
    platform: str = Query(..., description="Social media platform"),
    content_type: str = Query("sponsored_post", description="Type of content"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get current market rates for content"""
    try:
        rates = await analytics_service.get_market_rates(platform, content_type)
        
        return {
            "platform": platform,
            "content_type": content_type,
            "market_rates": [
                {
                    "platform": rate.platform,
                    "content_type": rate.content_type,
                    "follower_range": rate.follower_range,
                    "rate_range": rate.rate_range,
                    "engagement_threshold": rate.engagement_threshold,
                    "timestamp": rate.timestamp.isoformat()
                }
                for rate in rates
            ],
            "summary": {
                "total_rates": len(rates),
                "average_min_rate": sum(r.rate_range["min"] for r in rates) / len(rates) if rates else 0,
                "average_max_rate": sum(r.rate_range["max"] for r in rates) / len(rates) if rates else 0,
                "last_updated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market rates: {str(e)}")


@router.get("/competitor-analysis/{user_id}")
async def get_competitor_analysis(
    user_id: int,
    competitors: List[str] = Query(..., description="List of competitor usernames"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get competitor analysis"""
    try:
        analysis = await analytics_service.get_competitor_analysis(user_id, competitors)
        
        return {
            "user_id": user_id,
            "competitors_analyzed": competitors,
            "competitor_analysis": [
                {
                    "competitor_name": comp.competitor_name,
                    "platform": comp.platform,
                    "followers": comp.followers,
                    "engagement_rate": comp.engagement_rate,
                    "content_frequency": comp.content_frequency,
                    "top_performing_content": comp.top_performing_content,
                    "growth_rate": comp.growth_rate,
                    "timestamp": comp.timestamp.isoformat()
                }
                for comp in analysis
            ],
            "summary": {
                "total_competitors": len(analysis),
                "average_engagement_rate": sum(c.engagement_rate for c in analysis) / len(analysis) if analysis else 0,
                "average_followers": sum(c.followers for c in analysis) / len(analysis) if analysis else 0,
                "last_updated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get competitor analysis: {str(e)}")


@router.get("/trending-content")
async def get_trending_content(
    platform: str = Query(..., description="Social media platform"),
    category: Optional[str] = Query(None, description="Content category filter"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of results"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get trending content for a platform"""
    try:
        trending = await analytics_service.get_trending_content(platform, category)
        
        # Apply limit
        trending = trending[:limit]
        
        return {
            "platform": platform,
            "category": category,
            "trending_content": [
                {
                    "platform": content.platform,
                    "hashtag": content.hashtag,
                    "post_count": content.post_count,
                    "engagement_rate": content.engagement_rate,
                    "trend_score": content.trend_score,
                    "category": content.category,
                    "timestamp": content.timestamp.isoformat()
                }
                for content in trending
            ],
            "summary": {
                "total_trends": len(trending),
                "average_engagement_rate": sum(t.engagement_rate for t in trending) / len(trending) if trending else 0,
                "average_trend_score": sum(t.trend_score for t in trending) / len(trending) if trending else 0,
                "last_updated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trending content: {str(e)}")


@router.get("/live-metrics/{user_id}")
async def get_live_metrics(
    user_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get live metrics for a user"""
    try:
        metrics = await influencer_service.get_live_metrics(user_id)
        
        if not metrics:
            raise HTTPException(status_code=404, detail="No live metrics found for user")
        
        return {
            "user_id": user_id,
            "live_metrics": metrics,
            "last_updated": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get live metrics: {str(e)}")


@router.get("/trending-topics")
async def get_trending_topics(
    platform: str = Query(..., description="Social media platform"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get trending topics for a platform"""
    try:
        topics = await influencer_service.get_trending_topics(platform)
        
        return {
            "platform": platform,
            "trending_topics": topics,
            "total_topics": len(topics),
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trending topics: {str(e)}")


@router.get("/market-insights")
async def get_market_insights(
    industry: str = Query(..., description="Industry to analyze"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get market insights for an industry"""
    try:
        insights = await influencer_service.get_market_insights(industry)
        
        return {
            "industry": industry,
            "market_insights": insights,
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market insights: {str(e)}")


@router.get("/analytics-summary/{user_id}")
async def get_analytics_summary(
    user_id: int,
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get comprehensive analytics summary for a user"""
    try:
        # Gather all analytics data
        engagement_trends = await analytics_service.get_engagement_trends(user_id, days)
        live_metrics = await influencer_service.get_live_metrics(user_id)
        
        # Calculate summary statistics
        total_followers = sum(trend.followers for trend in engagement_trends)
        average_engagement = sum(trend.engagement_rate for trend in engagement_trends) / len(engagement_trends) if engagement_trends else 0
        
        return {
            "user_id": user_id,
            "analysis_period_days": days,
            "summary": {
                "total_followers": total_followers,
                "average_engagement_rate": average_engagement,
                "platforms_analyzed": len(engagement_trends),
                "data_freshness": "real-time"
            },
            "engagement_trends": [
                {
                    "platform": trend.platform,
                    "followers": trend.followers,
                    "engagement_rate": trend.engagement_rate,
                    "timestamp": trend.timestamp.isoformat()
                }
                for trend in engagement_trends
            ],
            "live_metrics": live_metrics,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics summary: {str(e)}")
