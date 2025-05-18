"""create subscription plans table

Revision ID: 44ac4cf582ef
Revises: 4ea3e5750588
Create Date: 2025-05-18 14:20:50.197594

"""
import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '44ac4cf582ef'
down_revision: Union[str, None] = '4ea3e5750588'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
     op.create_table(
        'subscription_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('price_id', sa.String(), nullable=False),
        sa.Column('tier', sa.String(), nullable=False),  # Changed to VARCHAR
        sa.Column('price_per_month', sa.Float(), nullable=False),
        sa.Column('features', sa.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
     )


def downgrade() -> None:
    op.drop_table('subscription_plans')
