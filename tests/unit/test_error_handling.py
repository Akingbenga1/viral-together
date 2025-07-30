import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
import json


class TestAuthenticationErrors:
    """Test cases for authentication-related error handling."""

    @pytest.mark.asyncio
    async def test_malformed_json_request(self, client: AsyncClient):
        """Test handling of malformed JSON in requests."""
        malformed_json = '{"username": "test", "password": incomplete'
        
        response = await client.post(
            "/auth/register",
            content=malformed_json,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_empty_request_body(self, client: AsyncClient):
        """Test handling of empty request body."""
        response = await client.post("/auth/register", json={})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_null_values_in_request(self, client: AsyncClient):
        """Test handling of null values in request fields."""
        null_data = {
            "username": None,
            "password": None,
            "first_name": None,
            "last_name": None
        }
        
        response = await client.post("/auth/register", json=null_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_oversized_request_payload(self, client: AsyncClient):
        """Test handling of oversized request payloads."""
        oversized_data = {
            "username": "testuser",
            "password": "testpass",
            "first_name": "A" * 10000,  # Very long string
            "last_name": "B" * 10000
        }
        
        response = await client.post("/auth/register", json=oversized_data)
        
        # Should either reject due to size or validation
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        ]

    @pytest.mark.asyncio
    async def test_special_characters_in_credentials(self, client: AsyncClient):
        """Test handling of special characters in credentials."""
        special_char_data = {
            "username": "test<script>alert('xss')</script>",
            "password": "pass'OR'1'='1",
            "first_name": "John",
            "last_name": "Doe"
        }
        
        response = await client.post("/auth/register", json=special_char_data)
        
        # Should handle special characters gracefully
        if response.status_code == status.HTTP_200_OK:
            # If successful, verify no XSS or injection occurred
            response_data = response.json()
            assert "<script>" not in response_data.get("username", "")

    @pytest.mark.asyncio
    async def test_unicode_characters_in_credentials(self, client: AsyncClient):
        """Test handling of Unicode characters in credentials."""
        unicode_data = {
            "username": "用户名",  # Chinese characters
            "password": "пароль123",  # Cyrillic characters
            "first_name": "José",  # Accented characters
            "last_name": "Müller"  # German umlaut
        }
        
        response = await client.post("/auth/register", json=unicode_data)
        
        # Should handle Unicode gracefully
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]


class TestDatabaseErrors:
    """Test cases for database-related error handling."""

    @pytest.mark.asyncio
    async def test_concurrent_user_creation(self, client: AsyncClient, test_factory):
        """Test handling of concurrent user creation with same username."""
        user_data = test_factory.user_data()
        
        # Simulate concurrent requests (in real scenario, these would be truly concurrent)
        response1 = await client.post("/auth/register", json=user_data)
        response2 = await client.post("/auth/register", json=user_data)
        
        # One should succeed, one should fail
        responses = [response1, response2]
        success_count = sum(1 for r in responses if r.status_code == status.HTTP_200_OK)
        error_count = sum(1 for r in responses if r.status_code == status.HTTP_400_BAD_REQUEST)
        
        assert success_count == 1
        assert error_count == 1

    @pytest.mark.asyncio
    async def test_database_constraint_violations(self, authenticated_client: AsyncClient, test_user):
        """Test handling of database constraint violations."""
        # Try to create business with invalid foreign key
        business_data = {
            "business_name": "Test Business",
            "business_email": "test@example.com",
            "user_id": 99999  # Non-existent user ID
        }
        
        response = await authenticated_client.post("/business/create", json=business_data)
        
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    @pytest.mark.asyncio
    async def test_sql_injection_attempts(self, client: AsyncClient):
        """Test protection against SQL injection attempts."""
        injection_attempts = [
            "'; DROP TABLE users; --",
            "admin'--",
            "' OR '1'='1",
            "'; INSERT INTO users (username) VALUES ('hacker'); --"
        ]
        
        for injection in injection_attempts:
            malicious_data = {
                "username": injection,
                "password": "testpass"
            }
            
            # Try registration
            register_response = await client.post("/auth/register", json=malicious_data)
            # Should not crash the application
            assert register_response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR
            
            # Try login
            login_response = await client.post("/auth/token", data=malicious_data)
            # Should not crash the application
            assert login_response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR


class TestValidationErrors:
    """Test cases for input validation error handling."""

    @pytest.mark.asyncio
    async def test_email_format_validation(self, authenticated_client: AsyncClient, test_user):
        """Test email format validation in various contexts."""
        invalid_emails = [
            "",
            "notanemail",
            "@domain.com",
            "user@",
            "user@domain",
            "user..double.dot@domain.com",
            "user@domain..com",
            "user name@domain.com",  # Space in email
            "user@domain.com.",  # Trailing dot
            "user@.domain.com",  # Leading dot in domain
        ]
        
        for invalid_email in invalid_emails:
            business_data = {
                "business_name": "Test Business",
                "business_email": invalid_email,
                "user_id": test_user.id
            }
            
            response = await authenticated_client.post("/business/create", json=business_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_numeric_field_validation(self, authenticated_client: AsyncClient, test_influencer):
        """Test numeric field validation."""
        invalid_numbers = [
            "not_a_number",
            "",
            None,
            float('inf'),
            float('-inf'),
            -1,  # Negative where positive expected
            0,   # Zero where positive expected
        ]
        
        for invalid_number in invalid_numbers:
            try:
                rate_card_data = {
                    "platform": "Instagram",
                    "content_type": "Post",
                    "rate": invalid_number,
                    "influencer_id": test_influencer.id
                }
                
                response = await authenticated_client.post("/rate_card/create", json=rate_card_data)
                assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            except (TypeError, ValueError):
                # JSON serialization might fail for some values, which is also valid error handling
                pass

    @pytest.mark.asyncio
    async def test_date_format_validation(self, authenticated_client: AsyncClient, test_business):
        """Test date format validation."""
        invalid_dates = [
            "not_a_date",
            "2023-13-01",  # Invalid month
            "2023-02-30",  # Invalid day
            "2023/02/01",  # Wrong format
            "01-02-2023",  # Wrong format
            "",
            None
        ]
        
        for invalid_date in invalid_dates:
            try:
                promotion_data = {
                    "title": "Test Promotion",
                    "description": "Test description",
                    "budget": 1000,
                    "start_date": invalid_date,
                    "end_date": "2024-12-31",
                    "business_id": test_business.id
                }
                
                response = await authenticated_client.post("/promotion/create", json=promotion_data)
                assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            except (TypeError, ValueError):
                # JSON serialization might fail, which is also valid
                pass

    @pytest.mark.asyncio
    async def test_string_length_validation(self, authenticated_client: AsyncClient, test_user):
        """Test string length validation."""
        # Test very long strings
        very_long_string = "A" * 10000
        
        business_data = {
            "business_name": very_long_string,
            "business_email": "test@example.com",
            "business_description": very_long_string,
            "user_id": test_user.id
        }
        
        response = await authenticated_client.post("/business/create", json=business_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_required_field_validation(self, authenticated_client: AsyncClient):
        """Test validation of required fields."""
        # Test with missing required fields
        incomplete_data_sets = [
            {},  # All fields missing
            {"business_name": "Test"},  # Some fields missing
            {"business_email": "test@example.com"},  # Different fields missing
        ]
        
        for incomplete_data in incomplete_data_sets:
            response = await authenticated_client.post("/business/create", json=incomplete_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestResourceNotFoundErrors:
    """Test cases for resource not found error handling."""

    @pytest.mark.asyncio
    async def test_nonexistent_resource_access(self, authenticated_client: AsyncClient):
        """Test accessing nonexistent resources."""
        nonexistent_ids = [99999, -1, 0]
        
        endpoints = [
            "/business/{}",
            "/influencer/get_influencer/{}",
            "/rate_card/{}",
            "/promotion/{}",
            "/collaboration/{}"
        ]
        
        for endpoint_template in endpoints:
            for resource_id in nonexistent_ids:
                endpoint = endpoint_template.format(resource_id)
                response = await authenticated_client.get(endpoint)
                
                assert response.status_code in [
                    status.HTTP_404_NOT_FOUND,
                    status.HTTP_422_UNPROCESSABLE_ENTITY  # For invalid ID formats
                ]

    @pytest.mark.asyncio
    async def test_invalid_resource_id_formats(self, authenticated_client: AsyncClient):
        """Test handling of invalid resource ID formats."""
        invalid_ids = ["abc", "12.34", "null", "undefined", ""]
        
        endpoints = [
            "/business/{}",
            "/influencer/get_influencer/{}",
            "/rate_card/{}"
        ]
        
        for endpoint_template in endpoints:
            for invalid_id in invalid_ids:
                endpoint = endpoint_template.format(invalid_id)
                response = await authenticated_client.get(endpoint)
                
                assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_deleted_resource_access(self, authenticated_client: AsyncClient, db_session: AsyncSession, test_business):
        """Test accessing resources that have been deleted."""
        business_id = test_business.id
        
        # Delete the business
        delete_response = await authenticated_client.delete(f"/business/delete/{business_id}")
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
        
        # Try to access the deleted business
        get_response = await authenticated_client.get(f"/business/{business_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
        
        # Try to update the deleted business
        update_response = await authenticated_client.put(
            f"/business/update/{business_id}",
            json={"business_name": "Updated Name"}
        )
        assert update_response.status_code == status.HTTP_404_NOT_FOUND


class TestAuthorizationErrors:
    """Test cases for authorization-related error handling."""

    @pytest.mark.asyncio
    async def test_cross_user_resource_access(self, client: AsyncClient, test_factory):
        """Test that users cannot access other users' resources."""
        # Create two users
        user1_data = test_factory.user_data()
        user2_data = test_factory.user_data()
        
        await client.post("/auth/register", json=user1_data)
        await client.post("/auth/register", json=user2_data)
        
        # Login both users
        user1_login = await client.post("/auth/token", data={
            "username": user1_data["username"],
            "password": user1_data["password"]
        })
        user2_login = await client.post("/auth/token", data={
            "username": user2_data["username"],
            "password": user2_data["password"]
        })
        
        user1_token = user1_login.json()["access_token"]
        user2_token = user2_login.json()["access_token"]
        
        # User 1 creates a business
        client.headers.update({"Authorization": f"Bearer {user1_token}"})
        business_data = test_factory.business_data(user_id=1)
        business_response = await client.post("/business/create", json=business_data)
        business_id = business_response.json()["id"]
        
        # User 2 tries to access User 1's business
        client.headers.update({"Authorization": f"Bearer {user2_token}"})
        
        # Try to view
        view_response = await client.get(f"/business/{business_id}")
        assert view_response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]
        
        # Try to update
        update_response = await client.put(
            f"/business/update/{business_id}",
            json={"business_name": "Unauthorized Update"}
        )
        assert update_response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]
        
        # Try to delete
        delete_response = await client.delete(f"/business/delete/{business_id}")
        assert delete_response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]

    @pytest.mark.asyncio
    async def test_expired_token_handling(self, client: AsyncClient):
        """Test handling of expired authentication tokens."""
        # Use a clearly expired/invalid token
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0IiwiZXhwIjoxfQ.invalid"
        
        client.headers.update({"Authorization": f"Bearer {expired_token}"})
        
        protected_endpoints = [
            "/profile/me",
            "/business/create",
            "/influencer/create_influencer",
            "/rate_card/create"
        ]
        
        for endpoint in protected_endpoints:
            if "create" in endpoint:
                response = await client.post(endpoint, json={})
            else:
                response = await client.get(endpoint)
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_missing_permissions(self, authenticated_client: AsyncClient):
        """Test accessing endpoints that require specific permissions."""
        # Try to access admin-only endpoints (if they exist)
        admin_endpoints = [
            "/admin/users",
            "/admin/statistics",
            "/admin/system"
        ]
        
        for endpoint in admin_endpoints:
            response = await authenticated_client.get(endpoint)
            # Should return 403 Forbidden or 404 Not Found (if endpoint doesn't exist)
            assert response.status_code in [
                status.HTTP_403_FORBIDDEN,
                status.HTTP_404_NOT_FOUND
            ]


class TestRateLimitingErrors:
    """Test cases for rate limiting error handling."""

    @pytest.mark.asyncio
    async def test_rapid_successive_requests(self, client: AsyncClient, test_factory):
        """Test handling of rapid successive requests."""
        user_data = test_factory.user_data()
        
        # Make many rapid requests
        responses = []
        for i in range(50):  # Adjust number based on rate limits
            response = await client.post("/auth/register", json={
                **user_data,
                "username": f"{user_data['username']}{i}"
            })
            responses.append(response)
        
        # Should handle all requests gracefully (either succeed or rate limit)
        for response in responses:
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_429_TOO_MANY_REQUESTS,
                status.HTTP_422_UNPROCESSABLE_ENTITY  # Validation errors are also acceptable
            ]

    @pytest.mark.asyncio
    async def test_concurrent_database_operations(self, authenticated_client: AsyncClient, test_user, test_factory):
        """Test handling of concurrent database operations."""
        # Create multiple businesses concurrently (simulated)
        business_data = test_factory.business_data(user_id=test_user.id)
        
        responses = []
        for i in range(10):
            business_data_copy = {**business_data, "business_name": f"Business {i}"}
            response = await authenticated_client.post("/business/create", json=business_data_copy)
            responses.append(response)
        
        # All should either succeed or fail gracefully
        for response in responses:
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_429_TOO_MANY_REQUESTS
            ]


class TestSystemErrors:
    """Test cases for system-level error handling."""

    @pytest.mark.asyncio
    async def test_malformed_content_type(self, client: AsyncClient):
        """Test handling of malformed content-type headers."""
        response = await client.post(
            "/auth/register",
            content='{"username": "test", "password": "pass"}',
            headers={"Content-Type": "application/xml"}  # Wrong content type
        )
        
        assert response.status_code in [
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    @pytest.mark.asyncio
    async def test_missing_content_type(self, client: AsyncClient):
        """Test handling of missing content-type headers."""
        response = await client.post(
            "/auth/register",
            content='{"username": "test", "password": "pass"}'
            # No Content-Type header
        )
        
        # Should handle gracefully
        assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_unsupported_http_methods(self, client: AsyncClient):
        """Test handling of unsupported HTTP methods."""
        # Try unsupported methods on various endpoints
        endpoints = ["/auth/register", "/business/create", "/influencer/create_influencer"]
        
        for endpoint in endpoints:
            # Try PATCH on POST endpoint
            response = await client.request("PATCH", endpoint, json={})
            assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.mark.asyncio
    async def test_nonexistent_endpoints(self, client: AsyncClient):
        """Test accessing nonexistent endpoints."""
        nonexistent_endpoints = [
            "/nonexistent",
            "/api/v2/users",  # Wrong version
            "/auth/logout",   # If not implemented
            "/admin/secret"   # Admin endpoint
        ]
        
        for endpoint in nonexistent_endpoints:
            response = await client.get(endpoint)
            assert response.status_code == status.HTTP_404_NOT_FOUND 