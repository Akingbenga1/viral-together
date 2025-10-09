"""Add download_links column to influencer_recommendation_summaries

Revision ID: 6d1c8dc27113
Revises: 113b1925b7d7
Create Date: 2025-10-03 14:50:14.255750

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6d1c8dc27113'
down_revision: Union[str, None] = '113b1925b7d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add download_links column as JSON array
    op.add_column('influencer_recommendation_summaries', 
                  sa.Column('download_links', sa.JSON, nullable=True))


def downgrade() -> None:
    # Remove download_links column
    op.drop_column('influencer_recommendation_summaries', 'download_links')
