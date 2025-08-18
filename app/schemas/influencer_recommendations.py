from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID

class InfluencerRecommendationsBase(BaseModel):
    user_id: int
    user_level: str = Field(..., description="beginner, intermediate, advanced")
    base_plan: Dict[str, Any]
    enhanced_plan: Dict[str, Any]
    monthly_schedule: Dict[str, Any]
    performance_goals: Dict[str, Any]
    pricing_recommendations: Dict[str, Any]
    ai_insights: Optional[List[Dict[str, Any]]] = None
    coordination_uuid: Optional[str] = None
    status: str = Field(default="active", description="active, implemented, archived")

class InfluencerRecommendationsCreate(InfluencerRecommendationsBase):
    pass

class InfluencerRecommendationsUpdate(BaseModel):
    user_level: Optional[str] = None
    base_plan: Optional[Dict[str, Any]] = None
    enhanced_plan: Optional[Dict[str, Any]] = None
    monthly_schedule: Optional[Dict[str, Any]] = None
    performance_goals: Optional[Dict[str, Any]] = None
    pricing_recommendations: Optional[Dict[str, Any]] = None
    ai_insights: Optional[List[Dict[str, Any]]] = None
    coordination_uuid: Optional[str] = None
    status: Optional[str] = None

class InfluencerRecommendations(InfluencerRecommendationsBase):
    id: int
    uuid: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
