"""create business table 

Revision ID: ee3f11d38a84
Revises: 58f2c0259bfc
Create Date: 2024-10-17 14:45:33.659074

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ee3f11d38a84'
down_revision: Union[str, None] = '58f2c0259bfc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'businesses',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
                sa.Column('name', sa.String(length=255), nullable=False, unique=True, index=True),
                sa.Column('description', sa.Text, nullable=True),
                sa.Column('website_url', sa.String(length=255), nullable=True),
                sa.Column('location', sa.String(length=100), nullable=True),
                sa.Column('contact_email', sa.String(length=255), nullable=False),
                sa.Column('contact_phone', sa.String(length=20), nullable=True),
                sa.Column('industry', sa.String(length=100), nullable=True),
                sa.Column('logo_url', sa.String(length=255), nullable=True),  # Optional logo URL
                sa.Column('rating', sa.Float(precision=2), nullable=True),  # Optional rating field
                sa.Column('verified', sa.Boolean(), default=False),  # Whether the business is verified or not
                sa.Column('owner_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
                sa.Column('category', sa.String(length=100), nullable=True),  # Optional business category
                sa.Column('founded_year', sa.Integer, nullable=True),  # Optional founded year
                sa.Column('number_of_employees', sa.Integer, nullable=True),  # Optional number of employees
                sa.Column('annual_revenue', sa.Numeric(precision=15, scale=2), nullable=True),  # Optional revenue
                sa.Column('active', sa.Boolean(), default=True),  # Business active or not
                sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
                sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )


def downgrade() -> None:
    op.drop_table('businesses')
