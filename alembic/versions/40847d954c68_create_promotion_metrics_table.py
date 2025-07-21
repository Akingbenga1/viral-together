"""create promotion metrics table

Revision ID: 40847d954c68
Revises: 67a74ba98cf4
Create Date: 2025-07-21 11:27:23.969424

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '40847d954c68'
down_revision: Union[str, None] = '67a74ba98cf4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'collaboration_metrics',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('collaboration_id', sa.Integer(), sa.ForeignKey('collaborations.id'), nullable=False),
        sa.Column('initial_rate_proposed', sa.Numeric(precision=10, scale=2)),
        sa.Column('final_rate_agreed', sa.Numeric(precision=10, scale=2)),
        sa.Column('negotiation_rounds', sa.Integer()),
        sa.Column('time_to_agreement_hours', sa.Integer()),
        sa.Column('deliverables_submitted', sa.Integer()),
        sa.Column('deliverables_approved', sa.Integer()),
        sa.Column('deliverables_rejected', sa.Integer()),
        sa.Column('revision_requests', sa.Integer()),
        sa.Column('agreed_completion_date', sa.DateTime()),
        sa.Column('actual_completion_date', sa.DateTime()),
        sa.Column('days_early_or_late', sa.Integer()),
        sa.Column('business_rating', sa.Numeric(precision=3, scale=2)),
        sa.Column('influencer_rating', sa.Numeric(precision=3, scale=2)),
        sa.Column('collaboration_success', sa.Boolean()),
        sa.Column('payment_status', sa.String(length=50)),
        sa.Column('payment_completed_date', sa.DateTime()),
        sa.Column('days_to_payment', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('collaboration_metrics')
