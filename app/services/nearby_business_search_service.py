"""
Service for finding businesses near influencer locations using database + MCP search
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from decimal import Decimal
import math
from app.db.models.location import InfluencerOperationalLocation, BusinessOperationalLocation
from app.db.models.business import Business
from app.db.models.influencer import Influencer
from app.schemas.nearby_business_search import (
    NearbyBusinessDBResult,
    NearbyBusinessMCPResult,
    NearbyBusinessSearchRequest,
    NearbyBusinessSearchResult
)
from app.services.mcp_client import MCPClient
from app.services.web_search.duckduckgo_search import DuckDuckGoSearchService

logger = logging.getLogger(__name__)


class NearbyBusinessSearchService:
    """
    Single responsibility: Find businesses near influencer locations
    using both database and MCP search integration
    """
    
    def __init__(
        self,
        mcp_client: Optional[MCPClient] = None,
        duckduckgo_service: Optional[DuckDuckGoSearchService] = None
    ):
        self.mcp_client = mcp_client
        self.duckduckgo_service = duckduckgo_service or DuckDuckGoSearchService()
    
    async def find_businesses_near_influencer(
        self,
        db: AsyncSession,
        request: NearbyBusinessSearchRequest
    ) -> NearbyBusinessSearchResult:
        """
        Find businesses near an influencer's ALL locations using both database and DuckDuckGo search
        
        Args:
            db: Database session
            request: Search request parameters
            
        Returns:
            Combined results from database and external search across all influencer locations
        """
        # Get ALL influencer locations (not just primary)
        influencer_locations = await self._get_all_influencer_locations(
            db, request.influencer_id
        )
        
        if not influencer_locations:
            logger.warning(f"No locations found for influencer {request.influencer_id}")
            return NearbyBusinessSearchResult(
                database_businesses=[],
                external_businesses=[],
                search_location=None,
                total_results=0,
                db_count=0,
                external_count=0
            )
        
        # Collect all businesses from all locations
        all_db_businesses = []
        all_external_businesses = []
        all_search_locations = []
        
        # Search each location
        for location in influencer_locations:
            logger.info(f"Searching businesses near location: {location.city_name}, {location.country_name}")
            
            # Search database for businesses near this location
            db_businesses = await self._find_database_businesses(
                db,
                float(location.latitude),
                float(location.longitude),
                request.radius_km,
                request.industry_filter,
                request.verified_only
            )
            
            # Search external businesses via DuckDuckGo for this location
            external_businesses = []
            if request.include_external:
                external_businesses = await self._find_external_businesses(
                    location,
                    request.radius_km,
                    request.industry_filter
                )
            
            # Add to combined results
            all_db_businesses.extend(db_businesses)
            all_external_businesses.extend(external_businesses)
            all_search_locations.append(self._format_location(location))
        
        # Remove duplicate businesses based on ID and URL
        unique_db_businesses = self._deduplicate_db_businesses(all_db_businesses)
        unique_external_businesses = self._deduplicate_external_businesses(all_external_businesses)
        
        # Format combined search locations
        search_location = " | ".join(all_search_locations) if all_search_locations else None
        
        logger.info(
            f"Found total {len(unique_db_businesses)} DB businesses and "
            f"{len(unique_external_businesses)} external businesses across {len(influencer_locations)} locations"
        )
        
        return NearbyBusinessSearchResult(
            database_businesses=unique_db_businesses,
            external_businesses=unique_external_businesses,
            search_location=search_location,
            total_results=len(unique_db_businesses) + len(unique_external_businesses),
            db_count=len(unique_db_businesses),
            external_count=len(unique_external_businesses)
        )
    
    async def _get_all_influencer_locations(
        self,
        db: AsyncSession,
        influencer_id: int
    ) -> List[InfluencerOperationalLocation]:
        """Get ALL influencer operational locations (not just primary)"""
        result = await db.execute(
            select(InfluencerOperationalLocation)
            .where(InfluencerOperationalLocation.influencer_id == influencer_id)
            .order_by(InfluencerOperationalLocation.is_primary.desc())  # Primary first
        )
        locations = result.scalars().all()
        return locations if locations else []
    
    async def _get_influencer_primary_location(
        self,
        db: AsyncSession,
        influencer_id: int
    ) -> Optional[InfluencerOperationalLocation]:
        """Get influencer's primary operational location (kept for backward compatibility)"""
        # Try primary location first
        result = await db.execute(
            select(InfluencerOperationalLocation)
            .where(InfluencerOperationalLocation.influencer_id == influencer_id)
            .where(InfluencerOperationalLocation.is_primary == True)
        )
        locations = result.scalars().all()
        location = locations[0] if locations else None
        
        if not location:
            # Fallback to any location
            result = await db.execute(
                select(InfluencerOperationalLocation)
                .where(InfluencerOperationalLocation.influencer_id == influencer_id)
            )
            locations = result.scalars().all()
            location = locations[0] if locations else None
        
        return location
    
    async def _find_database_businesses(
        self,
        db: AsyncSession,
        latitude: float,
        longitude: float,
        radius_km: float,
        industry_filter: Optional[str],
        verified_only: bool
    ) -> List[NearbyBusinessDBResult]:
        """Find businesses from our database within radius"""
        # Build async query with eager loading
        query = (
            select(BusinessOperationalLocation)
            .options(selectinload(BusinessOperationalLocation.business))
            .join(Business)
        )
        
        if verified_only:
            query = query.where(Business.verified == True)
        
        if industry_filter:
            query = query.where(Business.industry.ilike(f"%{industry_filter}%"))
        
        result = await db.execute(query)
        locations = result.scalars().all()
        
        nearby_businesses = []
        
        for location in locations:
            distance = await self._calculate_distance(
                latitude, longitude,
                float(location.latitude), float(location.longitude)
            )
            
            if distance <= radius_km:
                nearby_businesses.append(
                    NearbyBusinessDBResult(
                        id=location.business_id,
                        name=location.business.name,
                        website_url=location.business.website_url,
                        contact_phone=location.business.contact_phone,
                        contact_email=location.business.contact_email,
                        industry=location.business.industry,
                        location=location.business.location,
                        logo_url=location.business.logo_url,
                        rating=float(location.business.rating) if location.business.rating else None,
                        verified=location.business.verified,
                        category=location.business.category,
                        founded_year=location.business.founded_year,
                        latitude=location.latitude,
                        longitude=location.longitude,
                        city_name=location.city_name,
                        country_name=location.country_name,
                        region_name=location.region_name,
                        distance_km=round(distance, 2)
                    )
                )
        
        # Sort by distance
        nearby_businesses.sort(key=lambda x: x.distance_km or float('inf'))
        return nearby_businesses
    
    async def _find_external_businesses(
        self,
        influencer_location: InfluencerOperationalLocation,
        radius_km: float,
        industry_filter: Optional[str]
    ) -> List[NearbyBusinessMCPResult]:
        """
        Find external businesses using DuckDuckGo Maps search
        This searches for real businesses near the influencer's location
        """
        try:
            # Use DuckDuckGo Maps with specific city/country for better results
            logger.info(
                f"Searching DuckDuckGo Maps for businesses in "
                f"{influencer_location.city_name}, {influencer_location.country_name}"
            )
            
            # Build keywords for search
            keywords = "businesses" if not industry_filter else industry_filter
            
            # Use the location-specific Maps search
            search_results = await self.duckduckgo_service.search_maps_with_location(
                keywords=keywords,
                city=influencer_location.city_name,
                country=influencer_location.country_name,
                max_results=10
            )
            
            # Parse and format results
            external_businesses = []
            
            for idx, result in enumerate(search_results):
                external_businesses.append(
                    NearbyBusinessMCPResult(
                        name=result.title,
                        website_url=result.url,
                        description=result.snippet,
                        city=influencer_location.city_name,
                        country=influencer_location.country_name,
                        latitude=influencer_location.latitude,
                        longitude=influencer_location.longitude,
                        relevance_score=1.0 - (idx * 0.1),  # Decreasing relevance
                        source="duckduckgo_maps"
                    )
                )
            
            logger.info(f"Found {len(external_businesses)} external businesses from DuckDuckGo Maps")
            return external_businesses
            
        except Exception as e:
            logger.error(f"Error searching external businesses: {str(e)}")
            return []
    
    async def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371  # Earth's radius in kilometers
        
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _format_location(self, location: InfluencerOperationalLocation) -> str:
        """Format location for display"""
        parts = []
        if location.city_name:
            parts.append(location.city_name)
        if location.region_name:
            parts.append(location.region_name)
        if location.country_name:
            parts.append(location.country_name)
        return ", ".join(parts) if parts else "Unknown Location"
    
    def _deduplicate_db_businesses(
        self, 
        businesses: List[NearbyBusinessDBResult]
    ) -> List[NearbyBusinessDBResult]:
        """Remove duplicate database businesses based on ID"""
        seen_ids = set()
        unique_businesses = []
        
        for business in businesses:
            if business.id not in seen_ids:
                seen_ids.add(business.id)
                unique_businesses.append(business)
        
        return unique_businesses
    
    def _deduplicate_external_businesses(
        self,
        businesses: List[NearbyBusinessMCPResult]
    ) -> List[NearbyBusinessMCPResult]:
        """Remove duplicate external businesses based on name and URL similarity"""
        seen_names_lower = set()
        seen_urls = set()
        unique_businesses = []
        
        for business in businesses:
            is_duplicate = False
            business_name_lower = business.name.lower().strip()
            
            # Check if name already seen
            if business_name_lower in seen_names_lower:
                is_duplicate = True
            
            # Check if website URL already seen
            if business.website_url and business.website_url in seen_urls:
                is_duplicate = True
            
            if not is_duplicate:
                seen_names_lower.add(business_name_lower)
                if business.website_url:
                    seen_urls.add(business.website_url)
                unique_businesses.append(business)
        
        return unique_businesses

