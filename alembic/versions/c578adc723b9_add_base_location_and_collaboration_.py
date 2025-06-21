"""add base location and collaboration scope

Revision ID: c578adc723b9
Revises: d8173f7783ac
Create Date: 2025-06-21 20:25:06.585370

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c578adc723b9'
down_revision: Union[str, None] = 'd8173f7783ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands for collaboration scope ###
    op.create_table('business_collaboration_countries',
    sa.Column('business_id', sa.Integer(), nullable=False),
    sa.Column('country_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
    sa.ForeignKeyConstraint(['country_id'], ['countries.id'], ),
    sa.PrimaryKeyConstraint('business_id', 'country_id')
    )
    op.create_table('influencer_collaboration_countries',
    sa.Column('influencer_id', sa.Integer(), nullable=False),
    sa.Column('country_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['country_id'], ['countries.id'], ),
    sa.ForeignKeyConstraint(['influencer_id'], ['influencers.id'], ),
    sa.PrimaryKeyConstraint('influencer_id', 'country_id')
    )
    # ### end commands for collaboration scope ###

    # ### commands for base location ###
    # NOTE: Adding base_country_id as nullable=True to prevent errors on existing data.
    # A separate data migration would be needed to populate this for existing rows
    # before making it non-nullable.
    op.add_column('businesses', sa.Column('base_country_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_businesses_base_country_id', 'businesses', 'countries', ['base_country_id'], ['id'])
    
    op.add_column('influencers', sa.Column('base_country_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_influencers_base_country_id', 'influencers', 'countries', ['base_country_id'], ['id'])
    # ### end commands for base location ###


def downgrade() -> None:
    # ### commands for base location ###
    op.drop_constraint('fk_influencers_base_country_id', 'influencers', type_='foreignkey')
    op.drop_column('influencers', 'base_country_id')
    
    op.drop_constraint('fk_businesses_base_country_id', 'businesses', type_='foreignkey')
    op.drop_column('businesses', 'base_country_id')
    # ### end commands for base location ###

    # ### commands for collaboration scope ###
    op.drop_table('influencer_collaboration_countries')
    op.drop_table('business_collaboration_countries')
    # ### end commands for collaboration scope ###