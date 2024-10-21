"""Create influencers table

Revision ID: 58f2c0259bfc
Revises: e3ded3cadcba
Create Date: 2024-10-15 08:40:40.777376

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '58f2c0259bfc'
down_revision: Union[str, None] = 'e3ded3cadcba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'influencers',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('profile_image_url', sa.String(length=255), nullable=True),
        sa.Column('website_url', sa.String(length=255), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('languages', sa.String(length=255), nullable=True),
        sa.Column('availability', sa.Boolean(), default=True, nullable=False),
        sa.Column('rate_per_post', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('total_posts', sa.Integer(), nullable=True),  # Optional
        sa.Column('growth_rate', sa.Numeric(precision=5, scale=2), nullable=True),  # Optional
        sa.Column('successful_campaigns', sa.Integer(), nullable=True),  # Optional
    )
    op.create_index('ix_influencers_user_id', 'influencers', ['user_id'])


def downgrade() -> None:
    op.drop_table('influencers')
