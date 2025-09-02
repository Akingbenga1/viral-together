import httpx
import asyncio
from typing import Dict, List, Optional, Tuple
from app.services.interfaces.geocoding_service_interface import IGeocodingService, ILocationSearchInterface
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class GoogleMapsService(IGeocodingService, ILocationSearchInterface):
    """Google Maps implementation of geocoding and location search services"""
    
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.base_url = settings.GOOGLE_MAPS_BASE_URL
        
        if not self.api_key:
            raise ValueError("Google Maps API key is required")
    
    async def geocode_address(self, address: str, country_code: Optional[str] = None) -> Optional[Dict]:
        """Convert address to coordinates using Google Maps Geocoding API"""
        try:
            params = {
                "address": address,
                "key": self.api_key,
                "output": "json"
            }
            
            if country_code:
                params["components"] = f"country:{country_code}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/maps/api/geocode/json",
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                if data["status"] == "OK" and data["results"]:
                    result = data["results"][0]
                    location = result["geometry"]["location"]
                    
                    # Extract address components
                    address_components = result.get("address_components", [])
                    address_data = self._extract_address_components(address_components)
                    
                    return {
                        "latitude": location["lat"],
                        "longitude": location["lng"],
                        "display_name": result["formatted_address"],
                        "city": address_data.get("city"),
                        "region": address_data.get("state"),
                        "country": address_data.get("country"),
                        "postcode": address_data.get("postal_code"),
                        "country_code": address_data.get("country_code", "").upper()
                    }
                return None
                
        except Exception as e:
            logger.error(f"Google Maps geocoding error: {e}")
            return None
    
    async def reverse_geocode(self, latitude: float, longitude: float) -> Optional[Dict]:
        """Convert coordinates to address using Google Maps Reverse Geocoding API"""
        try:
            params = {
                "latlng": f"{latitude},{longitude}",
                "key": self.api_key,
                "output": "json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/maps/api/geocode/json",
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                if data["status"] == "OK" and data["results"]:
                    result = data["results"][0]
                    address_components = result.get("address_components", [])
                    address_data = self._extract_address_components(address_components)
                    
                    return {
                        "display_name": result["formatted_address"],
                        "city": address_data.get("city"),
                        "region": address_data.get("state"),
                        "country": address_data.get("country"),
                        "postcode": address_data.get("postal_code"),
                        "country_code": address_data.get("country_code", "").upper()
                    }
                return None
                
        except Exception as e:
            logger.error(f"Google Maps reverse geocoding error: {e}")
            return None
    
    async def search_locations(self, query: str, limit: int = 10) -> List[Dict]:
        """Search locations using Google Maps Places API"""
        try:
            params = {
                "input": query,
                "key": self.api_key,
                "output": "json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/maps/api/place/autocomplete/json",
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                if data["status"] == "OK":
                    results = []
                    for place in data["predictions"][:limit]:
                        # Get place details for coordinates
                        place_details = await self._get_place_details(place["place_id"])
                        if place_details:
                            results.append(place_details)
                    return results
                return []
                
        except Exception as e:
            logger.error(f"Google Maps location search error: {e}")
            return []
    
    async def _get_place_details(self, place_id: str) -> Optional[Dict]:
        """Get detailed information about a place"""
        try:
            params = {
                "place_id": place_id,
                "key": self.api_key,
                "fields": "geometry,formatted_address,address_components",
                "output": "json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/maps/api/place/details/json",
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                if data["status"] == "OK":
                    result = data["result"]
                    location = result["geometry"]["location"]
                    address_components = result.get("address_components", [])
                    address_data = self._extract_address_components(address_components)
                    
                    return {
                        "display_name": result["formatted_address"],
                        "latitude": location["lat"],
                        "longitude": location["lng"],
                        "city": address_data.get("city"),
                        "region": address_data.get("state"),
                        "country": address_data.get("country"),
                        "country_code": address_data.get("country_code", "").upper()
                    }
                return None
                
        except Exception as e:
            logger.error(f"Google Maps place details error: {e}")
            return None
    
    def _extract_address_components(self, address_components: List[Dict]) -> Dict[str, str]:
        """Extract address components from Google Maps response"""
        address_data = {}
        
        for component in address_components:
            types = component.get("types", [])
            value = component.get("long_name", "")
            
            if "locality" in types or "sublocality" in types:
                address_data["city"] = value
            elif "administrative_area_level_1" in types:
                address_data["state"] = value
            elif "country" in types:
                address_data["country"] = value
            elif "postal_code" in types:
                address_data["postal_code"] = value
            elif "country" in types and "short_name" in component:
                address_data["country_code"] = component["short_name"]
        
        return address_data
