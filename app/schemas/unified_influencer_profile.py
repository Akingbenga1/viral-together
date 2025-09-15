from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

# Sub-schemas for nested data
class UserProfile(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    username: str
    mobile_number: Optional[str] = None
    created_at: datetime

class CountryInfo(BaseModel):
    id: int
    name: str
    code: str

class OperationalLocation(BaseModel):
    id: int
    influencer_id: int
    city_name: str
    region_name: Optional[str] = None
    region_code: Optional[str] = None
    country_code: str
    country_name: str
    latitude: Decimal
    longitude: Decimal
    postcode: Optional[str] = None
    time_zone: Optional[str] = None
    is_primary: bool
    created_at: datetime

class CoachingGroup(BaseModel):
    id: int
    coach_influencer_id: int
    name: str
    description: Optional[str] = None
    is_paid: bool
    price: Optional[Decimal] = None
    currency: str
    max_members: Optional[int] = None
    current_members: int
    join_code: str
    is_active: bool
    created_at: datetime

class RateCard(BaseModel):
    id: int
    uuid: str
    influencer_id: int
    platform_id: Optional[int] = None
    content_type: str
    base_rate: float
    audience_size_multiplier: float
    engagement_rate_multiplier: float
    exclusivity_fee: float
    usage_rights_fee: float
    revision_fee: float
    rush_fee: float
    description: Optional[str] = None
    created_at: datetime
    platform_name: Optional[str] = None  # From relationship

class RateSummary(BaseModel):
    average_rate: Optional[float] = None
    min_rate: Optional[float] = None
    max_rate: Optional[float] = None
    total_cards: int

class InfluencerTargets(BaseModel):
    id: int
    user_id: int
    posting_frequency: Optional[str] = None
    engagement_goals: Optional[str] = None
    follower_growth: Optional[str] = None
    pricing: Optional[Decimal] = None
    pricing_currency: str
    estimated_hours_per_week: Optional[str] = None
    content_types: Optional[List[str]] = None
    platform_recommendations: Optional[List[str]] = None
    content_creation_tips: Optional[List[str]] = None
    created_at: datetime

class SocialMediaPlatform(BaseModel):
    id: int
    name: str
    icon_url: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None

class InfluencerProfile(BaseModel):
    id: int
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    website_url: Optional[str] = None
    location: Optional[str] = None
    languages: Optional[str] = None
    availability: bool
    rate_per_post: Optional[float] = None
    total_posts: Optional[int] = None
    growth_rate: Optional[float] = None
    successful_campaigns: int
    base_country_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    # Nested user data
    user: UserProfile
    base_country: CountryInfo
    collaboration_countries: List[CountryInfo] = []

class UnifiedInfluencerProfile(BaseModel):
    """Unified response containing all influencer-related data"""
    
    # Core influencer data
    influencer: InfluencerProfile
    
    # Operational locations
    operational_locations: List[OperationalLocation] = []
    
    # Coaching groups (both as coach and member)
    coaching_groups_as_coach: List[CoachingGroup] = []
    coaching_groups_as_member: List[CoachingGroup] = []
    
    # Rate cards and pricing
    rate_cards: List[RateCard] = []
    rate_summary: Optional[RateSummary] = None
    
    # Influencer targets/goals
    influencer_targets: Optional[InfluencerTargets] = None
    
    # Social media platforms
    social_media_platforms: List[SocialMediaPlatform] = []
    
    # Metadata
    data_gathered_at: datetime = Field(default_factory=datetime.now)
    total_data_points: int = 0
    
    class Config:
        from_attributes = True

class UnifiedInfluencerProfileResponse(BaseModel):
    """Special response model that handles SQLAlchemy to Pydantic conversion"""
    
    # Core influencer data (converted from SQLAlchemy)
    influencer: InfluencerProfile
    
    # Operational locations (converted from SQLAlchemy)
    operational_locations: List[OperationalLocation] = []
    
    # Coaching groups (converted from SQLAlchemy)
    coaching_groups_as_coach: List[CoachingGroup] = []
    coaching_groups_as_member: List[CoachingGroup] = []
    
    # Rate cards (converted from SQLAlchemy)
    rate_cards: List[RateCard] = []
    rate_summary: Optional[RateSummary] = None
    
    # Influencer targets (converted from SQLAlchemy)
    influencer_targets: Optional[InfluencerTargets] = None
    
    # Social media platforms (converted from SQLAlchemy)
    social_media_platforms: List[SocialMediaPlatform] = []
    
    # Metadata
    data_gathered_at: datetime = Field(default_factory=datetime.now)
    total_data_points: int = 0
    
    @classmethod
    def from_sqlalchemy_models(
        cls,
        influencer,
        operational_locations,
        coaching_groups_as_coach,
        coaching_groups_as_member,
        rate_cards,
        rate_summary,
        influencer_targets,
        social_media_platforms
    ):
        """Factory method to convert SQLAlchemy models to Pydantic response"""
        
        # Convert influencer with nested relationships
        influencer_data = {
            "id": influencer.id,
            "bio": influencer.bio,
            "profile_image_url": influencer.profile_image_url,
            "website_url": influencer.website_url,
            "location": influencer.location,
            "languages": influencer.languages,
            "availability": influencer.availability,
            "rate_per_post": influencer.rate_per_post,
            "total_posts": influencer.total_posts,
            "growth_rate": influencer.growth_rate,
            "successful_campaigns": influencer.successful_campaigns,
            "base_country_id": influencer.base_country_id,
            "user_id": influencer.user_id,
            "created_at": influencer.created_at,
            "updated_at": influencer.updated_at,
            "user": {
                "id": influencer.user.id,
                "first_name": influencer.user.first_name,
                "last_name": influencer.user.last_name,
                "email": influencer.user.email,
                "username": influencer.user.username,
                "mobile_number": influencer.user.mobile_number,
                "created_at": influencer.user.created_at
            },
            "base_country": {
                "id": influencer.base_country.id,
                "name": influencer.base_country.name,
                "code": influencer.base_country.code
            },
            "collaboration_countries": [
                {
                    "id": country.id,
                    "name": country.name,
                    "code": country.code
                }
                for country in influencer.collaboration_countries
            ]
        }
        
        # Convert operational locations
        operational_locations_data = [
            {
                "id": loc.id,
                "influencer_id": loc.influencer_id,
                "city_name": loc.city_name,
                "region_name": loc.region_name,
                "region_code": loc.region_code,
                "country_code": loc.country_code,
                "country_name": loc.country_name,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "postcode": loc.postcode,
                "time_zone": loc.time_zone,
                "is_primary": loc.is_primary,
                "created_at": loc.created_at
            }
            for loc in operational_locations
        ]
        
        # Convert coaching groups
        coaching_groups_as_coach_data = [
            {
                "id": group.id,
                "coach_influencer_id": group.coach_influencer_id,
                "name": group.name,
                "description": group.description,
                "is_paid": group.is_paid,
                "price": group.price,
                "currency": group.currency,
                "max_members": group.max_members,
                "current_members": group.current_members,
                "join_code": group.join_code,
                "is_active": group.is_active,
                "created_at": group.created_at
            }
            for group in coaching_groups_as_coach
        ]
        
        coaching_groups_as_member_data = [
            {
                "id": group.id,
                "coach_influencer_id": group.coach_influencer_id,
                "name": group.name,
                "description": group.description,
                "is_paid": group.is_paid,
                "price": group.price,
                "currency": group.currency,
                "max_members": group.max_members,
                "current_members": group.current_members,
                "join_code": group.join_code,
                "is_active": group.is_active,
                "created_at": group.created_at
            }
            for group in coaching_groups_as_member
        ]
        
        # Convert rate cards
        rate_cards_data = [
            {
                "id": card.id,
                "uuid": str(card.uuid),
                "influencer_id": card.influencer_id,
                "platform_id": card.platform_id,
                "content_type": card.content_type,
                "base_rate": card.base_rate,
                "audience_size_multiplier": card.audience_size_multiplier,
                "engagement_rate_multiplier": card.engagement_rate_multiplier,
                "exclusivity_fee": card.exclusivity_fee,
                "usage_rights_fee": card.usage_rights_fee,
                "revision_fee": card.revision_fee,
                "rush_fee": card.rush_fee,
                "description": card.description,
                "created_at": card.created_at,
                "platform_name": card.platform.name if card.platform else None
            }
            for card in rate_cards
        ]
        
        # Convert influencer targets
        influencer_targets_data = None
        if influencer_targets:
            influencer_targets_data = {
                "id": influencer_targets.id,
                "user_id": influencer_targets.user_id,
                "posting_frequency": influencer_targets.posting_frequency,
                "engagement_goals": influencer_targets.engagement_goals,
                "follower_growth": influencer_targets.follower_growth,
                "pricing": influencer_targets.pricing,
                "pricing_currency": influencer_targets.pricing_currency,
                "estimated_hours_per_week": influencer_targets.estimated_hours_per_week,
                "content_types": influencer_targets.content_types,
                "platform_recommendations": influencer_targets.platform_recommendations,
                "content_creation_tips": influencer_targets.content_creation_tips,
                "created_at": influencer_targets.created_at
            }
        
        # Convert social media platforms
        social_media_platforms_data = [
            {
                "id": platform.id,
                "name": platform.name,
                "icon_url": platform.icon_url,
                "description": platform.description,
                "category": None  # SocialMediaPlatform model doesn't have category field
            }
            for platform in social_media_platforms
        ]
        
        return cls(
            influencer=influencer_data,
            operational_locations=operational_locations_data,
            coaching_groups_as_coach=coaching_groups_as_coach_data,
            coaching_groups_as_member=coaching_groups_as_member_data,
            rate_cards=rate_cards_data,
            rate_summary=rate_summary,
            influencer_targets=influencer_targets_data,
            social_media_platforms=social_media_platforms_data,
            data_gathered_at=datetime.now(),
            total_data_points=(
                len(operational_locations) +
                len(coaching_groups_as_coach) +
                len(coaching_groups_as_member) +
                len(rate_cards) +
                (1 if influencer_targets else 0) +
                len(social_media_platforms)
            )
        )