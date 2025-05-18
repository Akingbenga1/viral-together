"""alter users table add stripe_customer_id column

Revision ID: 26a48748b5aa
Revises: 57fe485dffff
Create Date: 2025-05-18 14:30:27.485464

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26a48748b5aa'
down_revision: Union[str, None] = '57fe485dffff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('stripe_customer_id', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'stripe_customer_id')
