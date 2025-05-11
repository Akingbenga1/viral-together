"""Add created_at and updated_at to users table

Revision ID: 6535f36e40bc
Revises: ee3f11d38a84
Create Date: 2025-05-11 18:16:40.133389

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6535f36e40bc'
down_revision: Union[str, None] = 'ee3f11d38a84'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False))
    op.add_column('users', sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False))



def downgrade() -> None:
    op.drop_column('users', 'created_at')
    op.drop_column('users', 'updated_at')
