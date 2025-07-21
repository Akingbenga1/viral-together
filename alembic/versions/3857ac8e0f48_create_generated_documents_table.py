"""create generated documents table

Revision ID: 3857ac8e0f48
Revises: b76391d370ee
Create Date: 2025-07-21 11:34:09.605251

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3857ac8e0f48'
down_revision: Union[str, None] = 'b76391d370ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'generated_documents',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('template_id', sa.Integer(), sa.ForeignKey('document_templates.id'), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('subtype', sa.String(length=50)),
        sa.Column('influencer_id', sa.Integer(), sa.ForeignKey('influencers.id')),
        sa.Column('business_id', sa.Integer(), sa.ForeignKey('businesses.id')),
        sa.Column('promotion_id', sa.Integer(), sa.ForeignKey('promotions.id')),
        sa.Column('collaboration_id', sa.Integer(), sa.ForeignKey('collaborations.id')),
        sa.Column('parameters', sa.JSON(), nullable=False),
        sa.Column('file_path', sa.String(length=255), nullable=False),
        sa.Column('generation_status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('error_message', sa.Text()),
        sa.Column('generated_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('generated_documents')