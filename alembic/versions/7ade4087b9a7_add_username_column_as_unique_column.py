"""add username column as unique column

Revision ID: 7ade4087b9a7
Revises: 277a6ebbb95d
Create Date: 2024-10-13 18:05:36.827194

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7ade4087b9a7'
down_revision: Union[str, None] = '277a6ebbb95d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add a new unique column to the users table
    op.add_column('users', sa.Column('username', sa.String(150), nullable=False))
    op.create_unique_constraint('uq_users_username', 'users', ['username'])


def downgrade() -> None:
    # Remove the unique column if we downgrade
    op.drop_constraint('uq_users_username', 'users', type_='unique')
    op.drop_column('users', 'username')
