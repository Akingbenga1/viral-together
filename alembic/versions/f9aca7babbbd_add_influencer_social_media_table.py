"""add_influencer_social_media_table

Revision ID: f9aca7babbbd
Revises: c4a81dad96ba
Create Date: 2025-10-04 18:13:54.137235

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f9aca7babbbd'
down_revision: Union[str, None] = 'c4a81dad96ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create influencer_social_media table
    op.create_table(
        'influencer_social_media',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('influencer_id', sa.Integer(), nullable=False),
        sa.Column('social_media_platform_id', sa.Integer(), nullable=False),
        sa.Column('handle', sa.String(length=255), nullable=False),
        sa.Column('bio_url', sa.String(length=500), nullable=True),
        sa.Column('follower_count', sa.Integer(), nullable=True),
        sa.Column('is_verified', sa.String(length=10), server_default='False', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['influencer_id'], ['influencers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['social_media_platform_id'], ['social_media_platforms.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_influencer_social_media_id'), 'influencer_social_media', ['id'], unique=False)


def downgrade() -> None:
    # Drop the table
    op.drop_index(op.f('ix_influencer_social_media_id'), table_name='influencer_social_media')
    op.drop_table('influencer_social_media')
