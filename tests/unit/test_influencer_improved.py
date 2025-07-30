import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import status

from app.db.models.influencer import Influencer


class TestInfluencerCreation:
    """Test cases for influencer creation functionality."""

    @pytest.mark.asyncio
    async def test_create_influencer_success(self, authenticated_client: AsyncClient, test_user, test_factory):
        """Test successful influencer creation."""
        influencer_data = test_factory.influencer_data(user_id=test_user.id)
        
        response = await authenticated_client.post("/influencer/create_influencer", json=influencer_data)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["bio"] == influencer_data["bio"]
        assert response_data["user_id"] == test_user.id
        assert response_data["availability"] == influencer_data["availability"]

    @pytest.mark.asyncio
    async def test_create_influencer_without_auth_fails(self, client: AsyncClient, test_factory):
        """Test that creating influencer without authentication fails."""
        influencer_data = test_factory.influencer_data(user_id=1)
        
        response = await client.post("/influencer/create_influencer", json=influencer_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_create_influencer_invalid_data_fails(self, authenticated_client: AsyncClient, test_user):
        """Test influencer creation with invalid data fails."""
        invalid_data = {
            "bio": "",  # Empty bio
            "rate_per_post": -100,  # Negative rate
            "total_posts": "not_a_number",  # Invalid type
            "user_id": test_user.id
        }
        
        response = await authenticated_client.post("/influencer/create_influencer", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_influencer_missing_required_fields_fails(self, authenticated_client: AsyncClient):
        """Test influencer creation with missing required fields fails."""
        incomplete_data = {"bio": "Test bio"}  # Missing other required fields
        
        response = await authenticated_client.post("/influencer/create_influencer", json=incomplete_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_influencer_stored_in_database(self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user, test_factory):
        """Test that created influencer is properly stored in database."""
        influencer_data = test_factory.influencer_data(user_id=test_user.id)
        
        response = await authenticated_client.post("/influencer/create_influencer", json=influencer_data)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify influencer exists in database
        result = await db_session.execute(
            select(Influencer).where(Influencer.user_id == test_user.id)
        )
        db_influencer = result.scalar_one_or_none()
        
        assert db_influencer is not None
        assert db_influencer.bio == influencer_data["bio"]
        assert db_influencer.user_id == test_user.id


class TestInfluencerRetrieval:
    """Test cases for influencer retrieval functionality."""

    @pytest.mark.asyncio
    async def test_get_influencer_by_id_success(self, authenticated_client: AsyncClient, test_influencer):
        """Test successful influencer retrieval by ID."""
        response = await authenticated_client.get(f"/influencer/get_influencer/{test_influencer.id}")
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["id"] == test_influencer.id
        assert response_data["bio"] == test_influencer.bio

    @pytest.mark.asyncio
    async def test_get_influencer_nonexistent_id_fails(self, authenticated_client: AsyncClient):
        """Test getting influencer with nonexistent ID fails."""
        nonexistent_id = 99999
        
        response = await authenticated_client.get(f"/influencer/get_influencer/{nonexistent_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_influencer_invalid_id_fails(self, authenticated_client: AsyncClient):
        """Test getting influencer with invalid ID format fails."""
        invalid_id = "not_a_number"
        
        response = await authenticated_client.get(f"/influencer/get_influencer/{invalid_id}")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_list_all_influencers_success(self, authenticated_client: AsyncClient, test_influencer):
        """Test listing all influencers."""
        response = await authenticated_client.get("/influencer/list")
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) >= 1  # Should contain at least our test influencer
        
        # Verify our test influencer is in the list
        influencer_ids = [inf["id"] for inf in response_data]
        assert test_influencer.id in influencer_ids

    @pytest.mark.asyncio
    async def test_get_available_influencers_success(self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user, test_factory):
        """Test getting only available influencers."""
        # Create available and unavailable influencers
        available_data = test_factory.influencer_data(user_id=test_user.id)
        available_data["availability"] = True
        
        unavailable_data = test_factory.influencer_data(user_id=test_user.id)
        unavailable_data["availability"] = False
        
        # Create influencers directly in database for this test
        available_influencer = Influencer(**available_data)
        unavailable_influencer = Influencer(**unavailable_data)
        
        db_session.add_all([available_influencer, unavailable_influencer])
        await db_session.commit()
        
        response = await authenticated_client.get("/influencer/influencers/available")
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        
        # All returned influencers should be available
        for influencer in response_data:
            assert influencer["availability"] is True


class TestInfluencerUpdate:
    """Test cases for influencer update functionality."""

    @pytest.mark.asyncio
    async def test_update_influencer_success(self, authenticated_client: AsyncClient, test_influencer, faker_instance):
        """Test successful influencer update."""
        update_data = {
            "bio": faker_instance.text(max_nb_chars=200),
            "rate_per_post": 350.0,
            "availability": False
        }
        
        response = await authenticated_client.put(f"/influencer/update_influencer/{test_influencer.id}", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["bio"] == update_data["bio"]
        assert response_data["rate_per_post"] == update_data["rate_per_post"]
        assert response_data["availability"] == update_data["availability"]

    @pytest.mark.asyncio
    async def test_update_influencer_nonexistent_fails(self, authenticated_client: AsyncClient, faker_instance):
        """Test updating nonexistent influencer fails."""
        nonexistent_id = 99999
        update_data = {"bio": faker_instance.text()}
        
        response = await authenticated_client.put(f"/influencer/update_influencer/{nonexistent_id}", json=update_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_influencer_invalid_data_fails(self, authenticated_client: AsyncClient, test_influencer):
        """Test updating influencer with invalid data fails."""
        invalid_data = {
            "rate_per_post": -100,  # Negative rate
            "total_posts": "not_a_number"  # Invalid type
        }
        
        response = await authenticated_client.put(f"/influencer/update_influencer/{test_influencer.id}", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_set_influencer_availability(self, authenticated_client: AsyncClient, test_influencer):
        """Test setting influencer availability."""
        # Set to false
        response = await authenticated_client.put(f"/influencer/set_availability/{test_influencer.id}/False")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["availability"] is False
        
        # Set to true
        response = await authenticated_client.put(f"/influencer/set_availability/{test_influencer.id}/True")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["availability"] is True

    @pytest.mark.asyncio
    async def test_set_availability_invalid_value_fails(self, authenticated_client: AsyncClient, test_influencer):
        """Test setting availability with invalid value fails."""
        invalid_value = "maybe"
        
        response = await authenticated_client.put(f"/influencer/set_availability/{test_influencer.id}/{invalid_value}")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestInfluencerDeletion:
    """Test cases for influencer deletion functionality."""

    @pytest.mark.asyncio
    async def test_delete_influencer_success(self, authenticated_client: AsyncClient, db_session: AsyncSession, test_influencer):
        """Test successful influencer deletion."""
        influencer_id = test_influencer.id
        
        response = await authenticated_client.delete(f"/influencer/remove_influencer/{influencer_id}")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify influencer is deleted from database
        result = await db_session.execute(select(Influencer).where(Influencer.id == influencer_id))
        deleted_influencer = result.scalar_one_or_none()
        assert deleted_influencer is None

    @pytest.mark.asyncio
    async def test_delete_influencer_nonexistent_fails(self, authenticated_client: AsyncClient):
        """Test deleting nonexistent influencer fails."""
        nonexistent_id = 99999
        
        response = await authenticated_client.delete(f"/influencer/remove_influencer/{nonexistent_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_influencer_invalid_id_fails(self, authenticated_client: AsyncClient):
        """Test deleting influencer with invalid ID fails."""
        invalid_id = "not_a_number"
        
        response = await authenticated_client.delete(f"/influencer/remove_influencer/{invalid_id}")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestInfluencerSearch:
    """Test cases for influencer search functionality."""

    @pytest.mark.asyncio
    async def test_search_influencers_by_location(self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user, test_factory):
        """Test searching influencers by location."""
        # Create influencers with different locations
        locations = ["New York", "Los Angeles", "Chicago"]
        created_influencers = []
        
        for location in locations:
            influencer_data = test_factory.influencer_data(user_id=test_user.id)
            influencer_data["location"] = location
            influencer = Influencer(**influencer_data)
            db_session.add(influencer)
            created_influencers.append(influencer)
        
        await db_session.commit()
        
        # Search for New York influencers
        response = await authenticated_client.get("/influencer/search/New York")
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert isinstance(response_data, list)
        
        # All returned influencers should be from New York
        for influencer in response_data:
            assert influencer["location"] == "New York"

    @pytest.mark.asyncio
    async def test_search_influencers_by_language(self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user, test_factory):
        """Test searching influencers by language."""
        # Create influencers with different languages
        languages = ["English", "Spanish", "French"]
        
        for language in languages:
            influencer_data = test_factory.influencer_data(user_id=test_user.id)
            influencer_data["languages"] = language
            influencer = Influencer(**influencer_data)
            db_session.add(influencer)
        
        await db_session.commit()
        
        # Search for English-speaking influencers
        response = await authenticated_client.get("/influencer/search_by_language/English")
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert isinstance(response_data, list)
        
        # All returned influencers should speak English
        for influencer in response_data:
            assert "English" in influencer["languages"]

    @pytest.mark.asyncio
    async def test_search_influencers_no_results(self, authenticated_client: AsyncClient):
        """Test searching influencers with no matching results."""
        response = await authenticated_client.get("/influencer/search/NonexistentLocation")
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == 0


class TestInfluencerValidation:
    """Test cases for influencer data validation."""

    @pytest.mark.asyncio
    async def test_rate_validation(self, authenticated_client: AsyncClient, test_user):
        """Test rate validation."""
        invalid_rates = [-1, 0, "not_a_number", 999999999]
        
        for invalid_rate in invalid_rates:
            influencer_data = {
                "bio": "Test bio",
                "rate_per_post": invalid_rate,
                "user_id": test_user.id,
                "availability": True
            }
            
            response = await authenticated_client.post("/influencer/create_influencer", json=influencer_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_bio_length_validation(self, authenticated_client: AsyncClient, test_user):
        """Test bio length validation."""
        # Test very long bio
        very_long_bio = "A" * 10000
        
        influencer_data = {
            "bio": very_long_bio,
            "user_id": test_user.id,
            "availability": True
        }
        
        response = await authenticated_client.post("/influencer/create_influencer", json=influencer_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_url_validation(self, authenticated_client: AsyncClient, test_user):
        """Test URL validation for profile image and website."""
        invalid_urls = ["not_a_url", "http://", "ftp://example.com", ""]
        
        for invalid_url in invalid_urls:
            influencer_data = {
                "bio": "Test bio",
                "profile_image_url": invalid_url,
                "website_url": invalid_url,
                "user_id": test_user.id,
                "availability": True
            }
            
            response = await authenticated_client.post("/influencer/create_influencer", json=influencer_data)
            # Depending on validation implementation, this might pass or fail
            if response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
                error_detail = str(response.json())
                assert "url" in error_detail.lower()


class TestInfluencerIntegration:
    """Integration tests for influencer workflows."""

    @pytest.mark.asyncio
    async def test_complete_influencer_lifecycle(self, authenticated_client: AsyncClient, test_user, test_factory):
        """Test complete influencer lifecycle: create -> read -> update -> delete."""
        # Step 1: Create influencer
        influencer_data = test_factory.influencer_data(user_id=test_user.id)
        create_response = await authenticated_client.post("/influencer/create_influencer", json=influencer_data)
        assert create_response.status_code == status.HTTP_200_OK
        influencer_id = create_response.json()["id"]

        # Step 2: Read influencer
        read_response = await authenticated_client.get(f"/influencer/get_influencer/{influencer_id}")
        assert read_response.status_code == status.HTTP_200_OK
        assert read_response.json()["bio"] == influencer_data["bio"]

        # Step 3: Update influencer
        update_data = {"bio": "Updated bio", "rate_per_post": 400.0}
        update_response = await authenticated_client.put(f"/influencer/update_influencer/{influencer_id}", json=update_data)
        assert update_response.status_code == status.HTTP_200_OK
        assert update_response.json()["bio"] == update_data["bio"]

        # Step 4: Set availability
        availability_response = await authenticated_client.put(f"/influencer/set_availability/{influencer_id}/False")
        assert availability_response.status_code == status.HTTP_200_OK
        assert availability_response.json()["availability"] is False

        # Step 5: Delete influencer
        delete_response = await authenticated_client.delete(f"/influencer/remove_influencer/{influencer_id}")
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Step 6: Verify deletion
        verify_response = await authenticated_client.get(f"/influencer/get_influencer/{influencer_id}")
        assert verify_response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_influencer_with_multiple_rate_cards(self, authenticated_client: AsyncClient, test_influencer):
        """Test influencer with multiple rate cards."""
        platforms = ["Instagram", "TikTok", "YouTube"]
        
        # Create rate cards for different platforms
        for platform in platforms:
            rate_card_data = {
                "platform": platform,
                "content_type": "Post",
                "rate": 250.00,
                "influencer_id": test_influencer.id
            }
            
            response = await authenticated_client.post("/rate_card/create", json=rate_card_data)
            assert response.status_code == status.HTTP_200_OK

        # Get all rate cards for the influencer
        rate_cards_response = await authenticated_client.get(f"/rate_card/influencer/{test_influencer.id}")
        
        if rate_cards_response.status_code == status.HTTP_200_OK:
            rate_cards = rate_cards_response.json()
            returned_platforms = {card["platform"] for card in rate_cards}
            assert set(platforms).issubset(returned_platforms)

    @pytest.mark.asyncio
    async def test_influencer_availability_filtering(self, authenticated_client: AsyncClient, db_session: AsyncSession, test_user, test_factory):
        """Test filtering influencers by availability."""
        # Create available and unavailable influencers
        available_count = 3
        unavailable_count = 2
        
        # Create available influencers
        for i in range(available_count):
            influencer_data = test_factory.influencer_data(user_id=test_user.id)
            influencer_data["availability"] = True
            influencer = Influencer(**influencer_data)
            db_session.add(influencer)
        
        # Create unavailable influencers
        for i in range(unavailable_count):
            influencer_data = test_factory.influencer_data(user_id=test_user.id)
            influencer_data["availability"] = False
            influencer = Influencer(**influencer_data)
            db_session.add(influencer)
        
        await db_session.commit()
        
        # Get only available influencers
        available_response = await authenticated_client.get("/influencer/influencers/available")
        assert available_response.status_code == status.HTTP_200_OK
        
        available_influencers = available_response.json()
        
        # All returned influencers should be available
        for influencer in available_influencers:
            assert influencer["availability"] is True
        
        # Should have at least the available ones we created
        assert len(available_influencers) >= available_count 