from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.db.session import get_db
from app.api.auth import get_current_user
from app.services.non_ai_strategy_service import NonAIStrategyService
from app.schemas.influencer_recommendation_summaries import GrowthStrategiesResponse

router = APIRouter()


@router.get("/influencer/{influencer_id}")
async def get_non_ai_growth_strategies(
    influencer_id: int,
    recommendation_id: Optional[int] = Query(None, description="Specific recommendation ID to use for generating strategies"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get growth strategies for a specific influencer using Non-AI approach.
    
    This endpoint generates growth strategies using rule-based templates instead of AI agents.
    It provides immediate results without requiring background processing.
    
    The strategies include:
    - More Followers strategies
    - Content Ideas
    - Social Media Profiles
    - Influencer Collaboration Ideas
    - Business Collaboration Ideas
    - Content Script Ideas
    """
    try:
        service = NonAIStrategyService()
        
        # Handle Query(None) default value
        actual_recommendation_id = None
        if recommendation_id is not None and hasattr(recommendation_id, '__class__') and recommendation_id.__class__.__name__ != 'Query':
            actual_recommendation_id = recommendation_id
        
        # Generate strategies using Non-AI approach (now includes file generation and saving)
        result = await service.generate_strategies(
            db=db,
            influencer_id=influencer_id,
            recommendation_id=actual_recommendation_id
        )
        
        # Extract data from the new response format
        strategies = result.get('strategies', {})
        download_links = result.get('download_links', [])
        summary_id = result.get('summary_id')
        
        return {
            "status": "completed",
            "data": {
                "more_followers": strategies.get('more_followers', []),
                "content_ideas": strategies.get('content_ideas', []),
                "social_profiles": strategies.get('social_profiles', []),
                "influencer_collab": strategies.get('influencer_collab', []),
                "business_collab": strategies.get('business_collab', []),
                "content_scripts": strategies.get('content_scripts', []),
                "download_links": download_links
            },
            "summary_id": summary_id,
            "message": "Non-AI growth strategies generated successfully with downloadable files",
            "method": "rule_based_templates"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing non-AI growth strategies request: {str(e)}")


@router.get("/influencer/{influencer_id}/status")
async def get_non_ai_processing_status(
    influencer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Check the processing status of non-AI growth strategies for an influencer.
    
    Since non-AI approach is immediate, this will always return completed status
    if strategies exist, or not_started if they don't.
    """
    try:
        from app.db.models.influencer_recommendation_summaries import InfluencerRecommendationSummaries
        from sqlalchemy import select
        
        # Check if strategies exist
        query = select(InfluencerRecommendationSummaries).where(
            InfluencerRecommendationSummaries.influencer_id == influencer_id
        ).order_by(InfluencerRecommendationSummaries.created_at.desc())
        
        result = await db.execute(query)
        existing_summary = result.scalar_one_or_none()
        
        if existing_summary:
            return {
                "status": "completed",
                "data": {
                    "more_followers": existing_summary.more_followers or [],
                    "content_ideas": existing_summary.content_ideas or [],
                    "social_profiles": existing_summary.social_profiles or [],
                    "influencer_collab": existing_summary.influencer_collab or [],
                    "business_collab": existing_summary.business_collab or [],
                    "content_scripts": existing_summary.content_scripts or []
                },
                "message": "Non-AI growth strategies are ready",
                "method": "rule_based_templates"
            }
        
        return {
            "status": "not_started",
            "data": None,
            "message": "No non-AI growth strategies found. Generate strategies by calling the main endpoint.",
            "method": "rule_based_templates"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking non-AI processing status: {str(e)}")
