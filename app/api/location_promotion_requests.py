from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.dependencies import get_db, get_current_user, get_location_search_service, get_location_promotion_service
from app.schemas.location_promotion import *
from app.services.location.location_promotion_service import LocationPromotionService
from app.core.exceptions import AuthorizationError, NotFoundError

router = APIRouter()

@router.post("/location-promotion-requests", response_model=LocationPromotionRequest)
async def create_location_promotion_request(
    request: LocationPromotionRequestCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    service: LocationPromotionService = Depends(get_location_promotion_service)
):
    """Create a new location-based promotion request"""
    try:
        return await service.create_location_promotion_request(db, request, current_user)
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/location-promotion-requests", response_model=List[LocationPromotionRequestWithDetails])
async def get_location_promotion_requests(
    business_id: Optional[int] = Query(None),
    promotion_id: Optional[int] = Query(None),
    country_id: Optional[int] = Query(None),
    city: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    service: LocationPromotionService = Depends(get_location_promotion_service)
):
    """Get location promotion requests with optional filters"""
    try:
        return await service.get_location_promotion_requests(
            db, business_id, promotion_id, country_id, city, current_user
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/location-promotion-requests/nearby", response_model=List[LocationPromotionRequestWithDetails])
async def find_promotions_nearby(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    search_service = Depends(get_location_search_service)
):
    """Find promotion requests within specified radius"""
    try:
        return await search_service.find_promotion_requests_nearby(db, latitude, longitude, radius_km)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/location-promotion-requests/{request_id}", response_model=LocationPromotionRequest)
async def update_location_promotion_request(
    request_id: int,
    request: LocationPromotionRequestUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    service: LocationPromotionService = Depends(get_location_promotion_service)
):
    """Update a location promotion request"""
    try:
        return await service.update_location_promotion_request(db, request_id, request, current_user)
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/location-promotion-requests/{request_id}")
async def delete_location_promotion_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    service: LocationPromotionService = Depends(get_location_promotion_service)
):
    """Delete a location promotion request"""
    try:
        await service.delete_location_promotion_request(db, request_id, current_user)
        return {"message": "Location promotion request deleted successfully"}
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
