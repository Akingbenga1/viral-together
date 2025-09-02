from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db.models.location import LocationPromotionRequest
from app.db.models.business import Business
from app.db.models.promotions import Promotion
from app.schemas.location_promotion import *
from app.core.exceptions import AuthorizationError, NotFoundError
from fastapi import HTTPException

class LocationPromotionService:
    """Single responsibility: Handle location-based promotion requests"""
    
    async def create_location_promotion_request(
        self, 
        db: Session, 
        request: LocationPromotionRequestCreate,
        current_user
    ) -> LocationPromotionRequest:
        """Create a new location promotion request"""
        
        # Verify business ownership
        business = db.query(Business).filter(
            and_(
                Business.id == request.business_id,
                Business.owner_id == current_user.id
            )
        ).first()
        
        if not business:
            raise AuthorizationError("Not authorized to create requests for this business")
        
        # Verify promotion ownership
        promotion = db.query(Promotion).filter(
            and_(
                Promotion.id == request.promotion_id,
                Promotion.business_id == request.business_id
            )
        ).first()
        
        if not promotion:
            raise NotFoundError("Promotion not found")
        
        # Create location request
        request_data = request.dict(exclude={'business_id', 'promotion_id'})
        db_request = LocationPromotionRequest(
            business_id=request.business_id,
            promotion_id=request.promotion_id,
            **request_data
        )
        
        db.add(db_request)
        db.commit()
        db.refresh(db_request)
        
        return db_request
    
    async def get_location_promotion_requests(
        self, 
        db: Session, 
        business_id: Optional[int] = None,
        promotion_id: Optional[int] = None,
        country_id: Optional[int] = None,
        city: Optional[str] = None,
        current_user = None
    ) -> List[LocationPromotionRequestWithDetails]:
        """Get location promotion requests with optional filters"""
        
        query = db.query(LocationPromotionRequest)
        
        # Apply filters
        if business_id:
            query = query.filter(LocationPromotionRequest.business_id == business_id)
        
        if promotion_id:
            query = query.filter(LocationPromotionRequest.promotion_id == promotion_id)
        
        if country_id:
            query = query.filter(LocationPromotionRequest.country_id == country_id)
        
        if city:
            query = query.filter(LocationPromotionRequest.city.ilike(f"%{city}%"))
        
        requests = query.all()
        
        # Convert to response format with details
        result = []
        for request in requests:
            request_dict = {k: v for k, v in request.__dict__.items() if not k.startswith('_')}
            details = LocationPromotionRequestWithDetails(
                **request_dict,
                business_name=request.business.name if request.business else None,
                promotion_title=request.promotion.promotion_name if request.promotion else None,
                country_name=request.country.name if request.country else None
            )
            result.append(details)
        
        return result
    
    async def update_location_promotion_request(
        self, 
        db: Session, 
        request_id: int, 
        request: LocationPromotionRequestUpdate, 
        current_user
    ) -> LocationPromotionRequest:
        """Update a location promotion request"""
        
        db_request = db.query(LocationPromotionRequest).filter(
            LocationPromotionRequest.id == request_id
        ).first()
        
        if not db_request:
            raise NotFoundError("Location promotion request not found")
        
        # Verify ownership
        business = db.query(Business).filter(
            and_(
                Business.id == db_request.business_id,
                Business.owner_id == current_user.id
            )
        ).first()
        
        if not business:
            raise AuthorizationError("Not authorized to update this request")
        
        # Update fields
        for field, value in request.dict(exclude_unset=True).items():
            if hasattr(db_request, field):
                setattr(db_request, field, value)
        
        db.commit()
        db.refresh(db_request)
        
        return db_request
    
    async def delete_location_promotion_request(
        self, 
        db: Session, 
        request_id: int, 
        current_user
    ) -> bool:
        """Delete a location promotion request"""
        
        db_request = db.query(LocationPromotionRequest).filter(
            LocationPromotionRequest.id == request_id
        ).first()
        
        if not db_request:
            raise NotFoundError("Location promotion request not found")
        
        # Verify ownership
        business = db.query(Business).filter(
            and_(
                Business.id == db_request.business_id,
                Business.owner_id == current_user.id
            )
        ).first()
        
        if not business:
            raise AuthorizationError("Not authorized to delete this request")
        
        db.delete(db_request)
        db.commit()
        
        return True
