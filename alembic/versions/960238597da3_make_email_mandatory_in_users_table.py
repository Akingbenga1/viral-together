"""make email mandatory in users table

Revision ID: 960238597da3
Revises: 777b45188ea9
Create Date: 2025-08-03 19:21:43.205940

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '960238597da3'
down_revision: Union[str, None] = '777b45188ea9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # First, ensure there are no duplicate emails before making it unique
    # This is a safety check - if there are duplicates, the migration will fail

    
    # Make email column non-nullable
    op.alter_column('users', 'email',
                    existing_type=sa.String(length=255),
                    nullable=False)
    
    # Create unique index on email
    op.create_unique_constraint('uq_users_email', 'users', ['email'])


def downgrade() -> None:
    # Drop unique constraint on email
    op.drop_constraint('uq_users_email', 'users', type_='unique')
    
    # Make email column nullable again
    op.alter_column('users', 'email',
                    existing_type=sa.String(length=255),
                    nullable=True) 