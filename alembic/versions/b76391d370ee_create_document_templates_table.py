"""create document templates table

Revision ID: b76391d370ee
Revises: 40847d954c68
Create Date: 2025-07-21 11:28:51.952095

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b76391d370ee'
down_revision: Union[str, None] = '40847d954c68'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'document_templates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('subtype', sa.String(length=50)),
        sa.Column('prompt_text', sa.Text(), nullable=False),
        sa.Column('default_parameters', sa.JSON()),
        sa.Column('file_format', sa.String(length=20), server_default='pdf', nullable=False),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true()),
    )
    op.create_index('idx_document_templates_type', 'document_templates', ['type'])
    op.create_index('idx_document_templates_subtype', 'document_templates', ['subtype'])


def downgrade() -> None:
    op.drop_table('document_templates') 