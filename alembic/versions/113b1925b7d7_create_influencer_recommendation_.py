"""create_influencer_recommendation_summaries_table

Revision ID: 113b1925b7d7
Revises: 91ea9f911512
Create Date: 2025-09-30 18:47:04.651981

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '113b1925b7d7'
down_revision: Union[str, None] = '91ea9f911512'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create influencer_recommendation_summaries table
    op.create_table(
        'influencer_recommendation_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('influencer_recommendation_id', sa.Integer(), nullable=False),
        sa.Column('influencer_id', sa.Integer(), nullable=False),
        sa.Column('more_followers', sa.JSON(), nullable=True),
        sa.Column('content_ideas', sa.JSON(), nullable=True),
        sa.Column('social_profiles', sa.JSON(), nullable=True),
        sa.Column('influencer_collab', sa.JSON(), nullable=True),
        sa.Column('business_collab', sa.JSON(), nullable=True),
        sa.Column('content_scripts', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['influencer_recommendation_id'], ['influencer_recommendations.id'], ),
        sa.ForeignKeyConstraint(['influencer_id'], ['influencers.id'], )
    )


def downgrade() -> None:
    # Drop influencer_recommendation_summaries table
    op.drop_table('influencer_recommendation_summaries')
