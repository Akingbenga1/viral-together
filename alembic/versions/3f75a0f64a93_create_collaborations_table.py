"""create collaborations table

Revision ID: 3f75a0f64a93
Revises: 440ed4adaa17
Create Date: 2025-07-19 22:10:30.126032

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f75a0f64a93'
down_revision: Union[str, None] = '440ed4adaa17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'collaborations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('influencer_id', sa.Integer(), sa.ForeignKey('influencers.id'), nullable=False),
        sa.Column('promotion_id', sa.Integer(), sa.ForeignKey('promotions.id'), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='pending'),
        sa.Column('proposed_amount', sa.Numeric(precision=10, scale=2)),
        sa.Column('negotiated_amount', sa.Numeric(precision=10, scale=2)),
        sa.Column('negotiable', sa.Boolean(), server_default=sa.false()),
        sa.Column('collaboration_type', sa.String(length=50), nullable=False),
        sa.Column('deliverables', sa.Text()),
        sa.Column('deadline', sa.DateTime()),
        sa.Column('terms_and_conditions', sa.Text()),
        sa.Column('contract_signed', sa.Boolean(), server_default=sa.false()),
        sa.Column('payment_status', sa.String(length=50), server_default='pending'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
    )


def downgrade() -> None:
    op.drop_table('collaborations')