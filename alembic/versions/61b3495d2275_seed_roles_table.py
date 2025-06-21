"""seed roles table

Revision ID: 61b3495d2275
Revises: 3c7b07bebb69
Create Date: 2024-05-13 14:16:36.435770

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61b3495d2275'
down_revision: Union[str, None] = '3c7b07bebb69'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO roles (name, description) VALUES
        ('user', 'Regular user with basic permissions.'),
        ('influencer', 'Influencer user with specific content creation permissions.'),
        ('professional_influencer', 'Verified influencer with expanded capabilities.'),
        ('business', 'Business account with commercial permissions.'),
        ('business_influencer', 'Business account with influencer capabilities.'),
        ('moderator', 'User with additional content management permissions.'),
        ('admin', 'User with administrative permissions.'),
        ('super_admin', 'User with full system control.');
    """)


def downgrade() -> None:
    op.execute("DELETE FROM roles WHERE name IN ('user', 'influencer', 'professional_influencer', 'business', 'business_influencer', 'moderator', 'admin', 'super_admin');")
