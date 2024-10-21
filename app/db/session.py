from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create async engine for PostgreSQL
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Create async session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

# Dependency for getting DB session in routes
async def get_db():
    async with SessionLocal() as session:
        yield session
