from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.dependencies import get_db, get_current_user, get_location_search_service
from app.services.location.location_search_service import LocationSearchService

router = APIRouter()

@router.get("/influencers/nearby")
async def find_influencers_nearby(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(50, ge=1, le=500),
    category: Optional[str] = Query(None),
    min_followers: Optional[int] = Query(None, ge=0),
    max_rate: Optional[float] = Query(None, ge=0),
    db: Session = Depends(get_db),
    search_service: LocationSearchService = Depends(get_location_search_service)
):
    """Find influencers within specified radius"""
    try:
        return await search_service.find_influencers_nearby(
            db, latitude, longitude, radius_km, category, min_followers, max_rate
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/businesses/nearby")
async def find_businesses_nearby(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(50, ge=1, le=500),
    industry: Optional[str] = Query(None),
    verified_only: bool = Query(False),
    db: Session = Depends(get_db),
    search_service: LocationSearchService = Depends(get_location_search_service)
):
    """Find businesses within specified radius"""
    try:
        return await search_service.find_businesses_nearby(
            db, latitude, longitude, radius_km, industry, verified_only
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/promotions/nearby")
async def find_promotions_nearby(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(100, ge=1, le=1000),
    min_budget: Optional[float] = Query(None, ge=0),
    max_budget: Optional[float] = Query(None, ge=0),
    db: Session = Depends(get_db),
    search_service: LocationSearchService = Depends(get_location_search_service)
):
    """Find promotion requests within specified radius"""
    try:
        return await search_service.find_promotion_requests_nearby(
            db, latitude, longitude, radius_km, min_budget, max_budget
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
