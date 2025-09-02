from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.services.interfaces.location_service_interface import ILocationSearchService
from app.db.models.location import InfluencerOperationalLocation, BusinessOperationalLocation, LocationPromotionRequest
from app.db.models.influencer import Influencer
from app.db.models.business import Business
import math

class LocationSearchService(ILocationSearchService):
    """Single responsibility: Handle location-based search operations"""
    
    async def find_entities_nearby(
        self, 
        db: Session, 
        latitude: float, 
        longitude: float, 
        radius_km: float,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Find entities within specified radius"""
        # This method can be extended for different entity types
        # without modifying the base implementation
        pass
    
    async def find_influencers_nearby(
        self,
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float,
        category: Optional[str] = None,
        min_followers: Optional[int] = None,
        max_rate: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Find influencers within specified radius"""
        locations = db.query(InfluencerOperationalLocation).join(Influencer).all()
        
        nearby_influencers = []
        
        for location in locations:
            distance = await self.calculate_distance(
                latitude, longitude,
                float(location.latitude), float(location.longitude)
            )
            
            if distance <= radius_km:
                # Apply filters
                if category and location.influencer.category != category:
                    continue
                    
                if min_followers and location.influencer.total_posts < min_followers:
                    continue
                    
                if max_rate and location.influencer.rate_per_post > max_rate:
                    continue
                
                nearby_influencers.append({
                    "influencer": location.influencer,
                    "location": location,
                    "distance_km": round(distance, 2)
                })
        
        # Sort by distance
        nearby_influencers.sort(key=lambda x: x["distance_km"])
        return nearby_influencers
    
    async def find_businesses_nearby(
        self,
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float,
        industry: Optional[str] = None,
        verified_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Find businesses within specified radius"""
        query = db.query(BusinessOperationalLocation).join(Business)
        
        if verified_only:
            query = query.filter(Business.verified == True)
        
        locations = query.all()
        
        nearby_businesses = []
        
        for location in locations:
            distance = await self.calculate_distance(
                latitude, longitude,
                float(location.latitude), float(location.longitude)
            )
            
            if distance <= radius_km:
                if industry and location.business.industry != industry:
                    continue
                
                nearby_businesses.append({
                    "business": location.business,
                    "location": location,
                    "distance_km": round(distance, 2)
                })
        
        nearby_businesses.sort(key=lambda x: x["distance_km"])
        return nearby_businesses
    
    async def find_promotion_requests_nearby(
        self,
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float,
        min_budget: Optional[float] = None,
        max_budget: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Find promotion requests within specified radius"""
        requests = db.query(LocationPromotionRequest).all()
        
        nearby_requests = []
        
        for request in requests:
            distance = await self.calculate_distance(
                latitude, longitude,
                float(request.latitude), float(request.longitude)
            )
            
            if distance <= radius_km:
                if min_budget and request.promotion.budget and request.promotion.budget < min_budget:
                    continue
                    
                if max_budget and request.promotion.budget and request.promotion.budget > max_budget:
                    continue
                
                nearby_requests.append({
                    "request": request,
                    "business": request.business,
                    "promotion": request.promotion,
                    "distance_km": round(distance, 2)
                })
        
        nearby_requests.sort(key=lambda x: x["distance_km"])
        return nearby_requests
    
    async def calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371  # Earth's radius in kilometers
        
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
