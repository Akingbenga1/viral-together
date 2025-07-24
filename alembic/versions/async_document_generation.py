"""Add support for async document generation

Revision ID: f5e8d12a4b91
Revises: 3857ac8e0f48
Create Date: 2024-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f5e8d12a4b91'
down_revision = '3857ac8e0f48'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Make template_id nullable for optional template support
    op.alter_column('generated_documents', 'template_id',
                    existing_type=sa.INTEGER(),
                    nullable=True)
    
    # Add default values for type and subtype
    op.alter_column('generated_documents', 'type',
                    existing_type=sa.VARCHAR(50),
                    server_default='custom')
    
    op.alter_column('generated_documents', 'subtype',
                    existing_type=sa.VARCHAR(50),
                    server_default='generated')
    
    # Ensure generation_status has proper default
    op.alter_column('generated_documents', 'generation_status',
                    existing_type=sa.VARCHAR(20),
                    server_default='pending')
def downgrade() -> None:
    # Revert template_id to not nullable (but this might fail if there are null values)
    # op.alter_column('generated_documents', 'template_id',
    #                existing_type=sa.INTEGER(),
    #                nullable=False)
    
    # Remove default values
    op.alter_column('generated_documents', 'type',
                    existing_type=sa.VARCHAR(50),
                    server_default=None)
    
    op.alter_column('generated_documents', 'subtype',
                    existing_type=sa.VARCHAR(50),
                    server_default=None)
    
    op.alter_column('generated_documents', 'generation_status',
                    existing_type=sa.VARCHAR(20),
                    server_default=None) 