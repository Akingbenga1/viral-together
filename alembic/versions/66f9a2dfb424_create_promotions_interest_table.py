"""create promotions interest table

Revision ID: 66f9a2dfb424
Revises: 3f75a0f64a93
Create Date: 2025-07-19 22:13:24.734203

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '66f9a2dfb424'
down_revision: Union[str, None] = '3f75a0f64a93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    op.create_table(
        'promotion_interest',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('promotion_id', sa.Integer(), sa.ForeignKey('promotions.id'), nullable=False),
        sa.Column('influencer_id', sa.Integer(), sa.ForeignKey('influencers.id'), nullable=False),
        sa.Column('expressed_interest', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('status', sa.String(length=50), server_default='pending'),
        sa.Column('notes', sa.Text()),
    )


def downgrade() -> None:
    op.drop_table('promotion_interest')
