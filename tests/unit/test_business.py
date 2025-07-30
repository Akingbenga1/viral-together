import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import status

from app.db.models.business import Business


class TestBusinessCreation:
    """Test cases for business creation functionality."""

    @pytest.mark.asyncio
    async def test_create_business_success(self, authenticated_client: AsyncClient, test_user, test_factory):
        """Test successful business creation."""
        business_data = test_factory.business_data(user_id=test_user.id)
        
        response = await authenticated_client.post("/business/create", json=business_data)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["business_name"] == business_data["business_name"]
        assert response_data["business_email"] == business_data["business_email"]
        assert response_data["user_id"] == test_user.id

    @pytest.mark.asyncio
    async def test_create_business_without_auth_fails(self, client: AsyncClient, test_factory):
        """Test that creating business without authentication fails."""
        business_data = test_factory.business_data(user_id=1)
        
        response = await client.post("/business/create", json=business_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_create_business_invalid_data_fails(self, authenticated_client: AsyncClient):
        """Test business creation with invalid data fails."""
        invalid_data = {
            "business_name": "",  # Empty name
            "business_email": "invalid-email",  # Invalid email format
            "user_id": "not_a_number"  # Invalid user ID
        }
        
        response = await authenticated_client.post("/business/create", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_business_missing_required_fields_fails(self, authenticated_client: AsyncClient):
        """Test business creation with missing required fields fails."""
        incomplete_data = {"business_name": "Test Business"}  # Missing other required fields
        
        response = await authenticated_client.post("/business/create", json=incomplete_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_business_stored_in_database(self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user, test_factory):
        """Test that created business is properly stored in database."""
        business_data = test_factory.business_data(user_id=test_user.id)
        
        response = await authenticated_client.post("/business/create", json=business_data)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify business exists in database
        result = await db_session.execute(
            select(Business).where(Business.business_name == business_data["business_name"])
        )
        db_business = result.scalar_one_or_none()
        
        assert db_business is not None
        assert db_business.business_name == business_data["business_name"]
        assert db_business.user_id == test_user.id


class TestBusinessRetrieval:
    """Test cases for business retrieval functionality."""

    @pytest.mark.asyncio
    async def test_get_business_by_id_success(self, authenticated_client: AsyncClient, test_business):
        """Test successful business retrieval by ID."""
        response = await authenticated_client.get(f"/business/{test_business.id}")
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["id"] == test_business.id
        assert response_data["business_name"] == test_business.business_name

    @pytest.mark.asyncio
    async def test_get_business_nonexistent_id_fails(self, authenticated_client: AsyncClient):
        """Test getting business with nonexistent ID fails."""
        nonexistent_id = 99999
        
        response = await authenticated_client.get(f"/business/{nonexistent_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_business_without_auth_fails(self, client: AsyncClient, test_business):
        """Test that getting business without authentication fails."""
        response = await client.get(f"/business/{test_business.id}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_business_invalid_id_fails(self, authenticated_client: AsyncClient):
        """Test getting business with invalid ID format fails."""
        invalid_id = "not_a_number"
        
        response = await authenticated_client.get(f"/business/{invalid_id}")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_list_user_businesses_success(self, authenticated_client: AsyncClient, test_business):
        """Test listing businesses for authenticated user."""
        response = await authenticated_client.get("/business/my-businesses")
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert isinstance(response_data, list)
        
        # Should contain the test business
        business_ids = [business["id"] for business in response_data]
        assert test_business.id in business_ids

    @pytest.mark.asyncio
    async def test_list_all_businesses_success(self, authenticated_client: AsyncClient, test_business):
        """Test listing all businesses."""
        response = await authenticated_client.get("/business/list")
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) >= 1  # Should contain at least our test business


class TestBusinessUpdate:
    """Test cases for business update functionality."""

    @pytest.mark.asyncio
    async def test_update_business_success(self, authenticated_client: AsyncClient, test_business, faker_instance):
        """Test successful business update."""
        update_data = {
            "business_name": faker_instance.company(),
            "business_description": faker_instance.text(max_nb_chars=200)
        }
        
        response = await authenticated_client.put(f"/business/update/{test_business.id}", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["business_name"] == update_data["business_name"]
        assert response_data["business_description"] == update_data["business_description"]

    @pytest.mark.asyncio
    async def test_update_business_nonexistent_fails(self, authenticated_client: AsyncClient, faker_instance):
        """Test updating nonexistent business fails."""
        nonexistent_id = 99999
        update_data = {"business_name": faker_instance.company()}
        
        response = await authenticated_client.put(f"/business/update/{nonexistent_id}", json=update_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_business_without_auth_fails(self, client: AsyncClient, test_business, faker_instance):
        """Test updating business without authentication fails."""
        update_data = {"business_name": faker_instance.company()}
        
        response = await client.put(f"/business/update/{test_business.id}", json=update_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_update_business_invalid_data_fails(self, authenticated_client: AsyncClient, test_business):
        """Test updating business with invalid data fails."""
        invalid_data = {
            "business_email": "invalid-email-format",
            "business_phone": ""  # Empty phone if required
        }
        
        response = await authenticated_client.put(f"/business/update/{test_business.id}", json=invalid_data)
        
        # Depending on validation, this might be 422 or 400
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]

    @pytest.mark.asyncio
    async def test_update_business_unauthorized_user_fails(self, client: AsyncClient, test_business, test_factory):
        """Test that user cannot update another user's business."""
        # Create another user and authenticate as them
        other_user_data = test_factory.user_data()
        register_response = await client.post("/auth/register", json=other_user_data)
        assert register_response.status_code == status.HTTP_200_OK
        
        # Login as the other user
        form_data = {
            "username": other_user_data["username"],
            "password": other_user_data["password"]
        }
        login_response = await client.post("/auth/token", data=form_data)
        token = login_response.json()["access_token"]
        
        # Try to update the original user's business
        client.headers.update({"Authorization": f"Bearer {token}"})
        update_data = {"business_name": "Unauthorized Update"}
        
        response = await client.put(f"/business/update/{test_business.id}", json=update_data)
        
        # Should fail with forbidden or not found
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


class TestBusinessDeletion:
    """Test cases for business deletion functionality."""

    @pytest.mark.asyncio
    async def test_delete_business_success(self, authenticated_client: AsyncClient, db_session: AsyncSession, test_business):
        """Test successful business deletion."""
        business_id = test_business.id
        
        response = await authenticated_client.delete(f"/business/delete/{business_id}")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify business is deleted from database
        result = await db_session.execute(select(Business).where(Business.id == business_id))
        deleted_business = result.scalar_one_or_none()
        assert deleted_business is None

    @pytest.mark.asyncio
    async def test_delete_business_nonexistent_fails(self, authenticated_client: AsyncClient):
        """Test deleting nonexistent business fails."""
        nonexistent_id = 99999
        
        response = await authenticated_client.delete(f"/business/delete/{nonexistent_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_business_without_auth_fails(self, client: AsyncClient, test_business):
        """Test deleting business without authentication fails."""
        response = await client.delete(f"/business/delete/{test_business.id}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_delete_business_unauthorized_user_fails(self, client: AsyncClient, test_business, test_factory):
        """Test that user cannot delete another user's business."""
        # Create and authenticate as another user
        other_user_data = test_factory.user_data()
        register_response = await client.post("/auth/register", json=other_user_data)
        assert register_response.status_code == status.HTTP_200_OK
        
        form_data = {
            "username": other_user_data["username"],
            "password": other_user_data["password"]
        }
        login_response = await client.post("/auth/token", data=form_data)
        token = login_response.json()["access_token"]
        
        # Try to delete the original user's business
        client.headers.update({"Authorization": f"Bearer {token}"})
        response = await client.delete(f"/business/delete/{test_business.id}")
        
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


class TestBusinessValidation:
    """Test cases for business data validation."""

    @pytest.mark.asyncio
    async def test_business_email_validation(self, authenticated_client: AsyncClient, test_user):
        """Test business email validation."""
        invalid_emails = ["", "invalid", "@domain.com", "user@", "user@.com"]
        
        for invalid_email in invalid_emails:
            business_data = {
                "business_name": "Test Business",
                "business_email": invalid_email,
                "user_id": test_user.id
            }
            
            response = await authenticated_client.post("/business/create", json=business_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_business_name_validation(self, authenticated_client: AsyncClient, test_user):
        """Test business name validation."""
        invalid_names = ["", " ", "a" * 256]  # Empty, whitespace, too long
        
        for invalid_name in invalid_names:
            business_data = {
                "business_name": invalid_name,
                "business_email": "test@example.com",
                "user_id": test_user.id
            }
            
            response = await authenticated_client.post("/business/create", json=business_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_business_phone_validation(self, authenticated_client: AsyncClient, test_user):
        """Test business phone validation if implemented."""
        business_data = {
            "business_name": "Test Business",
            "business_email": "test@example.com",
            "business_phone": "invalid-phone",
            "user_id": test_user.id
        }
        
        response = await authenticated_client.post("/business/create", json=business_data)
        
        # Depending on validation implementation, this might pass or fail
        # If phone validation is strict, it should fail
        if response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
            assert "phone" in response.json()["detail"][0]["loc"]


class TestBusinessSearch:
    """Test cases for business search functionality."""

    @pytest.mark.asyncio
    async def test_search_businesses_by_name(self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user, faker_instance):
        """Test searching businesses by name."""
        # Create businesses with specific names
        business1_data = {
            "business_name": "Tech Solutions Inc",
            "business_email": faker_instance.email(),
            "user_id": test_user.id
        }
        business2_data = {
            "business_name": "Marketing Agency Ltd",
            "business_email": faker_instance.email(),
            "user_id": test_user.id
        }
        
        # Create businesses
        await authenticated_client.post("/business/create", json=business1_data)
        await authenticated_client.post("/business/create", json=business2_data)
        
        # Search for "Tech" businesses
        response = await authenticated_client.get("/business/search?name=Tech")
        
        if response.status_code == status.HTTP_200_OK:
            response_data = response.json()
            assert isinstance(response_data, list)
            # Should find the Tech Solutions business
            business_names = [business["business_name"] for business in response_data]
            assert any("Tech" in name for name in business_names)

    @pytest.mark.asyncio
    async def test_search_businesses_no_results(self, authenticated_client: AsyncClient):
        """Test searching businesses with no matching results."""
        response = await authenticated_client.get("/business/search?name=NonexistentBusiness")
        
        if response.status_code == status.HTTP_200_OK:
            response_data = response.json()
            assert isinstance(response_data, list)
            assert len(response_data) == 0


class TestBusinessIntegration:
    """Integration tests for business-related workflows."""

    @pytest.mark.asyncio
    async def test_complete_business_lifecycle(self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user, test_factory):
        """Test complete business lifecycle: create -> read -> update -> delete."""
        # Step 1: Create business
        business_data = test_factory.business_data(user_id=test_user.id)
        create_response = await authenticated_client.post("/business/create", json=business_data)
        assert create_response.status_code == status.HTTP_200_OK
        business_id = create_response.json()["id"]

        # Step 2: Read business
        read_response = await authenticated_client.get(f"/business/{business_id}")
        assert read_response.status_code == status.HTTP_200_OK
        assert read_response.json()["business_name"] == business_data["business_name"]

        # Step 3: Update business
        update_data = {"business_name": "Updated Business Name"}
        update_response = await authenticated_client.put(f"/business/update/{business_id}", json=update_data)
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["business_name"] == update_data["business_name"]

        # Step 4: Delete business
        delete_response = await authenticated_client.delete(f"/business/delete/{business_id}")
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Step 5: Verify deletion
        verify_response = await authenticated_client.get(f"/business/{business_id}")
        assert verify_response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_multiple_businesses_per_user(self, authenticated_client: AsyncClient, test_user, test_factory):
        """Test that a user can have multiple businesses."""
        # Create multiple businesses
        business_count = 3
        created_businesses = []
        
        for i in range(business_count):
            business_data = test_factory.business_data(user_id=test_user.id)
            response = await authenticated_client.post("/business/create", json=business_data)
            assert response.status_code == status.HTTP_200_OK
            created_businesses.append(response.json())

        # List user's businesses
        list_response = await authenticated_client.get("/business/my-businesses")
        assert list_response.status_code == status.HTTP_200_OK
        
        user_businesses = list_response.json()
        assert len(user_businesses) >= business_count
        
        # Verify all created businesses are in the list
        created_ids = {business["id"] for business in created_businesses}
        listed_ids = {business["id"] for business in user_businesses}
        assert created_ids.issubset(listed_ids) 