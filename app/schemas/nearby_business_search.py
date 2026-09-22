"""
Schema for businesses near you feature - combines DB businesses with MCP search results
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from decimal import Decimal


class NearbyBusinessMCPResult(BaseModel):
    """Business information retrieved from MCP search (external businesses)"""
    name: str
    website_url: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    description: Optional[str] = None
    category: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    hours: Optional[str] = None
    price_range: Optional[str] = None
    source: str = "mcp_search"  # Identifies this as external search result
    relevance_score: float = 0.0
    
    class Config:
        from_attributes = True


class NearbyBusinessDBResult(BaseModel):
    """Business information from our database"""
    id: int
    name: str
    website_url: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: str
    industry: Optional[str] = None
    location: Optional[str] = None
    logo_url: Optional[str] = None
    rating: Optional[float] = None
    verified: bool = False
    category: Optional[str] = None
    founded_year: Optional[int] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    city_name: Optional[str] = None
    country_name: Optional[str] = None
    region_name: Optional[str] = None
    distance_km: Optional[float] = None
    source: str = "database"  # Identifies this as our own data
    
    class Config:
        from_attributes = True


class NearbyBusinessSearchResult(BaseModel):
    """Combined results from database and MCP search"""
    database_businesses: List[NearbyBusinessDBResult] = []
    external_businesses: List[NearbyBusinessMCPResult] = []
    search_location: Optional[str] = None
    total_results: int = 0
    db_count: int = 0
    external_count: int = 0


class NearbyBusinessSearchRequest(BaseModel):
    """Request to find businesses near an influencer's location"""
    influencer_id: int
    radius_km: float = Field(50, ge=1, le=500)
    industry_filter: Optional[str] = None
    verified_only: bool = False
    include_external: bool = True  # Whether to include MCP search results

