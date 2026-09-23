"""add username column as unique column

Revision ID: 7ade4087b9a7
Revises: 277a6ebbb95d
Create Date: 2024-10-13 18:05:36.827194

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7ade4087b9a7'
down_revision: Union[str, None] = '277a6ebbb95d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add a new unique column to the users table
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('username', sa.String(150), nullable=True))
    
    # Update existing rows with a default username pattern
    connection = op.get_bind()
    connection.execute(sa.text("UPDATE users SET username = 'user_' || id WHERE username IS NULL"))
    
    # Now make the column NOT NULL and add unique constraint
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('username', nullable=False)
        batch_op.create_unique_constraint('uq_users_username', ['username'])


def downgrade() -> None:
    # Remove the unique column if we downgrade
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_constraint('uq_users_username', type_='unique')
        batch_op.drop_column('username')
