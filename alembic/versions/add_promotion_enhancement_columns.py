"""Add promotion enhancement columns

Revision ID: add_promotion_enhancement_columns
Revises: 
Create Date: 2024-01-15 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'promo_enhance_001'
down_revision = '819b7b5ad102'  # Latest revision
branch_labels = None
depends_on = None


def upgrade():
    # Add missing columns to promotions table
    op.add_column('promotions', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('promotions', sa.Column('status', sa.String(50), nullable=True, default='pending'))
    op.add_column('promotions', sa.Column('spent_amount', sa.Numeric(10, 2), nullable=True, default=0))
    
    # Update existing records to have default status
    op.execute("UPDATE promotions SET status = 'pending' WHERE status IS NULL")


def downgrade():
    # Remove the added columns
    op.drop_column('promotions', 'spent_amount')
    op.drop_column('promotions', 'status')
    op.drop_column('promotions', 'description')
