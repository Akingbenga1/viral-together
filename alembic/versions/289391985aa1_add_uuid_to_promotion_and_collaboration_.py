"""add uuid to promotion and collaboration table

Revision ID: 289391985aa1
Revises: promo_enhance_001
Create Date: 2025-10-07 14:37:26.873991

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '289391985aa1'
down_revision: Union[str, None] = 'promo_enhance_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    # Add nullable UUID columns to promotions and collaborations
    op.add_column('promotions', sa.Column('uuid', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('collaborations', sa.Column('uuid', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))


def downgrade() -> None:
    # Drop columns on downgrade
    op.drop_column('collaborations', 'uuid')
    op.drop_column('promotions', 'uuid')
