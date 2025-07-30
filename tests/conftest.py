import asyncio
import os
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import AsyncClient
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.main import app
from app.db.session import get_db
from app.core.security import create_access_token
from app.services.auth import hash_password

# Test database configuration
SQLALCHEMY_TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///./test.db")
SYNC_SQLALCHEMY_TEST_DATABASE_URL = SQLALCHEMY_TEST_DATABASE_URL.replace("+aiosqlite", "")

# Alembic configuration
alembic_cfg = Config("alembic.ini")
alembic_cfg.set_main_option("script_location", "alembic")
alembic_cfg.set_main_option("sqlalchemy.url", SYNC_SQLALCHEMY_TEST_DATABASE_URL)

# Create test engine with proper configuration
test_engine = create_async_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    future=True,
    echo=False,  # Set to True for SQL debugging
    poolclass=StaticPool,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_TEST_DATABASE_URL else {}
)

# Create sync engine for Alembic
sync_engine = create_engine(SYNC_SQLALCHEMY_TEST_DATABASE_URL)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Override the get_db dependency
async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function", autouse=True)
def setup_test_database():
    """Set up and tear down test database for each test."""
    # Run migrations
    command.upgrade(alembic_cfg, "head")
    yield
    # Clean up is handled by the reset_database fixture

@pytest.fixture
def faker_instance():
    """Provide a Faker instance for generating test data."""
    return Faker()

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for tests."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()

@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for API testing."""
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac

@pytest_asyncio.fixture(scope="function", autouse=True)
async def reset_database():
    """Reset database state between tests."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, faker_instance: Faker):
    """Create a test user for authentication tests."""
    from app.db.models.user import User
    
    user_data = {
        "username": faker_instance.user_name(),
        "first_name": faker_instance.first_name(),
        "last_name": faker_instance.last_name(),
        "email": faker_instance.email(),
        "hashed_password": hash_password("testpassword123")
    }
    
    user = User(**user_data)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Add plain password for testing
    user.plain_password = "testpassword123"
    return user

@pytest_asyncio.fixture
async def auth_token(test_user):
    """Generate an authentication token for the test user."""
    return create_access_token(data={"sub": test_user.username})

@pytest_asyncio.fixture
async def authenticated_client(client: AsyncClient, auth_token: str) -> AsyncClient:
    """Provide an authenticated HTTP client."""
    client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return client

@pytest_asyncio.fixture
async def test_business(db_session: AsyncSession, test_user, faker_instance: Faker):
    """Create a test business entity."""
    from app.db.models.business import Business
    
    business_data = {
        "business_name": faker_instance.company(),
        "business_email": faker_instance.email(),
        "business_phone": faker_instance.phone_number(),
        "business_address": faker_instance.address(),
        "business_description": faker_instance.text(max_nb_chars=200),
        "user_id": test_user.id
    }
    
    business = Business(**business_data)
    db_session.add(business)
    await db_session.commit()
    await db_session.refresh(business)
    return business

@pytest_asyncio.fixture
async def test_influencer(db_session: AsyncSession, test_user, faker_instance: Faker):
    """Create a test influencer entity."""
    from app.db.models.influencer import Influencer
    
    influencer_data = {
        "bio": faker_instance.text(max_nb_chars=200),
        "profile_image_url": faker_instance.url(),
        "website_url": faker_instance.url(),
        "location": faker_instance.city(),
        "languages": "English",
        "availability": True,
        "rate_per_post": faker_instance.random_int(min=50, max=1000),
        "total_posts": faker_instance.random_int(min=10, max=1000),
        "growth_rate": faker_instance.random_int(min=1, max=50),
        "successful_campaigns": faker_instance.random_int(min=0, max=100),
        "user_id": test_user.id
    }
    
    influencer = Influencer(**influencer_data)
    db_session.add(influencer)
    await db_session.commit()
    await db_session.refresh(influencer)
    return influencer

# Test data factories
class TestDataFactory:
    """Factory class for creating test data."""
    
    def __init__(self, faker_instance: Faker):
        self.faker = faker_instance
    
    def user_data(self, **overrides):
        """Generate user data."""
        data = {
            "username": self.faker.user_name(),
            "first_name": self.faker.first_name(),
            "last_name": self.faker.last_name(),
            "email": self.faker.email(),
            "password": "testpassword123"
        }
        data.update(overrides)
        return data
    
    def business_data(self, user_id: int, **overrides):
        """Generate business data."""
        data = {
            "business_name": self.faker.company(),
            "business_email": self.faker.email(),
            "business_phone": self.faker.phone_number(),
            "business_address": self.faker.address(),
            "business_description": self.faker.text(max_nb_chars=200),
            "user_id": user_id
        }
        data.update(overrides)
        return data
    
    def influencer_data(self, user_id: int, **overrides):
        """Generate influencer data."""
        data = {
            "bio": self.faker.text(max_nb_chars=200),
            "profile_image_url": self.faker.url(),
            "website_url": self.faker.url(),
            "location": self.faker.city(),
            "languages": "English",
            "availability": True,
            "rate_per_post": self.faker.random_int(min=50, max=1000),
            "total_posts": self.faker.random_int(min=10, max=1000),
            "growth_rate": self.faker.random_int(min=1, max=50),
            "successful_campaigns": self.faker.random_int(min=0, max=100),
            "user_id": user_id
        }
        data.update(overrides)
        return data
    
    def promotion_data(self, business_id: int, **overrides):
        """Generate promotion data."""
        data = {
            "title": self.faker.sentence(nb_words=4),
            "description": self.faker.text(max_nb_chars=500),
            "budget": self.faker.random_int(min=100, max=10000),
            "start_date": self.faker.future_date(),
            "end_date": self.faker.future_date(),
            "business_id": business_id
        }
        data.update(overrides)
        return data

@pytest.fixture
def test_factory(faker_instance: Faker):
    """Provide a test data factory instance."""
    return TestDataFactory(faker_instance) 