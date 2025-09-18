"""
Influencer marketing API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.core.dependencies import get_db
from app.services.influencer_marketing.influencer_marketing_service import InfluencerMarketingService

router = APIRouter(prefix="/api/influencer-marketing", tags=["Influencer Marketing"])

# Initialize service
influencer_service = InfluencerMarketingService()


@router.get("/brand-opportunities/{user_id}")
async def get_brand_partnership_opportunities(
    user_id: int,
    limit: int = Query(20, ge=1, le=50, description="Maximum number of opportunities"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get brand partnership opportunities for a user"""
    try:
        opportunities = await influencer_service.get_brand_partnership_opportunities(user_id)
        
        # Apply limit
        opportunities = opportunities[:limit]
        
        return {
            "user_id": user_id,
            "brand_opportunities": opportunities,
            "summary": {
                "total_opportunities": len(opportunities),
                "high_relevance_count": len([o for o in opportunities if o.get('relevance_score', 0) > 0.7]),
                "paid_opportunities": len([o for o in opportunities if 'paid' in o.get('compensation_range', '').lower()]),
                "last_updated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get brand opportunities: {str(e)}")


@router.get("/content-recommendations/{user_id}")
async def get_content_recommendations(
    user_id: int,
    platform: str = Query("instagram", description="Social media platform"),
    limit: int = Query(15, ge=1, le=30, description="Maximum number of recommendations"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get content recommendations based on trends"""
    try:
        recommendations = await influencer_service.get_content_recommendations(user_id, platform)
        
        # Apply limit
        recommendations = recommendations[:limit]
        
        return {
            "user_id": user_id,
            "platform": platform,
            "content_recommendations": recommendations,
            "summary": {
                "total_recommendations": len(recommendations),
                "average_trend_score": sum(r.get('trend_score', 0) for r in recommendations) / len(recommendations) if recommendations else 0,
                "high_trend_count": len([r for r in recommendations if r.get('trend_score', 0) > 0.8]),
                "last_updated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get content recommendations: {str(e)}")


@router.get("/pricing-recommendations/{user_id}")
async def get_pricing_recommendations(
    user_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get pricing recommendations based on market analysis"""
    try:
        recommendations = await influencer_service.get_pricing_recommendations(user_id)
        
        if not recommendations:
            raise HTTPException(status_code=404, detail="No pricing recommendations found for user")
        
        return {
            "user_id": user_id,
            "pricing_recommendations": recommendations,
            "last_updated": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pricing recommendations: {str(e)}")


@router.get("/growth-strategies/{user_id}")
async def get_growth_strategies(
    user_id: int,
    limit: int = Query(10, ge=1, le=20, description="Maximum number of strategies"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get growth strategies based on current trends"""
    try:
        strategies = await influencer_service.get_growth_strategies(user_id)
        
        # Apply limit
        strategies = strategies[:limit]
        
        return {
            "user_id": user_id,
            "growth_strategies": strategies,
            "summary": {
                "total_strategies": len(strategies),
                "high_priority_count": len([s for s in strategies if s.get('priority') == 'high']),
                "quick_implement_count": len([s for s in strategies if '1-2 weeks' in s.get('time_to_implement', '')]),
                "last_updated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get growth strategies: {str(e)}")


@router.get("/marketing-insights/{user_id}")
async def get_marketing_insights(
    user_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get comprehensive marketing insights for a user"""
    try:
        # Gather all marketing data
        brand_opportunities = await influencer_service.get_brand_partnership_opportunities(user_id)
        content_recommendations = await influencer_service.get_content_recommendations(user_id, "instagram")
        pricing_recommendations = await influencer_service.get_pricing_recommendations(user_id)
        growth_strategies = await influencer_service.get_growth_strategies(user_id)
        live_metrics = await influencer_service.get_live_metrics(user_id)
        
        return {
            "user_id": user_id,
            "marketing_insights": {
                "brand_opportunities": {
                    "total": len(brand_opportunities),
                    "high_relevance": len([o for o in brand_opportunities if o.get('relevance_score', 0) > 0.7]),
                    "top_opportunities": brand_opportunities[:5]
                },
                "content_recommendations": {
                    "total": len(content_recommendations),
                    "high_trend": len([r for r in content_recommendations if r.get('trend_score', 0) > 0.8]),
                    "top_recommendations": content_recommendations[:5]
                },
                "pricing_insights": {
                    "current_metrics": pricing_recommendations.get('current_metrics', {}),
                    "market_analysis": pricing_recommendations.get('market_analysis', {}),
                    "recommended_rates": pricing_recommendations.get('recommended_rates', {})
                },
                "growth_strategies": {
                    "total": len(growth_strategies),
                    "high_priority": len([s for s in growth_strategies if s.get('priority') == 'high']),
                    "top_strategies": growth_strategies[:3]
                },
                "live_metrics": live_metrics
            },
            "summary": {
                "data_freshness": "real-time",
                "insights_generated": datetime.now().isoformat(),
                "recommendation_priority": "high" if len(brand_opportunities) > 5 else "medium"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get marketing insights: {str(e)}")


@router.get("/trending-hashtags")
async def get_trending_hashtags(
    platform: str = Query(..., description="Social media platform"),
    category: Optional[str] = Query(None, description="Content category filter"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of hashtags"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get trending hashtags for a platform"""
    try:
        trending_topics = await influencer_service.get_trending_topics(platform)
        
        # Apply limit
        trending_topics = trending_topics[:limit]
        
        return {
            "platform": platform,
            "category": category,
            "trending_hashtags": trending_topics,
            "summary": {
                "total_hashtags": len(trending_topics),
                "last_updated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trending hashtags: {str(e)}")


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


@router.get("/opportunity-alerts/{user_id}")
async def get_opportunity_alerts(
    user_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get opportunity alerts for a user"""
    try:
        # Get brand opportunities
        brand_opportunities = await influencer_service.get_brand_partnership_opportunities(user_id)
        
        # Get trending content
        trending_content = []
        for platform in ['instagram', 'tiktok', 'twitter']:
            topics = await influencer_service.get_trending_topics(platform)
            trending_content.extend([{'platform': platform, 'hashtag': topic} for topic in topics[:5]])
        
        # Generate alerts
        alerts = []
        
        # High relevance brand opportunities
        high_relevance_opportunities = [o for o in brand_opportunities if o.get('relevance_score', 0) > 0.8]
        if high_relevance_opportunities:
            alerts.append({
                "type": "brand_opportunity",
                "priority": "high",
                "message": f"{len(high_relevance_opportunities)} high-relevance brand opportunities found",
                "count": len(high_relevance_opportunities),
                "timestamp": datetime.now().isoformat()
            })
        
        # Trending hashtags in user's niche
        if trending_content:
            alerts.append({
                "type": "trending_content",
                "priority": "medium",
                "message": f"{len(trending_content)} trending hashtags available for content creation",
                "count": len(trending_content),
                "timestamp": datetime.now().isoformat()
            })
        
        return {
            "user_id": user_id,
            "alerts": alerts,
            "summary": {
                "total_alerts": len(alerts),
                "high_priority_alerts": len([a for a in alerts if a.get('priority') == 'high']),
                "last_updated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get opportunity alerts: {str(e)}")
