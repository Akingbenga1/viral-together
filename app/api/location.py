from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.dependencies import get_db, get_current_user, get_geocoding_service, get_influencer_location_service, get_business_location_service
from app.services.location.influencer_location_service import InfluencerLocationService
from app.services.location.business_location_service import BusinessLocationService
from app.services.geocoding.geocoding_service_factory import GeocodingServiceFactory
from app.schemas.location import *
from app.core.exceptions import AuthorizationError, NotFoundError, DuplicateLocationError

router = APIRouter()

@router.post("/geocode", response_model=dict)
async def geocode_address(
    request: GeocodeRequest,
    geocoding_service = Depends(get_geocoding_service)
):
    """Convert address to coordinates"""
    result = await geocoding_service.geocode_address(request.address, request.country_code)
    if not result:
        raise HTTPException(status_code=404, detail="Address not found")
    return result

@router.post("/reverse-geocode", response_model=dict)
async def reverse_geocode(
    request: ReverseGeocodeRequest,
    geocoding_service = Depends(get_geocoding_service)
):
    """Convert coordinates to address"""
    result = await geocoding_service.reverse_geocode(float(request.latitude), float(request.longitude))
    if not result:
        raise HTTPException(status_code=404, detail="Location not found")
    return result

@router.get("/search", response_model=List[LocationSearchResult])
async def search_locations(
    query: str = Query(..., min_length=1),
    country_code: Optional[str] = Query(None, min_length=2, max_length=2),
    limit: int = Query(10, ge=1, le=50),
    geocoding_service = Depends(get_geocoding_service)
):
    """Search locations by name/city"""
    results = await geocoding_service.search_locations(query, limit)
    return results

@router.post("/influencers/{influencer_id}/locations", response_model=InfluencerLocation)
async def add_influencer_location(
    influencer_id: int,
    location: InfluencerLocationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    location_service: InfluencerLocationService = Depends(get_influencer_location_service)
):
    """Add operational location for influencer"""
    try:
        return await location_service.add_location(db, influencer_id, location, current_user)
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except DuplicateLocationError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/influencers/{influencer_id}/locations", response_model=List[InfluencerLocation])
async def get_influencer_locations(
    influencer_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    location_service: InfluencerLocationService = Depends(get_influencer_location_service)
):
    """Get all operational locations for influencer"""
    try:
        return await location_service.get_locations(db, influencer_id, current_user)
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/influencers/locations/{location_id}", response_model=InfluencerLocation)
async def update_influencer_location(
    location_id: int,
    location: InfluencerLocationUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    location_service: InfluencerLocationService = Depends(get_influencer_location_service)
):
    """Update influencer location"""
    try:
        return await location_service.update_location(db, location_id, location, current_user)
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DuplicateLocationError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/influencers/locations/{location_id}")
async def delete_influencer_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    location_service: InfluencerLocationService = Depends(get_influencer_location_service)
):
    """Delete influencer location"""
    try:
        await location_service.delete_location(db, location_id, current_user)
        return {"message": "Location deleted successfully"}
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/businesses/{business_id}/locations", response_model=BusinessLocation)
async def add_business_location(
    business_id: int,
    location: BusinessLocationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    location_service: BusinessLocationService = Depends(get_business_location_service)
):
    """Add operational location for business"""
    try:
        return await location_service.add_location(db, business_id, location, current_user)
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except DuplicateLocationError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/businesses/{business_id}/locations", response_model=List[BusinessLocation])
async def get_business_locations(
    business_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    location_service: BusinessLocationService = Depends(get_business_location_service)
):
    """Get all operational locations for business"""
    try:
        return await location_service.get_locations(db, business_id, current_user)
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/businesses/locations/{location_id}", response_model=BusinessLocation)
async def update_business_location(
    location_id: int,
    location: BusinessLocationUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    location_service: BusinessLocationService = Depends(get_business_location_service)
):
    """Update business location"""
    try:
        return await location_service.update_location(db, location_id, location, current_user)
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DuplicateLocationError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/businesses/locations/{location_id}")
async def delete_business_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    location_service: BusinessLocationService = Depends(get_business_location_service)
):
    """Delete business location"""
    try:
        await location_service.delete_location(db, location_id, current_user)
        return {"message": "Location deleted successfully"}
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
