"""create rate proposals table

Revision ID: 4feb8c8f9af3
Revises: 624e1aa08f0d
Create Date: 2025-05-12 17:56:56.471683

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4feb8c8f9af3'
down_revision: Union[str, None] = '624e1aa08f0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
     # Create rate_proposals table
    op.create_table(
        'rate_proposals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=100), nullable=False),
        sa.Column('influencer_id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('platform_id', sa.Integer(), nullable=False),
        sa.Column('proposed_rate', sa.Float(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), server_default='pending', nullable=True),
        sa.Column('message', sa.String(), nullable=True),
        sa.Column('influencer_approved', sa.String(), nullable=True),  # New column
        sa.Column('business_approved', sa.String(), nullable=True),  # New column
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['influencer_id'], ['influencers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['platform_id'], ['social_media_platforms.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_rate_proposals_id'), 'rate_proposals', ['id'], unique=True)
    op.create_index(op.f('ix_rate_proposals_uuid'), 'rate_proposals', ['uuid'], unique=True)
    op.create_index(op.f('ix_rate_proposals_influencer_id_business_id_platform_id'), 'rate_proposals', ['influencer_id', 'business_id', 'platform_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_rate_proposals_uuid'), table_name='rate_proposals')
    op.drop_index(op.f('ix_rate_proposals_id'), table_name='rate_proposals')
    op.drop_index(op.f('ix_rate_proposals_influencer_id_business_id_platform_id'), table_name='rate_proposals')
    op.drop_table('rate_proposals')
