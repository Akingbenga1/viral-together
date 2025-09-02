import httpx
import asyncio
from typing import Dict, List, Optional, Tuple
from app.services.interfaces.geocoding_service_interface import IGeocodingService, ILocationSearchInterface
import logging

logger = logging.getLogger(__name__)

class OpenStreetMapService(IGeocodingService, ILocationSearchInterface):
    """OpenStreetMap implementation of geocoding and location search services"""
    
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org"
        self.headers = {
            "User-Agent": "ViralTogether/1.0 (https://viraltogether.com; contact@viraltogether.com)"
        }
    
    async def geocode_address(self, address: str, country_code: Optional[str] = None) -> Optional[Dict]:
        """Convert address to coordinates using Nominatim API"""
        try:
            params = {
                "q": address,
                "format": "json",
                "limit": 1,
                "addressdetails": 1
            }
            
            if country_code:
                params["countrycodes"] = country_code
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/search",
                    params=params,
                    headers=self.headers
                )
                response.raise_for_status()
                
                data = response.json()
                if data:
                    location = data[0]
                    return {
                        "latitude": float(location["lat"]),
                        "longitude": float(location["lon"]),
                        "display_name": location["display_name"],
                        "city": location.get("address", {}).get("city") or 
                               location.get("address", {}).get("town") or
                               location.get("address", {}).get("village"),
                        "region": location.get("address", {}).get("state"),
                        "country": location.get("address", {}).get("country"),
                        "postcode": location.get("address", {}).get("postcode"),
                        "country_code": location.get("address", {}).get("country_code", "").upper()
                    }
                return None
                
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            return None
    
    async def reverse_geocode(self, latitude: float, longitude: float) -> Optional[Dict]:
        """Convert coordinates to address using Nominatim API"""
        try:
            params = {
                "lat": latitude,
                "lon": longitude,
                "format": "json",
                "addressdetails": 1
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/reverse",
                    params=params,
                    headers=self.headers
                )
                response.raise_for_status()
                
                data = response.json()
                if data:
                    address = data.get("address", {})
                    return {
                        "display_name": data["display_name"],
                        "city": address.get("city") or address.get("town") or address.get("village"),
                        "region": address.get("state"),
                        "country": address.get("country"),
                        "postcode": address.get("postcode"),
                        "country_code": address.get("country_code", "").upper()
                    }
                return None
                
        except Exception as e:
            logger.error(f"Reverse geocoding error: {e}")
            return None
    
    async def search_locations(self, query: str, limit: int = 10) -> List[Dict]:
        """Search locations by name/city"""
        try:
            params = {
                "q": query,
                "format": "json",
                "limit": limit,
                "addressdetails": 1
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/search",
                    params=params,
                    headers=self.headers
                )
                response.raise_for_status()
                
                data = response.json()
                return [
                    {
                        "display_name": item["display_name"],
                        "latitude": float(item["lat"]),
                        "longitude": float(item["lon"]),
                        "city": item.get("address", {}).get("city") or 
                               item.get("address", {}).get("town") or
                               item.get("address", {}).get("village"),
                        "region": item.get("address", {}).get("state"),
                        "country": item.get("address", {}).get("country"),
                        "country_code": item.get("address", {}).get("country_code", "").upper()
                    }
                    for item in data
                ]
                
        except Exception as e:
            logger.error(f"Location search error: {e}")
            return []
