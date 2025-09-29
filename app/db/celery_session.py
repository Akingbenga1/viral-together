"""
Database session for Celery workers - minimal imports to avoid circular dependencies
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create a minimal database engine for Celery workers
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
