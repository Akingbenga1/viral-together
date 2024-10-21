"""create users table

Revision ID: 277a6ebbb95d
Revises: 
Create Date: 2024-10-13 17:46:58.596183

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '277a6ebbb95d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('mobile', sa.String(20)),
        sa.Column('description', sa.Unicode(200)),
    )


def downgrade() -> None:
    op.drop_table('users')
