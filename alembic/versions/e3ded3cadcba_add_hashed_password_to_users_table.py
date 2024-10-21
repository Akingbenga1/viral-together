"""add hashed password to users table 

Revision ID: e3ded3cadcba
Revises: 7ade4087b9a7
Create Date: 2024-10-13 20:11:42.440528

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3ded3cadcba'
down_revision: Union[str, None] = '7ade4087b9a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('hashed_password', sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'hashed_password')
