from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.db.session import get_db
from app.api.auth import get_current_user
from app.services.growth_strategies_service import GrowthStrategiesService
from app.schemas.influencer_recommendation_summaries import GrowthStrategiesResponse

router = APIRouter()


@router.get("/influencer/{influencer_id}")
async def get_growth_strategies(
    influencer_id: int,
    recommendation_id: Optional[int] = Query(None, description="Specific recommendation ID to use for generating strategies"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get growth strategies for a specific influencer.
    
    This endpoint retrieves growth strategies from the database. If strategies don't exist,
    it will queue a background task to generate them and return a processing status.
    
    The strategies include:
    - More Followers strategies
    - Content Ideas
    - Social Media Profiles
    - Influencer Collaboration Ideas
    - Business Collaboration Ideas
    - Content Script Ideas
    """
    try:
        service = GrowthStrategiesService()
        
        # Handle Query(None) default value
        actual_recommendation_id = None
        if recommendation_id is not None and hasattr(recommendation_id, '__class__') and recommendation_id.__class__.__name__ != 'Query':
            actual_recommendation_id = recommendation_id
        
        # First, check if strategies already exist in database
        existing_strategies = await service.get_existing_strategies(
            db=db,
            influencer_id=influencer_id,
            recommendation_id=actual_recommendation_id
        )
        
        if existing_strategies:
            # Return existing strategies immediately
            return {
                "status": "completed",
                "data": existing_strategies,
                "message": "Growth strategies retrieved successfully"
            }
        
        # Check if processing is already in progress
        is_processing = await service.is_processing_in_progress(db, influencer_id)
        
        if is_processing:
            return {
                "status": "processing",
                "data": None,
                "message": "Growth strategies are currently being generated. Please check back in a few minutes."
            }
        
        # No existing strategies and not processing - check data availability first
        data_check = await service.check_data_availability(db, influencer_id, recommendation_id)
        
        if not data_check['available']:
            return {
                "status": "error",
                "data": None,
                "error_type": data_check['error'],
                "message": data_check['message'],
                "suggestion": data_check.get('suggestion', 'Please try again later.'),
                "details": data_check
            }
        
        # Data is available - queue background task
        from app.tasks.growth_strategies_tasks import generate_growth_strategies_task
        
        # Queue the background task
        task = generate_growth_strategies_task.delay(
            influencer_id=influencer_id,
            recommendation_id=data_check.get('recommendation_id', recommendation_id)
        )
        
        return {
            "status": "processing",
            "task_id": task.id,
            "data": None,
            "message": "AI agents are generating your growth strategies. This may take a few minutes."
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing growth strategies request: {str(e)}")


@router.get("/influencer/{influencer_id}/status")
async def get_processing_status(
    influencer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Check the processing status of growth strategies for an influencer.
    
    Returns the current status and any available data.
    """
    try:
        service = GrowthStrategiesService()
        
        # Check if strategies exist
        existing_strategies = await service.get_existing_strategies(
            db=db,
            influencer_id=influencer_id,
            recommendation_id=None
        )
        
        if existing_strategies:
            return {
                "status": "completed",
                "data": existing_strategies,
                "message": "Growth strategies are ready"
            }
        
        # Check if processing is in progress
        is_processing = await service.is_processing_in_progress(db, influencer_id)
        
        if is_processing:
            return {
                "status": "processing",
                "data": None,
                "message": "Growth strategies are being generated"
            }
        
        return {
            "status": "not_started",
            "data": None,
            "message": "No growth strategies found. Start processing by calling the main endpoint."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking processing status: {str(e)}")


@router.get("/growth-strategies/recommendation/{recommendation_id}", response_model=GrowthStrategiesResponse)
async def get_growth_strategies_by_recommendation(
    recommendation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get growth strategies for a specific recommendation ID.
    
    This endpoint generates or retrieves growth strategies based on a specific
    recommendation's data.
    """
    try:
        service = GrowthStrategiesService()
        strategies = await service.get_or_create_growth_strategies(
            db=db,
            influencer_id=None,  # Will be determined from recommendation
            recommendation_id=recommendation_id
        )
        
        return GrowthStrategiesResponse(**strategies)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating growth strategies: {str(e)}")
