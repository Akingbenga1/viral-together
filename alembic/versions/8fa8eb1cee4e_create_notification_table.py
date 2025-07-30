"""create notification table

Revision ID: 8fa8eb1cee4e
Revises: f5e8d12a4b91
Create Date: 2025-07-28 12:29:59.561152

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '8fa8eb1cee4e'
down_revision: Union[str, None] = 'f5e8d12a4b91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), unique=True, nullable=False, index=True),
        sa.Column('event_type', sa.String(50), nullable=False, index=True),
        sa.Column('recipient_user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('recipient_type', sa.String(20), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('event_metadata', sa.JSON, default=sa.text('\'{}\'::json')),
        
        # Email tracking
        sa.Column('email_enabled', sa.Boolean, default=True),
        sa.Column('email_sent', sa.Boolean, default=False),
        sa.Column('email_sent_at', sa.DateTime, nullable=True),
        sa.Column('email_error', sa.Text, nullable=True),
        
        # Twitter tracking  
        sa.Column('twitter_enabled', sa.Boolean, default=True),
        sa.Column('twitter_posted', sa.Boolean, default=False),
        sa.Column('twitter_posted_at', sa.DateTime, nullable=True),
        sa.Column('twitter_error', sa.Text, nullable=True),
        sa.Column('twitter_post_id', sa.String(100), nullable=True),
        
        # Read status
        sa.Column('read_at', sa.DateTime, nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )


def downgrade() -> None:
    op.drop_table('notifications') 
