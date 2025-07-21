"""create promotions table

Revision ID: 440ed4adaa17
Revises: e2d28df69181
Create Date: 2025-07-18 22:08:29.946179

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '440ed4adaa17'
down_revision: Union[str, None] = 'e2d28df69181'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'promotions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('business_id', sa.Integer(), sa.ForeignKey('businesses.id'), nullable=False),
        sa.Column('promotion_name', sa.String(length=255), nullable=False),
        sa.Column('promotion_item', sa.String(length=255), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('discount', sa.Numeric(precision=5, scale=2)),
        sa.Column('budget', sa.Numeric(precision=10, scale=2)),
        sa.Column('target_audience', sa.String(length=255)),
        sa.Column('social_media_platform_id', sa.Integer(), sa.ForeignKey('social_media_platforms.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('promotions')