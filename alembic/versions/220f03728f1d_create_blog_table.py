"""create blog table

Revision ID: 220f03728f1d
Revises: 960238597da3
Create Date: 2025-08-08 02:20:44.635147

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '220f03728f1d'
down_revision: Union[str, None] = '960238597da3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'blogs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('author_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('topic', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('images_json', sa.Text(), nullable=True),
        sa.Column('cover_image_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True)
    )
    op.create_index('ix_blogs_slug', 'blogs', ['slug'], unique=True)
    op.create_index('ix_blogs_author_id', 'blogs', ['author_id'])
    op.create_index('ix_blogs_topic', 'blogs', ['topic'])


def downgrade() -> None:
    op.drop_index('ix_blogs_topic', table_name='blogs')
    op.drop_index('ix_blogs_author_id', table_name='blogs')
    op.drop_index('ix_blogs_slug', table_name='blogs')
    op.drop_table('blogs')