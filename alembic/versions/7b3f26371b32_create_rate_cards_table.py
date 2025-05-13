"""create rate cards table

Revision ID: 7b3f26371b32
Revises: 519c23173b40
Create Date: 2025-05-12 17:44:18.736278

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b3f26371b32'
down_revision: Union[str, None] = '519c23173b40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
     # Create rate_cards table
    op.create_table(
        'rate_cards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('influencer_id', sa.Integer(), nullable=False),
        sa.Column('platform_id', sa.Integer(), nullable=True),
        sa.Column('content_type', sa.String(), nullable=True),
        sa.Column('base_rate', sa.Float(), nullable=False),
        sa.Column('audience_size_multiplier', sa.Float(), nullable=True, server_default='1.0'),
        sa.Column('engagement_rate_multiplier', sa.Float(), nullable=True, server_default='1.0'),
        sa.Column('exclusivity_fee', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('usage_rights_fee', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('revision_fee', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('rush_fee', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['influencer_id'], ['influencers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['platform_id'], ['social_media_platforms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index for faster lookups
    op.create_index(op.f('ix_rate_cards_id'), 'rate_cards', ['id'], unique=True)
    op.create_index(op.f('ix_rate_cards_influencer_id_platform_id'), 'rate_cards', ['influencer_id', 'platform_id'], unique=True)


def downgrade() -> None:
     # Drop table and indexes
    op.drop_index(op.f('ix_rate_cards_influencer_id_platform_id'), table_name='rate_cards')
    op.drop_index(op.f('ix_rate_cards_id'), table_name='rate_cards')
    op.drop_table('rate_cards')
