"""add billing_cycle field and seed subscription plans

Revision ID: add_billing_cycle_seed_plans
Revises: e2d28df69181
Create Date: 2025-01-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_billing_cycle_seed_plans'
down_revision: Union[str, None] = 'e2d28df69181'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add billing_cycle column to subscription_plans table
    op.add_column('subscription_plans', sa.Column('billing_cycle', sa.String(), nullable=False, server_default='monthly'))
    
    # Update existing Basic plan with proper features
    op.execute("""
        UPDATE subscription_plans 
        SET features = ARRAY[
            'Access to influencer directory',
            'Basic search and filtering', 
            'Email support',
            'Up to 10 campaign requests',
            'Standard response time'
        ],
        billing_cycle = 'monthly'
        WHERE id = 1;
    """)
    
    # Insert Pro plan
    op.execute("""
        INSERT INTO subscription_plans (id, uuid, name, description, price_id, tier, price_per_month, billing_cycle, features, is_active, created_at, updated_at) VALUES
        (2, gen_random_uuid()::text, 'Pro Plan', 'Perfect for growing businesses and content creators', 'price_pro_plan', 'pro', 29.99, 'monthly', ARRAY[
            'Access to influencer directory',
            'Basic search and filtering', 
            'Email support',
            'Unlimited campaign requests',
            'Priority support',
            'Advanced analytics',
            'Custom rate cards',
            'Direct messaging'
        ], true, NOW(), NOW());
    """)
    
    # Insert Enterprise plan
    op.execute("""
        INSERT INTO subscription_plans (id, uuid, name, description, price_id, tier, price_per_month, billing_cycle, features, is_active, created_at, updated_at) VALUES
        (3, gen_random_uuid()::text, 'Enterprise Plan', 'For large organizations and agencies', 'price_enterprise_plan', 'enterprise', 99.99, 'monthly', ARRAY[
            'Access to influencer directory',
            'Basic search and filtering', 
            'Email support',
            'Unlimited everything',
            'Dedicated account manager',
            'Custom integrations',
            'White-label options',
            'API access',
            '24/7 phone support'
        ], true, NOW(), NOW());
    """)


def downgrade() -> None:
    # Remove the new plans
    op.execute("DELETE FROM subscription_plans WHERE id IN (2, 3);")
    
    # Remove billing_cycle column
    op.drop_column('subscription_plans', 'billing_cycle')
