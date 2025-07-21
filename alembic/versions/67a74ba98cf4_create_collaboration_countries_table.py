"""create collaboration countries table

Revision ID: 67a74ba98cf4
Revises: 66f9a2dfb424
Create Date: 2025-07-21 11:25:19.582918

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67a74ba98cf4'
down_revision: Union[str, None] = '66f9a2dfb424'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'collaboration_countries',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('collaboration_id', sa.Integer(), sa.ForeignKey('collaborations.id'), nullable=False),
        sa.Column('country_id', sa.Integer(), sa.ForeignKey('countries.id'), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('collaboration_countries') 