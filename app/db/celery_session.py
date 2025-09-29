"""
Database session for Celery workers - minimal imports to avoid circular dependencies
Uses synchronous PostgreSQL connection for Celery workers only
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

def get_sync_database_url():
    """Convert async database URL to synchronous URL for Celery workers"""
    # Convert postgresql+asyncpg:// to postgresql+psycopg2://
    if settings.DATABASE_URL.startswith("postgresql+asyncpg://"):
        return settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    elif settings.DATABASE_URL.startswith("postgresql://"):
        return settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
    else:
        # Fallback - assume it's already a sync URL
        return settings.DATABASE_URL

# Create a synchronous database engine for Celery workers only
sync_database_url = get_sync_database_url()
engine = create_engine(sync_database_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
