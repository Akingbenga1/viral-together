"""create influencer coaching groups

Revision ID: 3fec060ddae1
Revises: fef76432564f
Create Date: 2025-08-28 21:19:53.105499

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3fec060ddae1'
down_revision: Union[str, None] = 'fef76432564f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    # Create influencer_coaching_groups table
    op.create_table('influencer_coaching_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('coach_influencer_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_paid', sa.Boolean(), nullable=False, default=False),
        sa.Column('price', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('max_members', sa.Integer(), nullable=True),
        sa.Column('current_members', sa.Integer(), nullable=False, default=0),
        sa.Column('join_code', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),

        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['coach_influenceclear_id'], ['influencers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_influencer_coaching_groups_id'), 'influencer_coaching_groups', ['id'], unique=False)

    # Create influencer_coaching_members table
    op.create_table('influencer_coaching_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('member_influencer_id', sa.Integer(), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('payment_status', sa.String(length=20), nullable=False, default='pending'),
        sa.Column('payment_reference', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['influencer_coaching_groups.id'], ),
        sa.ForeignKeyConstraint(['member_influencer_id'], ['influencers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_influencer_coaching_members_id'), 'influencer_coaching_members', ['id'], unique=False)

    # Create influencer_coaching_sessions table
    op.create_table('influencer_coaching_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('session_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('meeting_link', sa.String(length=500), nullable=True),
        sa.Column('recording_url', sa.String(length=500), nullable=True),
        sa.Column('materials', sa.JSON(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['influencer_coaching_groups.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_influencer_coaching_sessions_id'), 'influencer_coaching_sessions', ['id'], unique=False)

    # Create influencer_coaching_messages table
    op.create_table('influencer_coaching_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('sender_influencer_id', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(length=20), nullable=False, default='text'),
        sa.Column('file_url', sa.String(length=500), nullable=True),
        sa.Column('is_announcement', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['influencer_coaching_groups.id'], ),
        sa.ForeignKeyConstraint(['sender_influencer_id'], ['influencers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_influencer_coaching_messages_id'), 'influencer_coaching_messages', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_influencer_coaching_messages_id'), table_name='influencer_coaching_messages')
    op.drop_table('influencer_coaching_messages')
    
    op.drop_index(op.f('ix_influencer_coaching_sessions_id'), table_name='influencer_coaching_sessions')
    op.drop_table('influencer_coaching_sessions')
    
    op.drop_index(op.f('ix_influencer_coaching_members_id'), table_name='influencer_coaching_members')
    op.drop_table('influencer_coaching_members')
    
    
    op.drop_index(op.f('ix_influencer_coaching_groups_id'), table_name='influencer_coaching_groups')
    op.drop_table('influencer_coaching_groups')