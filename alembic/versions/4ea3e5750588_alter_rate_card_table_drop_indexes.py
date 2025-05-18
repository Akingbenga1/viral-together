"""alter rate card table drop indexes

Revision ID: 4ea3e5750588
Revises: 4feb8c8f9af3
Create Date: 2025-05-17 17:22:59.619862

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ea3e5750588'
down_revision: Union[str, None] = '4feb8c8f9af3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f('ix_rate_cards_influencer_id_platform_id'), table_name='rate_cards')
    op.drop_index(op.f('ix_rate_cards_id'), table_name='rate_cards')



def downgrade() -> None:
    op.create_index(op.f('ix_rate_cards_id'), 'rate_cards', ['id'], unique=True)
    op.create_index(op.f('ix_rate_cards_influencer_id_platform_id'), 'rate_cards', ['influencer_id', 'platform_id'], unique=True)
