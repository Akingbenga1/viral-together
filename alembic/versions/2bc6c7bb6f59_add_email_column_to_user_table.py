"""Add email column to user table

Revision ID: 2bc6c7bb6f59
Revises: 26a48748b5aa
Create Date: 2025-05-18 16:39:13.916945

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2bc6c7bb6f59'
down_revision: Union[str, None] = '26a48748b5aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('email', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('mobile_number', sa.String(length=20), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'email')
    op.drop_column('users', 'mobile_number')
