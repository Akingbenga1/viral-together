from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class IGeocodingService(ABC):
    """Interface for geocoding operations only"""
    
    @abstractmethod
    async def geocode_address(self, address: str, country_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Convert address to coordinates"""
        pass
    
    @abstractmethod
    async def reverse_geocode(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """Convert coordinates to address"""
        pass

class ILocationSearchInterface(ABC):
    """Interface for location search operations only"""
    
    @abstractmethod
    async def search_locations(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search locations by name/city"""
        pass
