import asyncio
import os
from typing import Generator

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import AsyncClient
from dotenv import load_dotenv
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text, create_engine, select

from app.db.base import Base
from app.db.models import Influencer
from app.main import app
from app.db.models.user import User
from app.core.security import create_access_token
from app.db.session import get_db, engine
from app.api.influencer.influencer import InfluencerCreate
from app.services import hash_password

# client = TestClient(app)

# Alembic configuration
alembic_cfg = Config("alembic.ini")  # Path to your alembic.ini file

# Test setup: create a user and retrieve a real token via async DB connection

# Use the test database URL
SQLALCHEMY_TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
SYNC_SQLALCHEMY_TEST_DATABASE_URL = SQLALCHEMY_TEST_DATABASE_URL.replace("+asyncpg", "")  # Synchronous URL


# Create a synchronous engine just for Alembic migrations
sync_engine = create_engine(SYNC_SQLALCHEMY_TEST_DATABASE_URL)

# Programmatically configure Alembic to use the test database URL
alembic_cfg.set_main_option("script_location", "alembic")
alembic_cfg.set_main_option("sqlalchemy.url", SYNC_SQLALCHEMY_TEST_DATABASE_URL)  # Set the test DB URL dynamically

# Create a new engine and session factory for the test database
test_engine = create_async_engine(SQLALCHEMY_TEST_DATABASE_URL, future=True, echo=True)


test_user = None
# Create an async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)



# Override the get_db dependency to yield the test database session
async def override_get_db():
    async with AsyncSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function", autouse=True)
def apply_migrations():
    """Synchronous fixture to run Alembic migrations using sync engine"""
    command.upgrade(alembic_cfg, "head")  # Run migrations synchronously before tests

@pytest.fixture(scope="session", autouse=True)
def event_loop() -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Fixture to provide an async client
@pytest_asyncio.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac

@pytest_asyncio.fixture(scope="function")
async def run_migrations_and_setup_db():
    """Fixture to run Alembic migrations and set up the test database"""
    # Run Alembic migrations to set up the test database schema
    # Ensure migrations are applied before entering async code
    # Yield the test session for the test
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()  # Ensure rollback after the test
        await session.close()

    # # Clean up by dropping the tables after the test
    # async with test_engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)
#
# # Reset the event loop between tests
# @pytest_asyncio.fixture(scope="function", autouse=True)
# def reset_event_loop():
#     loop = asyncio.get_event_loop()
#     yield
#     loop.run_until_complete(asyncio.sleep(0))
#     loop.close()
#     asyncio.set_event_loop(asyncio.new_event_loop())

# Create a pytest fixture for Faker

# @pytest_asyncio.fixture(scope="function", autouse=True)
# async def reset_event_loop():
#     """Fixture to reset the event loop between tests."""
#     loop = asyncio.get_event_loop()
#     yield
#     await asyncio.sleep(1)
#     # loop.close()  # Close the loop at the end of each test
#     asyncio.set_event_loop(asyncio.new_event_loop())  # Create a fresh event loop

@pytest.fixture
def faker():
    """Fixture to return a Faker instance."""
    return Faker()


@pytest.fixture
async def create_test_user(run_migrations_and_setup_db, faker):
    """Fixture to create a real user in the async test database"""
    new_user = {
        "username": faker.user_name(),
        "first_name": faker.first_name(),
        "last_name": faker.last_name(),
        "hashed_password": faker.password()  # Assume the password is hashed correctly
    }

    # Insert the user into the database asynchronously
    await run_migrations_and_setup_db.execute(
        text(
            "INSERT INTO users (username, hashed_password, first_name, last_name ) "
            "VALUES (:username, :hashed_password, :first_name, :last_name)"
        ),
        {
            "username": new_user["username"],
            "hashed_password": hash_password(new_user["hashed_password"]),
            "first_name": new_user["first_name"],
            "last_name": new_user["last_name"]
        }
    )
    await run_migrations_and_setup_db.commit()

    # Fetch the created user asynchronously
    result = await run_migrations_and_setup_db.execute(text(f"SELECT * FROM users WHERE username = '{ new_user["username"]}'"))
    user = result.fetchone()

    return User(username=user.username, id=user.id, first_name=user.first_name)


@pytest.fixture
async def generate_token(create_test_user):
    """Fixture to generate a real token for the test user"""
    global test_user
    test_user = await create_test_user
    access_token = create_access_token(data={"sub": test_user.username})
    return access_token


@pytest_asyncio.fixture(scope="function", autouse=True)
async def reset_database(run_migrations_and_setup_db: AsyncSession):
    """Fixture to drop and recreate the database schema before each test."""

    # Drop all tables
    async with run_migrations_and_setup_db.bind.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Recreate all tables
    async with run_migrations_and_setup_db.bind.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Commit the changes
    await run_migrations_and_setup_db.commit()
# Adjusted Tests using async sessions

### Unit Test for Creating an Influencer (with real authentication)
@pytest.mark.asyncio
async def test_create_influencer_with_real_user_and_token(client, run_migrations_and_setup_db, create_test_user):
    """Test case that creates an influencer using a real user and token"""

    global test_user
    test_user = await  create_test_user
    token =  create_access_token(data={"sub": test_user.username})

    # Arrange
    influencer_data = InfluencerCreate(
        bio="Bio of an influencer",
        profile_image_url="https://example.com/image.jpg",
        website_url="https://example.com",
        location="New York",
        languages="English",
        availability=True,
        rate_per_post=100.0,
        total_posts=10,
        growth_rate=20,
        successful_campaigns=5,
        user_id=test_user.id  # Assuming this will be set to the created user's ID
    )



    # Act: Make a request to create an influencer using the real token
    response = await client.post(
        "/influencer/create_influencer",
        json=influencer_data.model_dump(),
        headers={"Authorization": f"Bearer {token}"}
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["bio"] == influencer_data.bio
    assert response.json()["user_id"] == influencer_data.user_id

@pytest.mark.asyncio
async def test_get_influencer_by_id_with_real_user_and_token(client, run_migrations_and_setup_db, create_test_user):
    """Test case to get an influencer by ID using a real token"""

    # Arrange
    influencer = {"bio": "Test Bio"}

    global test_user
    test_user = await  create_test_user
    token =  create_access_token(data={"sub": test_user.username})

    # Insert influencer into the database
    result = await run_migrations_and_setup_db.execute(
        text("INSERT INTO influencers (bio, user_id, availability) VALUES (:bio, :user_id, :availability) RETURNING id"),
        {"bio": "Test Bio", "user_id": test_user.id, "availability": True}  # Assuming user_id is 1
    )
    influencer_id = result.scalar()
    await run_migrations_and_setup_db.commit()
    await run_migrations_and_setup_db.close()

    # Act: Make a request to get the influencer by ID using the real token
    response = await client.get(
        f"/influencer/get_influencer/{influencer_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["bio"] == "Test Bio"
    assert response.json()["user_id"] == test_user.id

@pytest.mark.asyncio
async def test_update_influencer_by_id_with_real_user_and_token(client, run_migrations_and_setup_db, create_test_user):
    """Test case to update an influencer by ID using a real token"""

    # Arrange
    global test_user
    test_user = await create_test_user
    token = create_access_token(data={"sub": test_user.username})

    # Insert influencer into the database
    result = await run_migrations_and_setup_db.execute(
        text("INSERT INTO influencers (bio, user_id, availability) VALUES (:bio, :user_id, :availability) RETURNING id"),
        {"bio": "Old Bio", "user_id": test_user.id, "availability": True}
    )
    influencer_id = result.scalar()
    await run_migrations_and_setup_db.commit()

    # Prepare updated influencer data
    update_data = {
        "bio": "Updated Bio",
        "availability": False
    }

    # Act: Make a request to update the influencer using the real token
    response = await client.put(
        f"/influencer/update_influencer/{influencer_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["bio"] == "Updated Bio"
    assert response.json()["availability"] is False
    assert response.json()["user_id"] == test_user.id

@pytest.mark.asyncio
async def test_delete_influencer_by_id_with_real_user_and_token(client, run_migrations_and_setup_db, create_test_user):
    """Test case to delete an influencer by ID using a real token"""

    # Arrange
    global test_user
    test_user = await create_test_user
    token = create_access_token(data={"sub": test_user.username})

    # Insert influencer into the database
    result = await run_migrations_and_setup_db.execute(
        text("INSERT INTO influencers (bio, user_id, availability) VALUES (:bio, :user_id, :availability) RETURNING id"),
        {"bio": "To be deleted", "user_id": test_user.id, "availability": True}
    )
    influencer_id = result.scalar()
    await run_migrations_and_setup_db.commit()

    # Act: Make a request to delete the influencer using the real token
    response = await client.delete(
        f"/influencer/remove_influencer/{influencer_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Assert
    assert response.status_code == 204

    # Verify that the influencer is no longer in the database
    result = await run_migrations_and_setup_db.execute(
        text("SELECT * FROM influencers WHERE id = :influencer_id"),
        {"influencer_id": influencer_id}
    )
    deleted_influencer = result.fetchone()
    assert deleted_influencer is None


@pytest.mark.asyncio
async def test_list_all_influencers_with_real_user_and_token(client, run_migrations_and_setup_db, create_test_user):
    """Test case to list all influencers using a real token"""

    # Arrange
    global test_user
    test_user = await create_test_user
    token = create_access_token(data={"sub": test_user.username})

    # Insert a couple of influencers into the database
    await run_migrations_and_setup_db.execute(
        text("INSERT INTO influencers (bio, user_id, availability) VALUES (:bio, :user_id, :availability)"),
        {"bio": "Influencer 1", "user_id": test_user.id, "availability": True}
    )
    await run_migrations_and_setup_db.execute(
        text("INSERT INTO influencers (bio, user_id, availability) VALUES (:bio, :user_id, :availability)"),
        {"bio": "Influencer 2", "user_id": test_user.id, "availability": True}
    )
    await run_migrations_and_setup_db.commit()

    # Act: Make a request to list all influencers using the real token
    response = await client.get(
        "/influencer/list",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Assert
    assert response.status_code == 200
    assert len(response.json()) >= 2  # There should be at least 2 influencers
    assert response.json()[0]["bio"] == "Influencer 1"
    assert response.json()[1]["bio"] == "Influencer 2"


@pytest.mark.asyncio
async def test_set_influencer_availability(client, run_migrations_and_setup_db, create_test_user):
    """Test case to set an influencer's availability using a real token"""

    global test_user
    test_user = await create_test_user
    token = create_access_token(data={"sub": test_user.username})

    # Insert an influencer into the database
    result = await run_migrations_and_setup_db.execute(
        text(
            "INSERT INTO influencers (bio, user_id, availability) VALUES (:bio, :user_id, :availability) RETURNING id"),
        {"bio": "Influencer Bio Gbenga", "user_id": test_user.id, "availability": True}
    )
    influencer_id = result.scalar()
    print("influencer_id availabilty", influencer_id)
    await run_migrations_and_setup_db.commit()

    # Act: Set the influencer's availability to False
    response = await client.put(
        f"/influencer/set_availability/{influencer_id}/False",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["availability"] is False


import os
from fastapi.datastructures import UploadFile


@pytest.mark.asyncio
@pytest.mark.skip(reason="Skipping this test for now")
async def test_update_influencer_profile_picture(client, run_migrations_and_setup_db, create_test_user, tmpdir):
    """Test case to update an influencer's profile picture using a real token"""

    global test_user
    test_user = await create_test_user
    token = create_access_token(data={"sub": test_user.username})

    # Set the directory for file uploads
    UPLOAD_DIRECTORY = tmpdir.mkdir("uploads")

    # Insert an influencer into the database
    result = await run_migrations_and_setup_db.execute(
        text(
            "INSERT INTO influencers (bio, user_id, availability) VALUES (:bio, :user_id, :availability) RETURNING id"),
        {"bio": "Influencer Bio", "user_id": test_user.id, "availability": True}
    )
    influencer_id = result.scalar()
    await run_migrations_and_setup_db.commit()

    # Prepare a fake profile picture file
    file_path = os.path.join(UPLOAD_DIRECTORY, "test_image.jpg")
    with open(file_path, "wb") as f:
        f.write(b"fake image content")

    file = UploadFile(file_path)

    # Act: Update the influencer's profile picture
    response = await client.put(
        f"/influencer/update_profile_picture/{influencer_id}",
        files={"file": file},
        headers={"Authorization": f"Bearer {token}"}
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["profile_image_url"] is not None


@pytest.mark.asyncio
async def test_get_all_available_influencers(client, run_migrations_and_setup_db, create_test_user):
    """Test case to get all available influencers using a real token"""

    global test_user
    test_user = await create_test_user
    token = create_access_token(data={"sub": test_user.username})

    # Insert available and unavailable influencers into the database
    await run_migrations_and_setup_db.execute(
        text("INSERT INTO influencers (bio, user_id, availability) VALUES (:bio, :user_id, :availability)"),
        {"bio": "Available Influencer", "user_id": test_user.id, "availability": True}
    )
    await run_migrations_and_setup_db.execute(
        text("INSERT INTO influencers (bio, user_id, availability) VALUES (:bio, :user_id, :availability)"),
        {"bio": "Unavailable Influencer", "user_id": test_user.id, "availability": False}
    )
    await run_migrations_and_setup_db.commit()

    # Act: Get all available influencers
    response = await client.get(
        "/influencer/influencers/available",
        headers={"Authorization": f"Bearer {token}"}
    )

    print("response_result", response)
    # Assert
    assert response.status_code == 200
    assert len(response.json()) == 1  # Only the available influencer should be returned
    assert response.json()[0]["bio"] == "Available Influencer"


@pytest.mark.asyncio
async def test_search_influencers_by_location(client, run_migrations_and_setup_db, create_test_user):
    """Test case to search influencers by location using a real token"""

    global test_user
    test_user = await create_test_user
    token = create_access_token(data={"sub": test_user.username})

    # Insert influencers with different locations
    await run_migrations_and_setup_db.execute(
        text("INSERT INTO influencers (bio, user_id, location, availability) VALUES (:bio, :user_id, :location, :availability)"),
        {"bio": "NY Influencer", "user_id": test_user.id, "location": "New York", "availability": True}
    )
    await run_migrations_and_setup_db.execute(
        text("INSERT INTO influencers (bio, user_id, location, availability) VALUES (:bio, :user_id, :location, :availability)"),
        {"bio": "LA Influencer", "user_id": test_user.id, "location": "Los Angeles", "availability": True}
    )
    await run_migrations_and_setup_db.commit()

    # Act: Search for influencers by location
    response = await client.get(
        "/influencer/search/New York",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Assert
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["location"] == "New York"


@pytest.mark.asyncio
async def test_search_influencers_by_language(client, run_migrations_and_setup_db, create_test_user):
    """Test case to search influencers by language using a real token"""

    global test_user
    test_user = await create_test_user
    token = create_access_token(data={"sub": test_user.username})

    # Insert influencers with different languages
    await run_migrations_and_setup_db.execute(
        text("INSERT INTO influencers (bio, user_id, languages, availability) VALUES (:bio, :user_id, :languages,:availability)"),
        {"bio": "English Speaker", "user_id": test_user.id, "languages": "English", "availability": True}
    )
    await run_migrations_and_setup_db.execute(
        text("INSERT INTO influencers (bio, user_id, languages, availability) VALUES (:bio, :user_id, :languages, :availability)"),
        {"bio": "Spanish Speaker", "user_id": test_user.id, "languages": "Spanish", "availability": True}
    )
    await run_migrations_and_setup_db.commit()

    # Act: Search for influencers by language
    response = await client.get(
        "/influencer/search_by_language/English",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Assert
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["languages"] == "English"
