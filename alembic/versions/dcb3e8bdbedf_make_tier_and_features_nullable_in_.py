"""make tier and features nullable in subscription plans

Revision ID: dcb3e8bdbedf
Revises: c578adc723b9
Create Date: 2025-06-28 20:43:40.800916

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dcb3e8bdbedf'
down_revision: Union[str, None] = 'c578adc723b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make tier column nullable
    op.alter_column('subscription_plans', 'tier',
                    existing_type=sa.String(),
                    nullable=True)
    
    # Make features column nullable and remove server default
    op.alter_column('subscription_plans', 'features',
                    existing_type=sa.ARRAY(sa.String()),
                    nullable=True,
                    server_default=None)


def downgrade() -> None:
    # Revert tier column to not nullable
    op.alter_column('subscription_plans', 'tier',
                    existing_type=sa.String(),
                    nullable=False)
    
    # Revert features column to not nullable and restore server default
    op.alter_column('subscription_plans', 'features',
                    existing_type=sa.ARRAY(sa.String()),
                    nullable=False,
                    server_default='{}')
