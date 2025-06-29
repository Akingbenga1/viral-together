"""seed subscription plans table

Revision ID: e2d28df69181
Revises: dcb3e8bdbedf
Create Date: 2025-06-29 16:13:42.463264

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2d28df69181'
down_revision: Union[str, None] = 'dcb3e8bdbedf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO subscription_plans (id, uuid, name, description, price_id, tier, price_per_month, features, is_active, created_at, updated_at) VALUES
        (1, gen_random_uuid()::text, 'Basic Plan', 'Perfect for individuals getting started', 'price_1OEyYEBZJW6YgAadu2JERF9q', 'basic', 9.99, ARRAY['Feature 1', 'Feature 2', 'Basic Support'], true, NOW(), NOW());
    """)


def downgrade() -> None:
    pass
