"""
API endpoint for finding businesses near influencer locations
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.dependencies import get_db, get_current_user
from app.services.nearby_business_search_service import NearbyBusinessSearchService
from app.services.mcp_client import MCPClient
from app.schemas.nearby_business_search import (
    NearbyBusinessSearchResult,
    NearbyBusinessSearchRequest
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def get_nearby_business_service() -> NearbyBusinessSearchService:
    """Dependency to get the nearby business search service"""
    mcp_client = MCPClient()
    return NearbyBusinessSearchService(mcp_client=mcp_client)


@router.get("/influencers/{influencer_id}/businesses-nearby")
async def get_businesses_nearby(
    influencer_id: int,
    radius_km: float = Query(50, ge=1, le=500, description="Search radius in kilometers"),
    industry_filter: Optional[str] = Query(None, description="Filter by industry/category"),
    verified_only: bool = Query(False, description="Only show verified businesses from our database"),
    include_external: bool = Query(True, description="Include external businesses from MCP search"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
    search_service: NearbyBusinessSearchService = Depends(get_nearby_business_service)
) -> NearbyBusinessSearchResult:
    """
    Find businesses near an influencer's location.
    
    This endpoint:
    1. Gets the influencer's primary operational location
    2. Searches our database for businesses within radius
    3. Optionally uses MCP DuckDuckGo search to find external businesses
    4. Returns combined results
    
    **Authentication**: Required
    
    **Parameters**:
    - `influencer_id`: ID of the influencer
    - `radius_km`: Search radius in kilometers (1-500)
    - `industry_filter`: Optional industry/category filter
    - `verified_only`: Only return verified businesses from our database
    - `include_external`: Include external businesses via MCP search
    
    **Returns**:
    - Combined results from database and external search
    - Includes business details, locations, and distances
    """
    try:
        # Create search request
        request = NearbyBusinessSearchRequest(
            influencer_id=influencer_id,
            radius_km=radius_km,
            industry_filter=industry_filter,
            verified_only=verified_only,
            include_external=include_external
        )
        
        # Perform search
        result = await search_service.find_businesses_near_influencer(db, request)
        
        logger.info(
            f"Found {result.total_results} businesses near influencer {influencer_id}: "
            f"{result.db_count} from DB, {result.external_count} external"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error finding businesses near influencer {influencer_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to find businesses: {str(e)}"
        )

