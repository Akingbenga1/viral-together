"""create_countries_table

Revision ID: 8d3b0ee6e7c5
Revises: ac5712194995
Create Date: 2025-06-20 22:05:57.563657

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d3b0ee6e7c5'
down_revision: Union[str, None] = 'ac5712194995'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'countries',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('code', sa.String(2), nullable=False, unique=True, comment='ISO 3166-1 alpha-2 country code'),
        sa.Column('code3', sa.String(3), nullable=True, unique=True, comment='ISO 3166-1 alpha-3 country code'),
        sa.Column('numeric_code', sa.String(3), nullable=True, comment='ISO 3166-1 numeric country code'),
        sa.Column('phone_code', sa.String(10), nullable=True, comment='International dialing code'),
        sa.Column('capital', sa.String(100), nullable=True),
        sa.Column('currency', sa.String(3), nullable=True, comment='ISO 4217 currency code'),
        sa.Column('currency_name', sa.String(50), nullable=True),
        sa.Column('currency_symbol', sa.String(10), nullable=True),
        sa.Column('tld', sa.String(10), nullable=True, comment='Top-level domain'),
        sa.Column('region', sa.String(50), nullable=True),
        sa.Column('timezones', sa.Text, nullable=True, comment='JSON array of timezones'),
        sa.Column('latitude', sa.Numeric(10, 8), nullable=True),
        sa.Column('longitude', sa.Numeric(11, 8), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create indexes for commonly queried fields
    op.create_index('idx_countries_name', 'countries', ['name'])
    op.create_index('idx_countries_code', 'countries', ['code'])
    op.create_index('idx_countries_region', 'countries', ['region'])


def downgrade() -> None:
    op.drop_index('idx_countries_region', table_name='countries')
    op.drop_index('idx_countries_code', table_name='countries')
    op.drop_index('idx_countries_name', table_name='countries')
    
    # Drop the table
    op.drop_table('countries')
