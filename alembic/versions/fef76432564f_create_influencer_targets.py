"""create influencer targets

Revision ID: fef76432564f
Revises: da56af67047a
Create Date: 2025-08-26 18:08:35.120078

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fef76432564f'
down_revision: Union[str, None] = 'da56af67047a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table('influencers_targets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('posting_frequency', sa.String(length=100), nullable=True),
        sa.Column('engagement_goals', sa.String(length=200), nullable=True),
        sa.Column('follower_growth', sa.String(length=100), nullable=True),
        sa.Column('pricing', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('pricing_currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('estimated_hours_per_week', sa.String(length=50), nullable=True),
        sa.Column('content_types', sa.JSON(), nullable=True),
        sa.Column('platform_recommendations', sa.JSON(), nullable=True),
        sa.Column('content_creation_tips', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_influencers_targets_id'), 'influencers_targets', ['id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_influencers_targets_id'), table_name='influencers_targets')
    op.drop_table('influencers_targets')