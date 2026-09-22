"""add influencer fans requests

Revision ID: 0ec41c217d77
Revises: 289391985aa1
Create Date: 2025-10-27 08:37:45.163859

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0ec41c217d77'
down_revision: Union[str, None] = '289391985aa1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'influencer_fans_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=36), nullable=False),
        sa.Column('influencer_id', sa.Integer(), nullable=False),
        sa.Column('requester_name', sa.String(length=255), nullable=True),
        sa.Column('requester_email', sa.String(length=255), nullable=True),
        sa.Column('country_id', sa.Integer(), nullable=False),
        sa.Column('city_name', sa.String(length=255), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('country_code', sa.String(length=10), nullable=True),
        sa.Column('country_name', sa.String(length=255), nullable=True),
        sa.Column('region_name', sa.String(length=255), nullable=True),
        sa.Column('region_code', sa.String(length=50), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['influencer_id'], ['influencers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['country_id'], ['countries.id'], ondelete='RESTRICT')
    )

    # Create indexes for performance
    op.create_index(op.f('ix_influencer_fans_requests_id'), 'influencer_fans_requests', ['id'], unique=False)
    op.create_index(op.f('ix_influencer_fans_requests_uuid'), 'influencer_fans_requests', ['uuid'], unique=True)
    op.create_index(op.f('ix_influencer_fans_requests_influencer_id'), 'influencer_fans_requests', ['influencer_id'], unique=False)
    op.create_index(op.f('ix_influencer_fans_requests_country_id'), 'influencer_fans_requests', ['country_id'], unique=False)
    op.create_index(op.f('ix_influencer_fans_requests_status'), 'influencer_fans_requests', ['status'], unique=False)
    op.create_index(op.f('ix_influencer_fans_requests_created_at'), 'influencer_fans_requests', ['created_at'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_influencer_fans_requests_created_at'), table_name='influencer_fans_requests')
    op.drop_index(op.f('ix_influencer_fans_requests_status'), table_name='influencer_fans_requests')
    op.drop_index(op.f('ix_influencer_fans_requests_country_id'), table_name='influencer_fans_requests')
    op.drop_index(op.f('ix_influencer_fans_requests_influencer_id'), table_name='influencer_fans_requests')
    op.drop_index(op.f('ix_influencer_fans_requests_uuid'), table_name='influencer_fans_requests')
    op.drop_index(op.f('ix_influencer_fans_requests_id'), table_name='influencer_fans_requests')
    op.drop_table('influencer_fans_requests')
