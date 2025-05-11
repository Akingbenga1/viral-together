from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from typing import AsyncGenerator

# Create async engine for PostgreSQL
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Create async session
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Dependency for getting DB session in routes
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
