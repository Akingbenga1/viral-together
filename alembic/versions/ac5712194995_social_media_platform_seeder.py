"""social_media_platform_seeder

Revision ID: ac5712194995
Revises: 2bc6c7bb6f59
Create Date: 2025-06-20 16:38:41.817697

"""
from typing import Sequence, Union
from sqlalchemy import text

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac5712194995'
down_revision: Union[str, None] = '2bc6c7bb6f59'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed social media platforms data"""
    print("Seeding Social Media Platforms...")
    
    connection = op.get_bind()
    
    # Define the platforms to seed
    platforms = [
        "Instagram",
        "TikTok", 
        "YouTube",
        "Twitter",
        "Facebook",
        "LinkedIn",
        "Snapchat",
        "Pinterest",
        "Twitch",
        "Discord"
    ]
    
    # Insert platforms using individual statements for better error handling
    for platform_name in platforms:
        connection.execute(text(f"""
            INSERT INTO social_media_platforms (name, created_at, updated_at) 
            VALUES (:name, NOW(), NOW())
            ON CONFLICT (name) DO NOTHING;
        """), {"name": platform_name})
    
    print(f"Successfully seeded {len(platforms)} social media platforms!")

def downgrade() -> None:
    """Remove seeded social media platforms data"""
    print("Removing Social Media Platforms data...")
    
    connection = op.get_bind()
    
    # Remove the seeded platforms
    platforms_to_remove = [
        "Instagram", "TikTok", "YouTube", "Twitter", "Facebook",
        "LinkedIn", "Snapchat", "Pinterest", "Twitch", "Discord"
    ]
    
    platform_list = "', '".join(platforms_to_remove)
    connection.execute(text(f"""
        DELETE FROM social_media_platforms 
        WHERE name IN ('{platform_list}');
    """))
    
    print("Social Media Platforms data removed successfully!")
