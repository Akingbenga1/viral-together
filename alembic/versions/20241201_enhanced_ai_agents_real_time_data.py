"""Enhanced AI Agents with Real-time Data Integration

Revision ID: enhanced_ai_agents_real_time
Revises: da56af67047a
Create Date: 2024-12-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'enhanced_ai_agents_real_time'
down_revision = 'da56af67047a'
branch_labels = None
depends_on = None


def upgrade():
    """Add real-time data capabilities to AI agents"""
    
    # Add real-time data fields to ai_agents table
    op.add_column('ai_agents', sa.Column('real_time_data_enabled', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('ai_agents', sa.Column('web_search_enabled', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('ai_agents', sa.Column('social_media_apis_enabled', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('ai_agents', sa.Column('market_analysis_enabled', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('ai_agents', sa.Column('trending_content_enabled', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('ai_agents', sa.Column('competitor_analysis_enabled', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('ai_agents', sa.Column('engagement_tracking_enabled', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('ai_agents', sa.Column('brand_opportunities_enabled', sa.Boolean(), nullable=False, server_default='true'))
    
    # Add performance tracking fields
    op.add_column('ai_agents', sa.Column('last_real_time_update', sa.DateTime(timezone=True), nullable=True))
    op.add_column('ai_agents', sa.Column('real_time_data_quality_score', sa.Float(), nullable=True))
    op.add_column('ai_agents', sa.Column('api_response_time_ms', sa.Integer(), nullable=True))
    
    # Create real-time data cache table
    op.create_table('real_time_data_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cache_key', sa.String(255), nullable=False),
        sa.Column('data_type', sa.String(100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('cached_data', sa.JSON(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['ai_agents.id'], ondelete='CASCADE')
    )
    
    # Create indexes for performance
    op.create_index('idx_real_time_cache_key', 'real_time_data_cache', ['cache_key'])
    op.create_index('idx_real_time_cache_expires', 'real_time_data_cache', ['expires_at'])
    op.create_index('idx_real_time_cache_user_agent', 'real_time_data_cache', ['user_id', 'agent_id'])
    
    # Create API usage tracking table
    op.create_table('api_usage_tracking',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('service_name', sa.String(100), nullable=False),
        sa.Column('endpoint', sa.String(255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('request_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_request_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rate_limit_reset_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['ai_agents.id'], ondelete='CASCADE')
    )
    
    # Create indexes for API usage tracking
    op.create_index('idx_api_usage_service', 'api_usage_tracking', ['service_name'])
    op.create_index('idx_api_usage_user_agent', 'api_usage_tracking', ['user_id', 'agent_id'])
    
    # Create real-time data sources table
    op.create_table('real_time_data_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_name', sa.String(100), nullable=False),
        sa.Column('source_type', sa.String(50), nullable=False),  # 'web_search', 'social_media', 'analytics'
        sa.Column('api_endpoint', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),  # 'active', 'inactive', 'error'
        sa.Column('rate_limit_per_hour', sa.Integer(), nullable=True),
        sa.Column('rate_limit_per_day', sa.Integer(), nullable=True),
        sa.Column('last_health_check', sa.DateTime(timezone=True), nullable=True),
        sa.Column('health_status', sa.String(20), nullable=True),  # 'healthy', 'degraded', 'down'
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index for data sources
    op.create_index('idx_data_sources_type', 'real_time_data_sources', ['source_type'])
    op.create_index('idx_data_sources_status', 'real_time_data_sources', ['status'])
    
    # Insert default data sources
    op.execute("""
        INSERT INTO real_time_data_sources (source_name, source_type, status, rate_limit_per_hour, rate_limit_per_day) VALUES
        ('DuckDuckGo Search', 'web_search', 'active', 60, 1000),
        ('Google Custom Search', 'web_search', 'active', 100, 100),
        ('Twitter API v2', 'social_media', 'active', 300, 10000),
        ('Instagram Basic Display API', 'social_media', 'active', 200, 10000),
        ('YouTube Data API v3', 'social_media', 'active', 10000, 10000),
        ('TikTok for Business API', 'social_media', 'active', 1000, 10000),
        ('Real-time Analytics Service', 'analytics', 'active', 1000, 50000),
        ('Market Analysis Service', 'analytics', 'active', 500, 10000)
    """)


def downgrade():
    """Remove real-time data capabilities from AI agents"""
    
    # Drop tables
    op.drop_table('real_time_data_sources')
    op.drop_table('api_usage_tracking')
    op.drop_table('real_time_data_cache')
    
    # Remove columns from ai_agents table
    op.drop_column('ai_agents', 'brand_opportunities_enabled')
    op.drop_column('ai_agents', 'engagement_tracking_enabled')
    op.drop_column('ai_agents', 'competitor_analysis_enabled')
    op.drop_column('ai_agents', 'trending_content_enabled')
    op.drop_column('ai_agents', 'market_analysis_enabled')
    op.drop_column('ai_agents', 'social_media_apis_enabled')
    op.drop_column('ai_agents', 'web_search_enabled')
    op.drop_column('ai_agents', 'real_time_data_enabled')
    op.drop_column('ai_agents', 'api_response_time_ms')
    op.drop_column('ai_agents', 'real_time_data_quality_score')
    op.drop_column('ai_agents', 'last_real_time_update')
