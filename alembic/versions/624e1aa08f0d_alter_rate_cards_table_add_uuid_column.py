"""alter  rate cards table add uuid column

Revision ID: 624e1aa08f0d
Revises: 7b3f26371b32
Create Date: 2025-05-12 17:48:32.695012

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '624e1aa08f0d'
down_revision: Union[str, None] = '7b3f26371b32'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('rate_cards', sa.Column('uuid', sa.String(length=255), nullable=False))
    op.create_index(op.f('ix_rate_cards_uuid'), 'rate_cards', ['uuid'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_rate_cards_uuid'), table_name='rate_cards')
    op.drop_column('rate_cards', 'uuid')
