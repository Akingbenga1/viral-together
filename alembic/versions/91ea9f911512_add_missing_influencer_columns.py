"""add_missing_influencer_columns

Revision ID: 91ea9f911512
Revises: d374cec00888
Create Date: 2025-09-30 08:58:40.057326

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91ea9f911512'
down_revision: Union[str, None] = 'd374cec00888'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing columns to influencers table for better analysis
    op.add_column('influencers', sa.Column('engagement_rate', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('influencers', sa.Column('follower_growth', sa.Integer(), nullable=True))
    op.add_column('influencers', sa.Column('reach', sa.Integer(), nullable=True))
    op.add_column('influencers', sa.Column('total_revenue', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('influencers', sa.Column('rate_cards_count', sa.Integer(), nullable=True))
    op.add_column('influencers', sa.Column('consistency_score', sa.Integer(), nullable=True))
    op.add_column('influencers', sa.Column('posting_frequency', sa.Integer(), nullable=True))
    op.add_column('influencers', sa.Column('recent_posts', sa.Integer(), nullable=True))
    op.add_column('influencers', sa.Column('username', sa.String(100), nullable=True))
    op.add_column('influencers', sa.Column('email', sa.String(255), nullable=True))
    

def downgrade() -> None:

    # Remove columns
    op.drop_column('influencers', 'recent_posts')
    op.drop_column('influencers', 'posting_frequency')
    op.drop_column('influencers', 'consistency_score')
    op.drop_column('influencers', 'rate_cards_count')
    op.drop_column('influencers', 'total_revenue')
    op.drop_column('influencers', 'reach')
    op.drop_column('influencers', 'follower_growth')
    op.drop_column('influencers', 'engagement_rate')
    op.drop_column('influencers', 'email')
    op.drop_column('influencers', 'username')
