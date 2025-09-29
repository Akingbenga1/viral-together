"""create task status table

Revision ID: d374cec00888
Revises: d15c4d0a297f
Create Date: 2025-09-28 17:40:19.072007

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd374cec00888'
down_revision: Union[str, None] = 'd15c4d0a297f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create task_status table
    op.create_table('task_status',
        sa.Column('task_id', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('task_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('result', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('celery_task_id', sa.String(length=255), nullable=True),
        sa.Column('task_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('task_id')
    )
    
    # Create indexes
    op.create_index('ix_task_status_user_id', 'task_status', ['user_id'])
    op.create_index('ix_task_status_task_type', 'task_status', ['task_type'])
    op.create_index('ix_task_status_status', 'task_status', ['status'])
    op.create_index('ix_task_status_celery_task_id', 'task_status', ['celery_task_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_task_status_celery_task_id', table_name='task_status')
    op.drop_index('ix_task_status_status', table_name='task_status')
    op.drop_index('ix_task_status_task_type', table_name='task_status')
    op.drop_index('ix_task_status_user_id', table_name='task_status')
    
    # Drop table
    op.drop_table('task_status')
