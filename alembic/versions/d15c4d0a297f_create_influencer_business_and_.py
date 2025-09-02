"""create influencer, business and promotion location

Revision ID: d15c4d0a297f
Revises: 3fec060ddae1
Create Date: 2025-09-01 11:33:17.191859

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd15c4d0a297f'
down_revision: Union[str, None] = '3fec060ddae1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create influencer_operational_locations table
    op.create_table('influencer_operational_locations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('influencer_id', sa.Integer(), nullable=False),
        sa.Column('city_name', sa.String(length=100), nullable=False),
        sa.Column('region_name', sa.String(length=100), nullable=True),
        sa.Column('region_code', sa.String(length=10), nullable=True),
        sa.Column('country_code', sa.String(length=2), nullable=False),
        sa.Column('country_name', sa.String(length=100), nullable=False),
        sa.Column('latitude', sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column('longitude', sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column('postcode', sa.String(length=20), nullable=True),
        sa.Column('time_zone', sa.String(length=50), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['influencer_id'], ['influencers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create business_operational_locations table
    op.create_table('business_operational_locations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('city_name', sa.String(length=100), nullable=False),
        sa.Column('region_name', sa.String(length=100), nullable=True),
        sa.Column('region_code', sa.String(length=10), nullable=True),
        sa.Column('country_code', sa.String(length=2), nullable=False),
        sa.Column('country_name', sa.String(length=100), nullable=False),
        sa.Column('latitude', sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column('longitude', sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column('postcode', sa.String(length=20), nullable=True),
        sa.Column('time_zone', sa.String(length=50), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create location_promotion_requests table
    op.create_table('location_promotion_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('promotion_id', sa.Integer(), nullable=False),
        sa.Column('latitude', sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column('longitude', sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column('country_id', sa.Integer(), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('region_name', sa.String(length=100), nullable=True),
        sa.Column('region_code', sa.String(length=10), nullable=True),
        sa.Column('postcode', sa.String(length=20), nullable=True),
        sa.Column('time_zone', sa.String(length=50), nullable=True),
        sa.Column('radius_km', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
        sa.ForeignKeyConstraint(['promotion_id'], ['promotions.id'], ),
        sa.ForeignKeyConstraint(['country_id'], ['countries.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add indexes for better performance
    op.create_index('ix_influencer_operational_locations_influencer_id', 'influencer_operational_locations', ['influencer_id'])
    op.create_index('ix_business_operational_locations_business_id', 'business_operational_locations', ['business_id'])
    op.create_index('ix_location_promotion_requests_business_id', 'location_promotion_requests', ['business_id'])
    op.create_index('ix_location_promotion_requests_promotion_id', 'location_promotion_requests', ['promotion_id'])
    op.create_index('ix_location_promotion_requests_country_id', 'location_promotion_requests', ['country_id'])

def downgrade():
    op.drop_index('ix_location_promotion_requests_country_id', table_name='location_promotion_requests')
    op.drop_index('ix_location_promotion_requests_promotion_id', table_name='location_promotion_requests')
    op.drop_index('ix_location_promotion_requests_business_id', table_name='location_promotion_requests')
    op.drop_index('ix_business_operational_locations_business_id', table_name='business_operational_locations')
    op.drop_index('ix_influencer_operational_locations_influencer_id', table_name='influencer_operational_locations')
    op.drop_table('location_promotion_requests')
    op.drop_table('business_operational_locations')
    op.drop_table('influencer_operational_locations')