from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from app.services.interfaces.location_service_interface import ILocationService
from app.db.models.location import BusinessOperationalLocation
from app.db.models.business import Business
from app.schemas.location import BusinessLocationCreate, BusinessLocationUpdate
from app.core.exceptions import AuthorizationError, NotFoundError, DuplicateLocationError

class BusinessLocationService(ILocationService):
    """Single responsibility: Handle business location operations"""
    
    async def add_location(
        self, 
        db: AsyncSession, 
        business_id: int, 
        location: BusinessLocationCreate, 
        current_user
    ) -> BusinessOperationalLocation:
        """Add operational location for business"""
        if not await self._verify_business_ownership(db, business_id, current_user.id):
            raise AuthorizationError("Not authorized to manage this business's locations")
        
        # Check for duplicate coordinates (same latitude/longitude for the same business)
        duplicate_check = await db.execute(
            select(BusinessOperationalLocation).where(
                and_(
                    BusinessOperationalLocation.business_id == business_id,
                    BusinessOperationalLocation.latitude == location.latitude,
                    BusinessOperationalLocation.longitude == location.longitude
                )
            )
        )
        
        if duplicate_check.scalars().first():
            raise DuplicateLocationError(
                f"Location with coordinates ({location.latitude}, {location.longitude}) already exists for this business. "
                f"Each business can only have one location per set of coordinates."
            )
        
        # Check if first location (make primary)
        result = await db.execute(
            select(BusinessOperationalLocation).where(
                BusinessOperationalLocation.business_id == business_id
            )
        )
        existing_count = len(result.scalars().all())
        
        if existing_count == 0:
            location.is_primary = True
        
        # Create location
        from datetime import datetime
        
        db_location = BusinessOperationalLocation(
            business_id=business_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            **location.model_dump()
        )
        
        db.add(db_location)
        await db.commit()
        await db.refresh(db_location)
        
        return db_location
    
    async def get_locations(
        self, 
        db: AsyncSession, 
        business_id: int,
        current_user
    ) -> List[BusinessOperationalLocation]:
        """Get all operational locations for business"""
        if not await self._verify_business_ownership(db, business_id, current_user.id):
            raise AuthorizationError("Not authorized to view this business's locations")
        
        result = await db.execute(
            select(BusinessOperationalLocation).where(
                BusinessOperationalLocation.business_id == business_id
            )
        )
        return result.scalars().all()
    
    async def update_location(
        self, 
        db: AsyncSession, 
        location_id: int, 
        location: BusinessLocationUpdate, 
        current_user
    ) -> BusinessOperationalLocation:
        """Update business location"""
        result = await db.execute(
            select(BusinessOperationalLocation).where(
                BusinessOperationalLocation.id == location_id
            )
        )
        db_location = result.scalars().first()
        
        if not db_location:
            raise NotFoundError("Location not found")
        
        if not await self._verify_business_ownership(db, db_location.business_id, current_user.id):
            raise AuthorizationError("Not authorized to update this location")
        
        # Check for duplicate coordinates when updating (excluding current location)
        if 'latitude' in location.model_dump(exclude_unset=True) or 'longitude' in location.model_dump(exclude_unset=True):
            new_lat = location.latitude if 'latitude' in location.model_dump(exclude_unset=True) else db_location.latitude
            new_lng = location.longitude if 'longitude' in location.model_dump(exclude_unset=True) else db_location.longitude
            
            duplicate_check = await db.execute(
                select(BusinessOperationalLocation).where(
                    and_(
                        BusinessOperationalLocation.business_id == db_location.business_id,
                        BusinessOperationalLocation.latitude == new_lat,
                        BusinessOperationalLocation.longitude == new_lng,
                        BusinessOperationalLocation.id != location_id  # Exclude current location
                    )
                )
            )
            
            if duplicate_check.scalars().first():
                raise DuplicateLocationError(
                    f"Location with coordinates ({new_lat}, {new_lng}) already exists for this business. "
                    f"Each business can only have one location per set of coordinates."
                )
        
        for field, value in location.model_dump(exclude_unset=True).items():
            setattr(db_location, field, value)
        
        # Update the updated_at timestamp
        from datetime import datetime
        db_location.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(db_location)
        return db_location
    
    async def delete_location(
        self, 
        db: AsyncSession, 
        location_id: int, 
        current_user
    ) -> bool:
        """Delete business location"""
        result = await db.execute(
            select(BusinessOperationalLocation).where(
                BusinessOperationalLocation.id == location_id
            )
        )
        db_location = result.scalars().first()
        
        if not db_location:
            raise NotFoundError("Location not found")
        
        if not await self._verify_business_ownership(db, db_location.business_id, current_user.id):
            raise AuthorizationError("Not authorized to delete this location")
        
        db.delete(db_location)
        await db.commit()
        return True
    
    async def _verify_business_ownership(self, db: AsyncSession, business_id: int, user_id: int) -> bool:
        """Verify user owns the business"""
        result = await db.execute(
            select(Business).where(
                and_(
                    Business.id == business_id,
                    Business.owner_id == user_id
                )
            )
        )
        business = result.scalars().first()
        return business is not None
