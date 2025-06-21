"""merge role and country branches

Revision ID: d8173f7783ac
Revises: 61b3495d2275, a39189ae81bb
Create Date: 2025-06-21 20:23:34.736737

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8173f7783ac'
down_revision: Union[str, None] = ('61b3495d2275', 'a39189ae81bb')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
