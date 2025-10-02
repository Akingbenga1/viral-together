from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class GrowthStrategyBase(BaseModel):
    strategy: str
    description: str
    expected_growth: Optional[str] = None
    implementation: Optional[str] = None


class ContentIdeaBase(BaseModel):
    idea: str
    description: str
    content_type: Optional[str] = None
    posting_frequency: Optional[str] = None
    expected_engagement: Optional[str] = None


class SocialProfileBase(BaseModel):
    name: str
    platform: str
    profile_url: str
    followers: Optional[str] = None
    relevance_reason: str


class InfluencerCollabBase(BaseModel):
    collaboration: str
    description: str
    expected_reach: Optional[str] = None
    implementation: Optional[str] = None


class BusinessCollabBase(BaseModel):
    opportunity: str
    type: str
    description: str
    location: Optional[str] = None
    potential_revenue: Optional[str] = None
    implementation: Optional[str] = None
    relevance_reason: str


class ContentScriptBase(BaseModel):
    script: str
    content: str
    platform: str
    duration: Optional[str] = None
    hashtags: Optional[str] = None


class InfluencerRecommendationSummariesBase(BaseModel):
    influencer_recommendation_id: int
    influencer_id: int
    more_followers: Optional[List[GrowthStrategyBase]] = None
    content_ideas: Optional[List[ContentIdeaBase]] = None
    social_profiles: Optional[List[SocialProfileBase]] = None
    influencer_collab: Optional[List[InfluencerCollabBase]] = None
    business_collab: Optional[List[BusinessCollabBase]] = None
    content_scripts: Optional[List[ContentScriptBase]] = None


class InfluencerRecommendationSummariesCreate(InfluencerRecommendationSummariesBase):
    pass


class InfluencerRecommendationSummariesUpdate(BaseModel):
    more_followers: Optional[List[GrowthStrategyBase]] = None
    content_ideas: Optional[List[ContentIdeaBase]] = None
    social_profiles: Optional[List[SocialProfileBase]] = None
    influencer_collab: Optional[List[InfluencerCollabBase]] = None
    business_collab: Optional[List[BusinessCollabBase]] = None
    content_scripts: Optional[List[ContentScriptBase]] = None


class InfluencerRecommendationSummariesResponse(InfluencerRecommendationSummariesBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GrowthStrategiesResponse(BaseModel):
    """Response schema for the growth strategies endpoint"""
    more_followers: Optional[List[Dict[str, Any]]] = None
    content_ideas: Optional[List[Dict[str, Any]]] = None
    social_profiles: Optional[List[Dict[str, Any]]] = None
    influencer_collab: Optional[List[Dict[str, Any]]] = None
    business_collab: Optional[List[Dict[str, Any]]] = None
    content_scripts: Optional[List[Dict[str, Any]]] = None
