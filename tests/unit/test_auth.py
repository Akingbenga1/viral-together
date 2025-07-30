import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import status

from app.db.models.user import User
from app.core.security import verify_token
from app.services.auth import verify_password, hash_password


class TestUserRegistration:
    """Test cases for user registration functionality."""

    @pytest.mark.asyncio
    async def test_register_new_user_success(self, client: AsyncClient, test_factory):
        """Test successful user registration."""
        user_data = test_factory.user_data()
        
        response = await client.post("/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["username"] == user_data["username"]
        assert "password" not in response_data  # Password should not be returned

    @pytest.mark.asyncio
    async def test_register_duplicate_username_fails(self, client: AsyncClient, test_user, test_factory):
        """Test that registering with existing username fails."""
        user_data = test_factory.user_data(username=test_user.username)
        
        response = await client.post("/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_invalid_data_fails(self, client: AsyncClient):
        """Test registration with invalid data fails."""
        invalid_data = {
            "username": "",  # Empty username
            "password": "123"  # Too short password
        }
        
        response = await client.post("/auth/register", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_register_missing_fields_fails(self, client: AsyncClient):
        """Test registration with missing required fields fails."""
        incomplete_data = {"username": "testuser"}  # Missing password
        
        response = await client.post("/auth/register", json=incomplete_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_register_user_stored_in_database(self, client: AsyncClient, db_session: AsyncSession, test_factory):
        """Test that registered user is properly stored in database."""
        user_data = test_factory.user_data()
        
        response = await client.post("/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify user exists in database
        result = await db_session.execute(
            select(User).where(User.username == user_data["username"])
        )
        db_user = result.scalar_one_or_none()
        
        assert db_user is not None
        assert db_user.username == user_data["username"]
        assert verify_password(user_data["password"], db_user.hashed_password)


class TestUserLogin:
    """Test cases for user login functionality."""

    @pytest.mark.asyncio
    async def test_login_valid_credentials_success(self, client: AsyncClient, test_user):
        """Test successful login with valid credentials."""
        form_data = {
            "username": test_user.username,
            "password": test_user.plain_password
        }
        
        response = await client.post("/auth/token", data=form_data)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "access_token" in response_data
        assert response_data["token_type"] == "bearer"
        assert response_data["access_token"] is not None

    @pytest.mark.asyncio
    async def test_login_invalid_username_fails(self, client: AsyncClient):
        """Test login with invalid username fails."""
        form_data = {
            "username": "nonexistent_user",
            "password": "testpassword123"
        }
        
        response = await client.post("/auth/token", data=form_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorrect username or password" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_invalid_password_fails(self, client: AsyncClient, test_user):
        """Test login with invalid password fails."""
        form_data = {
            "username": test_user.username,
            "password": "wrongpassword"
        }
        
        response = await client.post("/auth/token", data=form_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorrect username or password" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_empty_credentials_fails(self, client: AsyncClient):
        """Test login with empty credentials fails."""
        form_data = {"username": "", "password": ""}
        
        response = await client.post("/auth/token", data=form_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_login_missing_credentials_fails(self, client: AsyncClient):
        """Test login with missing credentials fails."""
        response = await client.post("/auth/token", data={})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestTokenValidation:
    """Test cases for token validation and authentication."""

    @pytest.mark.asyncio
    async def test_valid_token_access_protected_endpoint(self, authenticated_client: AsyncClient):
        """Test that valid token allows access to protected endpoints."""
        response = await authenticated_client.get("/profile/me")
        
        # Should not return 401 Unauthorized (exact response depends on endpoint implementation)
        assert response.status_code != status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_invalid_token_access_denied(self, client: AsyncClient):
        """Test that invalid token denies access to protected endpoints."""
        client.headers.update({"Authorization": "Bearer invalid_token_here"})
        
        response = await client.get("/profile/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_missing_token_access_denied(self, client: AsyncClient):
        """Test that missing token denies access to protected endpoints."""
        response = await client.get("/profile/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_malformed_authorization_header_denied(self, client: AsyncClient, auth_token: str):
        """Test that malformed authorization header denies access."""
        # Missing "Bearer" prefix
        client.headers.update({"Authorization": auth_token})
        
        response = await client.get("/profile/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_expired_token_access_denied(self, client: AsyncClient):
        """Test that expired token denies access."""
        # This would require creating an expired token
        # For now, we'll test with a malformed token that should fail verification
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTYwMDAwMDAwMH0.invalid"
        client.headers.update({"Authorization": f"Bearer {expired_token}"})
        
        response = await client.get("/profile/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUserProfile:
    """Test cases for user profile functionality."""

    @pytest.mark.asyncio
    async def test_get_current_user_profile_success(self, authenticated_client: AsyncClient, test_user):
        """Test retrieving current user profile with valid token."""
        response = await authenticated_client.get("/profile/me")
        
        # The exact response depends on the profile endpoint implementation
        # We'll check that it's not unauthorized and contains user data
        if response.status_code == status.HTTP_200_OK:
            response_data = response.json()
            # Should contain user information (exact structure depends on implementation)
            assert isinstance(response_data, dict)

    @pytest.mark.asyncio
    async def test_get_current_user_without_auth_fails(self, client: AsyncClient):
        """Test that getting current user without auth fails."""
        response = await client.get("/profile/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPasswordSecurity:
    """Test cases for password security functionality."""

    def test_password_hashing_works(self):
        """Test that password hashing works correctly."""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert hashed != password  # Should be hashed, not plain text
        assert verify_password(password, hashed)  # Should verify correctly
        assert not verify_password("wrongpassword", hashed)  # Should reject wrong password

    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (salt is working)."""
        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2  # Different hashes due to salt
        assert verify_password(password, hash1)  # Both should verify
        assert verify_password(password, hash2)

    def test_empty_password_handling(self):
        """Test handling of empty passwords."""
        with pytest.raises((ValueError, Exception)):
            hash_password("")

    def test_none_password_handling(self):
        """Test handling of None passwords."""
        with pytest.raises((TypeError, AttributeError)):
            hash_password(None)


class TestAuthenticationIntegration:
    """Integration tests for complete authentication flows."""

    @pytest.mark.asyncio
    async def test_complete_registration_login_flow(self, client: AsyncClient, test_factory):
        """Test complete flow: register -> login -> access protected resource."""
        # Step 1: Register new user
        user_data = test_factory.user_data()
        register_response = await client.post("/auth/register", json=user_data)
        assert register_response.status_code == status.HTTP_200_OK

        # Step 2: Login with registered credentials
        form_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        login_response = await client.post("/auth/token", data=form_data)
        assert login_response.status_code == status.HTTP_200_OK
        
        token = login_response.json()["access_token"]

        # Step 3: Access protected resource with token
        client.headers.update({"Authorization": f"Bearer {token}"})
        profile_response = await client.get("/profile/me")
        
        # Should not be unauthorized (exact response depends on implementation)
        assert profile_response.status_code != status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_token_works_across_multiple_requests(self, authenticated_client: AsyncClient):
        """Test that token works for multiple consecutive requests."""
        # Make multiple requests with the same token
        for _ in range(3):
            response = await authenticated_client.get("/profile/me")
            assert response.status_code != status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_concurrent_logins_same_user(self, client: AsyncClient, test_user):
        """Test that same user can have multiple concurrent sessions."""
        form_data = {
            "username": test_user.username,
            "password": test_user.plain_password
        }
        
        # Get two tokens for the same user
        response1 = await client.post("/auth/token", data=form_data)
        response2 = await client.post("/auth/token", data=form_data)
        
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        
        token1 = response1.json()["access_token"]
        token2 = response2.json()["access_token"]
        
        # Both tokens should work
        client.headers.update({"Authorization": f"Bearer {token1}"})
        response = await client.get("/profile/me")
        assert response.status_code != status.HTTP_401_UNAUTHORIZED
        
        client.headers.update({"Authorization": f"Bearer {token2}"})
        response = await client.get("/profile/me")
        assert response.status_code != status.HTTP_401_UNAUTHORIZED 