"""add_download_links_column_to_influencer_recommendation_summaries

Revision ID: c4a81dad96ba
Revises: 6d1c8dc27113
Create Date: 2025-10-03 15:02:58.050807

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4a81dad96ba'
down_revision: Union[str, None] = '6d1c8dc27113'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add download_links column as JSON array
    op.add_column('influencer_recommendation_summaries', 
                  sa.Column('download_links', sa.JSON, nullable=True))


def downgrade() -> None:
    # Remove download_links column
    op.drop_column('influencer_recommendation_summaries', 'download_links')
