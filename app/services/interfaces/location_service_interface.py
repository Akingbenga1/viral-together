from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.schemas.location import LocationBase

class ILocationService(ABC):
    """Interface for location services - open for extension, closed for modification"""
    
    @abstractmethod
    async def add_location(self, db: Session, entity_id: int, location: LocationBase, current_user) -> Any:
        """Add location for an entity"""
        pass
    
    @abstractmethod
    async def get_locations(self, db: Session, entity_id: int, current_user) -> List[Any]:
        """Get all locations for an entity"""
        pass
    
    @abstractmethod
    async def update_location(self, db: Session, location_id: int, location: LocationBase, current_user) -> Any:
        """Update a location"""
        pass
    
    @abstractmethod
    async def delete_location(self, db: Session, location_id: int, current_user) -> bool:
        """Delete a location"""
        pass

class ILocationSearchService(ABC):
    """Interface for location search services"""
    
    @abstractmethod
    async def find_entities_nearby(
        self, 
        db: Session, 
        latitude: float, 
        longitude: float, 
        radius_km: float,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Find entities within specified radius"""
        pass
    
    @abstractmethod
    async def calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points"""
        pass
