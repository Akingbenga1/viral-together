"""create social media platforms  table

Revision ID: 519c23173b40
Revises: 6535f36e40bc
Create Date: 2025-05-12 15:38:13.897502

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '519c23173b40'
down_revision: Union[str, None] = '6535f36e40bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
     # Create social_media_platforms table
    op.create_table(
        'social_media_platforms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('icon_url', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create unique index on name
    op.create_index(op.f('ix_social_media_platforms_id'), 'social_media_platforms', ['id'], unique=True)
    op.create_index(op.f('ix_social_media_platforms_name'), 'social_media_platforms', ['name'], unique=True)



def downgrade() -> None:
    op.drop_table('social_media_platforms')
