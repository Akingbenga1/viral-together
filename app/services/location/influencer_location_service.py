from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from app.services.interfaces.location_service_interface import ILocationService
from app.db.models.location import InfluencerOperationalLocation
from app.db.models.influencer import Influencer
from app.schemas.location import InfluencerLocationCreate, InfluencerLocationUpdate
from app.core.exceptions import AuthorizationError, NotFoundError, DuplicateLocationError
from fastapi import HTTPException

class InfluencerLocationService(ILocationService):
    """Single responsibility: Handle influencer location operations"""
    
    async def add_location(
        self, 
        db: AsyncSession, 
        influencer_id: int, 
        location: InfluencerLocationCreate, 
        current_user
    ) -> InfluencerOperationalLocation:
        """Add operational location for influencer"""
        # Verify ownership
        if not await self._verify_influencer_ownership(db, influencer_id, current_user.id):
            raise AuthorizationError("Not authorized to manage this influencer's locations")
        
        # Check for duplicate coordinates (same latitude/longitude for the same influencer)
        duplicate_check = await db.execute(
            select(InfluencerOperationalLocation).where(
                and_(
                    InfluencerOperationalLocation.influencer_id == influencer_id,
                    InfluencerOperationalLocation.latitude == location.latitude,
                    InfluencerOperationalLocation.longitude == location.longitude
                )
            )
        )
        
        if duplicate_check.scalars().first():
            raise DuplicateLocationError(
                f"Location with coordinates ({location.latitude}, {location.longitude}) already exists for this influencer. "
                f"Each influencer can only have one location per set of coordinates."
            )
        
        # Check if first location (make primary)
        result = await db.execute(
            select(InfluencerOperationalLocation).where(
                InfluencerOperationalLocation.influencer_id == influencer_id
            )
        )
        existing_count = len(result.scalars().all())
        
        if existing_count == 0:
            location.is_primary = True
        
        # Create location
        from datetime import datetime
        
        db_location = InfluencerOperationalLocation(
            influencer_id=influencer_id,
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
        influencer_id: int,
        current_user
    ) -> List[InfluencerOperationalLocation]:
        """Get all operational locations for influencer"""
        if not await self._verify_influencer_ownership(db, influencer_id, current_user.id):
            raise AuthorizationError("Not authorized to view this influencer's locations")
        
        result = await db.execute(
            select(InfluencerOperationalLocation).where(
                InfluencerOperationalLocation.influencer_id == influencer_id
            )
        )
        return result.scalars().all()
    
    async def update_location(
        self, 
        db: AsyncSession, 
        location_id: int, 
        location: InfluencerLocationUpdate, 
        current_user
    ) -> InfluencerOperationalLocation:
        """Update influencer location"""
        result = await db.execute(
            select(InfluencerOperationalLocation).where(
                InfluencerOperationalLocation.id == location_id
            )
        )
        db_location = result.scalars().first()
        
        if not db_location:
            raise NotFoundError("Location not found")
        
        if not await self._verify_influencer_ownership(db, db_location.influencer_id, current_user.id):
            raise AuthorizationError("Not authorized to update this location")
        
        # Check for duplicate coordinates when updating (excluding current location)
        if 'latitude' in location.model_dump(exclude_unset=True) or 'longitude' in location.model_dump(exclude_unset=True):
            new_lat = location.latitude if 'latitude' in location.model_dump(exclude_unset=True) else db_location.latitude
            new_lng = location.longitude if 'longitude' in location.model_dump(exclude_unset=True) else db_location.longitude
            
            duplicate_check = await db.execute(
                select(InfluencerOperationalLocation).where(
                    and_(
                        InfluencerOperationalLocation.influencer_id == db_location.influencer_id,
                        InfluencerOperationalLocation.latitude == new_lat,
                        InfluencerOperationalLocation.longitude == new_lng,
                        InfluencerOperationalLocation.id != location_id  # Exclude current location
                    )
                )
            )
            
            if duplicate_check.scalars().first():
                raise DuplicateLocationError(
                    f"Location with coordinates ({new_lat}, {new_lng}) already exists for this influencer. "
                    f"Each influencer can only have one location per set of coordinates."
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
        """Delete influencer location"""
        result = await db.execute(
            select(InfluencerOperationalLocation).where(
                InfluencerOperationalLocation.id == location_id
            )
        )
        db_location = result.scalars().first()
        
        if not db_location:
            raise NotFoundError("Location not found")
        
        if not await self._verify_influencer_ownership(db, db_location.influencer_id, current_user.id):
            raise AuthorizationError("Not authorized to delete this location")
        
        db.delete(db_location)
        await db.commit()
        return True
    
    async def _verify_influencer_ownership(self, db: AsyncSession, influencer_id: int, user_id: int) -> bool:
        """Verify user owns the influencer profile"""
        result = await db.execute(
            select(Influencer).where(
                and_(
                    Influencer.id == influencer_id,
                    Influencer.user_id == user_id
                )
            )
        )
        influencer = result.scalars().first()
        return influencer is not None
