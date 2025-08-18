"""seed AI agents table

Revision ID: da56af67047a
Revises: d58f1bc228c8
Create Date: 2025-08-17 15:09:37.257516

"""
from typing import Sequence, Union
import uuid
from datetime import datetime
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql




# revision identifiers, used by Alembic.
revision: str = 'da56af67047a'
down_revision: Union[str, None] = 'd58f1bc228c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # AI Agents data to be seeded
    ai_agents_data = [
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Influencer Growth Agent',
            'agent_type': 'growth_advisor',
            'capabilities': '{"content_strategy": true, "audience_analysis": true, "platform_optimization": true, "engagement_tactics": true, "growth_metrics": true, "trend_identification": true}',
            'status': 'active',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Business Development Agent',
            'agent_type': 'business_advisor',
            'capabilities': '{"market_research": true, "partnership_opportunities": true, "brand_strategy": true, "revenue_optimization": true, "business_planning": true, "competitive_analysis": true}',
            'status': 'active',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Content Strategy Agent',
            'agent_type': 'content_advisor',
            'capabilities': '{"content_planning": true, "trend_analysis": true, "creative_direction": true, "publishing_schedule": true, "content_optimization": true, "storytelling": true}',
            'status': 'active',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Analytics & Insights Agent',
            'agent_type': 'analytics_advisor',
            'capabilities': '{"performance_analysis": true, "data_interpretation": true, "kpi_tracking": true, "optimization_recommendations": true, "reporting": true, "predictive_analytics": true}',
            'status': 'active',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Collaboration Manager Agent',
            'agent_type': 'collaboration_advisor',
            'capabilities': '{"partnership_matching": true, "campaign_coordination": true, "communication_facilitation": true, "project_management": true, "contract_negotiation": true, "relationship_building": true}',
            'status': 'active',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Rate Card Optimization Agent',
            'agent_type': 'pricing_advisor',
            'capabilities': '{"market_rate_analysis": true, "pricing_strategy": true, "value_proposition": true, "negotiation_support": true, "pricing_optimization": true, "revenue_maximization": true}',
            'status': 'active',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Social Media Platform Specialist',
            'agent_type': 'platform_advisor',
            'capabilities': '{"instagram_optimization": true, "tiktok_strategy": true, "youtube_management": true, "cross_platform_synergy": true, "platform_algorithms": true, "feature_optimization": true}',
            'status': 'active',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Brand Safety & Compliance Agent',
            'agent_type': 'compliance_advisor',
            'capabilities': '{"content_moderation": true, "brand_guidelines": true, "regulatory_compliance": true, "risk_assessment": true, "policy_enforcement": true, "legal_guidance": true}',
            'status': 'active',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Community Engagement Agent',
            'agent_type': 'engagement_advisor',
            'capabilities': '{"audience_interaction": true, "community_building": true, "feedback_management": true, "relationship_nurturing": true, "engagement_strategies": true, "community_moderation": true}',
            'status': 'active',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'uuid': str(uuid.uuid4()),
            'name': 'Performance Optimization Agent',
            'agent_type': 'optimization_advisor',
            'capabilities': '{"campaign_optimization": true, "roi_analysis": true, "a_b_testing": true, "performance_forecasting": true, "efficiency_improvement": true, "resource_optimization": true}',
            'status': 'active',
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    ]
    
    # Insert AI agents data
    for agent_data in ai_agents_data:
        op.execute(
            sa.text("""
                INSERT INTO ai_agents (uuid, name, agent_type, capabilities, status, is_active, created_at, updated_at)
                VALUES (:uuid, :name, :agent_type, :capabilities, :status, :is_active, :created_at, :updated_at)
            """).bindparams(**agent_data)
        )


def downgrade():
    # Remove seeded AI agents by agent_type
    agent_types = [
        'growth_advisor',
        'business_advisor', 
        'content_advisor',
        'analytics_advisor',
        'collaboration_advisor',
        'pricing_advisor',
        'platform_advisor',
        'compliance_advisor',
        'engagement_advisor',
        'optimization_advisor'
    ]
    
    for agent_type in agent_types:
        op.execute(
            sa.text("DELETE FROM ai_agents WHERE agent_type = :agent_type").bindparams(agent_type=agent_type)
        )