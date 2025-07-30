"""create twitter posts table

Revision ID: 777b45188ea9
Revises: a5a63918a5a3
Create Date: 2025-07-28 12:40:49.553177

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '777b45188ea9'
down_revision: Union[str, None] = 'a5a63918a5a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'twitter_posts',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), unique=True, nullable=False, index=True),
        sa.Column('notification_id', sa.Integer, sa.ForeignKey('notifications.id'), nullable=True, index=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('tweet_content', sa.Text, nullable=False),
        sa.Column('tweet_id', sa.String(100), nullable=True),
        sa.Column('status', sa.String(20), default='pending', index=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('event_metadata', sa.JSON, default=sa.text('\'{}\'::json')),
        
        # Timestamps
        sa.Column('posted_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )


def downgrade() -> None:
    op.drop_table('twitter_posts') 
