"""create Ai migrations tables and update users table

Revision ID: 6ef9a3a1d099
Revises: 220f03728f1d
Create Date: 2025-08-15 08:55:05.903533

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '6ef9a3a1d099'
down_revision: Union[str, None] = '220f03728f1d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add UUID column to users table
    op.add_column('users', sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Create ai_agents table (Agent Configuration Only)
    op.create_table('ai_agents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('agent_type', sa.String(length=100), nullable=False),
        sa.Column('capabilities', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_ai_agents_id'), 'ai_agents', ['id'], unique=False)
    op.create_index(op.f('ix_ai_agents_uuid'), 'ai_agents', ['uuid'], unique=True)

    # Create ai_agent_responses table
    op.create_table('ai_agent_responses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.String(length=255), nullable=False),
        sa.Column('response', sa.Text(), nullable=False),
        sa.Column('response_type', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['ai_agents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_ai_agent_responses_id'), 'ai_agent_responses', ['id'], unique=False)
    op.create_index(op.f('ix_ai_agent_responses_uuid'), 'ai_agent_responses', ['uuid'], unique=True)

    # Create user_agent_associations table (Enhanced Relationship Management)
    op.create_table('user_agent_associations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('association_type', sa.String(length=100), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('assigned_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['ai_agents.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.UniqueConstraint('user_id', 'is_primary', name='uq_user_primary_agent')
    )
    op.create_index(op.f('ix_user_agent_associations_id'), 'user_agent_associations', ['id'], unique=False)
    op.create_index(op.f('ix_user_agent_associations_uuid'), 'user_agent_associations', ['uuid'], unique=True)
    op.create_index(op.f('ix_user_agent_associations_user_id'), 'user_agent_associations', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_agent_associations_agent_id'), 'user_agent_associations', ['agent_id'], unique=False)
    op.create_index(op.f('ix_user_agent_associations_is_primary'), 'user_agent_associations', ['is_primary'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_user_agent_associations_is_primary'), table_name='user_agent_associations')
    op.drop_index(op.f('ix_user_agent_associations_agent_id'), table_name='user_agent_associations')
    op.drop_index(op.f('ix_user_agent_associations_user_id'), table_name='user_agent_associations')
    op.drop_index(op.f('ix_user_agent_associations_uuid'), table_name='user_agent_associations')
    op.drop_index(op.f('ix_user_agent_associations_id'), table_name='user_agent_associations')
    op.drop_table('user_agent_associations')
    op.drop_index(op.f('ix_ai_agent_responses_uuid'), table_name='ai_agent_responses')
    op.drop_index(op.f('ix_ai_agent_responses_id'), table_name='ai_agent_responses')
    op.drop_table('ai_agent_responses')
    op.drop_index(op.f('ix_ai_agents_uuid'), table_name='ai_agents')
    op.drop_index(op.f('ix_ai_agents_id'), table_name='ai_agents')
    op.drop_table('ai_agents')
    op.drop_constraint('uq_users_uuid', 'users', type_='unique')
    op.drop_column('users', 'uuid')
