from app.core.config import settings
from app.services.interfaces.geocoding_service_interface import IGeocodingService, ILocationSearchInterface
from app.services.geocoding.openstreetmap_service import OpenStreetMapService
from app.services.geocoding.google_maps_service import GoogleMapsService
import logging

logger = logging.getLogger(__name__)

class GeocodingServiceFactory:
    """Factory for creating geocoding services based on configuration"""
    
    @staticmethod
    def create_geocoding_service() -> IGeocodingService:
        """Create geocoding service based on configuration"""
        provider = settings.LOCATION_SERVICE_PROVIDER.lower()
        
        if provider == "openstreetmap":
            logger.info("Using OpenStreetMap geocoding service")
            return OpenStreetMapService()
        elif provider == "google":
            logger.info("Using Google Maps geocoding service")
            return GoogleMapsService()
        else:
            logger.warning(f"Unknown geocoding provider: {provider}. Falling back to OpenStreetMap")
            return OpenStreetMapService()
    
    @staticmethod
    def create_location_search_service() -> ILocationSearchInterface:
        """Create location search service based on configuration"""
        provider = settings.LOCATION_SERVICE_PROVIDER.lower()
        
        if provider == "openstreetmap":
            logger.info("Using OpenStreetMap location search service")
            return OpenStreetMapService()
        elif provider == "google":
            logger.info("Using Google Maps location search service")
            return GoogleMapsService()
        else:
            logger.warning(f"Unknown location search provider: {provider}. Falling back to OpenStreetMap")
            return OpenStreetMapService()
