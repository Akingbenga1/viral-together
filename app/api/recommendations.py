from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.dependencies import get_db, get_current_user
from app.db.models.influencer_recommendations import InfluencerRecommendations
from app.schemas.influencer_recommendations import (
    InfluencerRecommendations as InfluencerRecommendationsSchema,
    InfluencerRecommendationsCreate,
    InfluencerRecommendationsUpdate
)
from app.services.cron_scheduler import CronJobScheduler
from app.services.user_profile_analyzer import UserProfileAnalyzer
from app.services.ai_agent_orchestrator import AIAgentOrchestrator
from app.services.influencer_plan_recommender import InfluencerPlanRecommender

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.post("/generate/{user_id}", response_model=InfluencerRecommendationsSchema)
async def generate_recommendations(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Generate AI recommendations for a specific user"""
    try:
        # Initialize services
        scheduler = CronJobScheduler()
        profile_analyzer = UserProfileAnalyzer()
        ai_orchestrator = AIAgentOrchestrator()
        plan_recommender = InfluencerPlanRecommender()
        
        # Get comprehensive user profile
        user_profile = await scheduler.get_comprehensive_user_profile(user_id)
        
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        # Analyze user profile
        analysis_result = profile_analyzer.analyze_user_profile(user_profile)
        
        # Get AI agent recommendations
        ai_recommendations = await ai_orchestrator.get_agent_recommendations(
            user_profile=user_profile,
            analysis_result=analysis_result,
            db_session=db
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
        db.add(recommendation)
        await db.commit()
        await db.refresh(recommendation)
        
        return recommendation
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {str(e)}"
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
    recommendation = result.scalar_one_or_none()
    
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found"
        )
    
    return recommendation

@router.put("/{recommendation_id}", response_model=InfluencerRecommendationsSchema)
async def update_recommendation(
    recommendation_id: int,
    recommendation_update: InfluencerRecommendationsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a recommendation"""
    query = select(InfluencerRecommendations).where(
        InfluencerRecommendations.id == recommendation_id
    )
    
    result = await db.execute(query)
    recommendation = result.scalar_one_or_none()
    
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
    recommendation = result.scalar_one_or_none()
    
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found"
        )
    
    await db.delete(recommendation)
    await db.commit()
    
    return {"message": "Recommendation deleted successfully"}

@router.post("/trigger-analysis/{user_id}")
async def trigger_analysis(
    user_id: int,
    current_user = Depends(get_current_user)
):
    """Manually trigger analysis for a specific user"""
    try:
        scheduler = CronJobScheduler()
        await scheduler.run_user_analysis_job()
        
        return {
            "message": f"Analysis triggered for user {user_id}",
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error triggering analysis: {str(e)}"
        )
