"""create influencer recommendations table

Revision ID: d58f1bc228c8
Revises: 6ef9a3a1d099
Create Date: 2025-08-17 14:40:24.644866

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers, used by Alembic.
revision: str = 'd58f1bc228c8'
down_revision: Union[str, None] = '6ef9a3a1d099'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Create influencer_recommendations table
    op.create_table('influencer_recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('user_level', sa.String(length=50), nullable=False),
        sa.Column('base_plan', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('enhanced_plan', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('monthly_schedule', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('performance_goals', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('pricing_recommendations', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('ai_insights', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('coordination_uuid', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_influencer_recommendations_id'), 'influencer_recommendations', ['id'], unique=False)
    op.create_index(op.f('ix_influencer_recommendations_uuid'), 'influencer_recommendations', ['uuid'], unique=True)
    op.create_index(op.f('ix_influencer_recommendations_user_id'), 'influencer_recommendations', ['user_id'], unique=False)
    op.create_index(op.f('ix_influencer_recommendations_status'), 'influencer_recommendations', ['status'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_influencer_recommendations_status'), table_name='influencer_recommendations')
    op.drop_index(op.f('ix_influencer_recommendations_user_id'), table_name='influencer_recommendations')
    op.drop_index(op.f('ix_influencer_recommendations_uuid'), table_name='influencer_recommendations')
    op.drop_index(op.f('ix_influencer_recommendations_id'), table_name='influencer_recommendations')
    
    # Drop table
    op.drop_table('influencer_recommendations')

