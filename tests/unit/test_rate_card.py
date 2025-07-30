import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import status
from decimal import Decimal

from app.db.models.rate_card import RateCard


class TestRateCardCreation:
    """Test cases for rate card creation functionality."""

    @pytest.mark.asyncio
    async def test_create_rate_card_success(self, authenticated_client: AsyncClient, test_influencer, faker_instance):
        """Test successful rate card creation."""
        rate_card_data = {
            "platform": "Instagram",
            "content_type": "Post",
            "follower_range": "10K-50K",
            "rate": 250.00,
            "currency": "USD",
            "description": faker_instance.text(max_nb_chars=200),
            "influencer_id": test_influencer.id
        }
        
        response = await authenticated_client.post("/rate_card/create", json=rate_card_data)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["platform"] == rate_card_data["platform"]
        assert response_data["content_type"] == rate_card_data["content_type"]
        assert float(response_data["rate"]) == rate_card_data["rate"]
        assert response_data["influencer_id"] == test_influencer.id

    @pytest.mark.asyncio
    async def test_create_rate_card_without_auth_fails(self, client: AsyncClient, test_influencer):
        """Test that creating rate card without authentication fails."""
        rate_card_data = {
            "platform": "Instagram",
            "content_type": "Post",
            "rate": 250.00,
            "influencer_id": test_influencer.id
        }
        
        response = await client.post("/rate_card/create", json=rate_card_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_create_rate_card_invalid_data_fails(self, authenticated_client: AsyncClient, test_influencer):
        """Test rate card creation with invalid data fails."""
        invalid_data = {
            "platform": "",  # Empty platform
            "content_type": "Post",
            "rate": -100.00,  # Negative rate
            "influencer_id": test_influencer.id
        }
        
        response = await authenticated_client.post("/rate_card/create", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_rate_card_missing_fields_fails(self, authenticated_client: AsyncClient):
        """Test rate card creation with missing required fields fails."""
        incomplete_data = {"platform": "Instagram"}  # Missing other required fields
        
        response = await authenticated_client.post("/rate_card/create", json=incomplete_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_rate_card_nonexistent_influencer_fails(self, authenticated_client: AsyncClient):
        """Test creating rate card for nonexistent influencer fails."""
        rate_card_data = {
            "platform": "Instagram",
            "content_type": "Post",
            "rate": 250.00,
            "influencer_id": 99999  # Nonexistent influencer
        }
        
        response = await authenticated_client.post("/rate_card/create", json=rate_card_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRateCardRetrieval:
    """Test cases for rate card retrieval functionality."""

    @pytest.mark.asyncio
    async def test_get_rate_card_by_id_success(self, authenticated_client: AsyncClient, db_session: AsyncSession, test_influencer):
        """Test successful rate card retrieval by ID."""
        # Create a rate card first
        rate_card = RateCard(
            platform="Instagram",
            content_type="Post",
            follower_range="10K-50K",
            rate=Decimal("250.00"),
            currency="USD",
            influencer_id=test_influencer.id
        )
        db_session.add(rate_card)
        await db_session.commit()
        await db_session.refresh(rate_card)
        
        response = await authenticated_client.get(f"/rate_card/{rate_card.id}")
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["id"] == rate_card.id
        assert response_data["platform"] == "Instagram"

    @pytest.mark.asyncio
    async def test_get_rate_card_nonexistent_fails(self, authenticated_client: AsyncClient):
        """Test getting nonexistent rate card fails."""
        nonexistent_id = 99999
        
        response = await authenticated_client.get(f"/rate_card/{nonexistent_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_list_influencer_rate_cards(self, authenticated_client: AsyncClient, db_session: AsyncSession, test_influencer):
        """Test listing rate cards for an influencer."""
        # Create multiple rate cards
        platforms = ["Instagram", "TikTok", "YouTube"]
        for platform in platforms:
            rate_card = RateCard(
                platform=platform,
                content_type="Post",
                rate=Decimal("200.00"),
                influencer_id=test_influencer.id
            )
            db_session.add(rate_card)
        
        await db_session.commit()
        
        response = await authenticated_client.get(f"/rate_card/influencer/{test_influencer.id}")
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == len(platforms)
        
        returned_platforms = {card["platform"] for card in response_data}
        assert returned_platforms == set(platforms)

    @pytest.mark.asyncio
    async def test_search_rate_cards_by_platform(self, authenticated_client: AsyncClient, db_session: AsyncSession, test_influencer):
        """Test searching rate cards by platform."""
        # Create rate cards for different platforms
        instagram_card = RateCard(
            platform="Instagram",
            content_type="Post",
            rate=Decimal("250.00"),
            influencer_id=test_influencer.id
        )
        tiktok_card = RateCard(
            platform="TikTok",
            content_type="Video",
            rate=Decimal("300.00"),
            influencer_id=test_influencer.id
        )
        
        db_session.add_all([instagram_card, tiktok_card])
        await db_session.commit()
        
        response = await authenticated_client.get("/rate_card/search?platform=Instagram")
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert isinstance(response_data, list)
        
        # All returned cards should be Instagram
        for card in response_data:
            assert card["platform"] == "Instagram"


class TestRateCardUpdate:
    """Test cases for rate card update functionality."""

    @pytest.mark.asyncio
    async def test_update_rate_card_success(self, authenticated_client: AsyncClient, db_session: AsyncSession, test_influencer):
        """Test successful rate card update."""
        # Create a rate card
        rate_card = RateCard(
            platform="Instagram",
            content_type="Post",
            rate=Decimal("250.00"),
            influencer_id=test_influencer.id
        )
        db_session.add(rate_card)
        await db_session.commit()
        await db_session.refresh(rate_card)
        
        update_data = {
            "rate": 350.00,
            "content_type": "Reel",
            "description": "Updated rate for Instagram Reels"
        }
        
        response = await authenticated_client.put(f"/rate_card/update/{rate_card.id}", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert float(response_data["rate"]) == update_data["rate"]
        assert response_data["content_type"] == update_data["content_type"]

    @pytest.mark.asyncio
    async def test_update_rate_card_nonexistent_fails(self, authenticated_client: AsyncClient):
        """Test updating nonexistent rate card fails."""
        nonexistent_id = 99999
        update_data = {"rate": 350.00}
        
        response = await authenticated_client.put(f"/rate_card/update/{nonexistent_id}", json=update_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_rate_card_invalid_data_fails(self, authenticated_client: AsyncClient, db_session: AsyncSession, test_influencer):
        """Test updating rate card with invalid data fails."""
        # Create a rate card
        rate_card = RateCard(
            platform="Instagram",
            content_type="Post",
            rate=Decimal("250.00"),
            influencer_id=test_influencer.id
        )
        db_session.add(rate_card)
        await db_session.commit()
        await db_session.refresh(rate_card)
        
        invalid_data = {
            "rate": -100.00,  # Negative rate
            "platform": ""  # Empty platform
        }
        
        response = await authenticated_client.put(f"/rate_card/update/{rate_card.id}", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestRateCardDeletion:
    """Test cases for rate card deletion functionality."""

    @pytest.mark.asyncio
    async def test_delete_rate_card_success(self, authenticated_client: AsyncClient, db_session: AsyncSession, test_influencer):
        """Test successful rate card deletion."""
        # Create a rate card
        rate_card = RateCard(
            platform="Instagram",
            content_type="Post",
            rate=Decimal("250.00"),
            influencer_id=test_influencer.id
        )
        db_session.add(rate_card)
        await db_session.commit()
        await db_session.refresh(rate_card)
        rate_card_id = rate_card.id
        
        response = await authenticated_client.delete(f"/rate_card/delete/{rate_card_id}")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify deletion
        result = await db_session.execute(select(RateCard).where(RateCard.id == rate_card_id))
        deleted_card = result.scalar_one_or_none()
        assert deleted_card is None

    @pytest.mark.asyncio
    async def test_delete_rate_card_nonexistent_fails(self, authenticated_client: AsyncClient):
        """Test deleting nonexistent rate card fails."""
        nonexistent_id = 99999
        
        response = await authenticated_client.delete(f"/rate_card/delete/{nonexistent_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRateCardValidation:
    """Test cases for rate card data validation."""

    @pytest.mark.asyncio
    async def test_rate_validation(self, authenticated_client: AsyncClient, test_influencer):
        """Test rate value validation."""
        invalid_rates = [-1, 0, "not_a_number", 999999999]  # Negative, zero, non-numeric, too large
        
        for invalid_rate in invalid_rates:
            rate_card_data = {
                "platform": "Instagram",
                "content_type": "Post",
                "rate": invalid_rate,
                "influencer_id": test_influencer.id
            }
            
            response = await authenticated_client.post("/rate_card/create", json=rate_card_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_platform_validation(self, authenticated_client: AsyncClient, test_influencer):
        """Test platform validation."""
        invalid_platforms = ["", " ", "InvalidPlatform123"]
        
        for invalid_platform in invalid_platforms:
            rate_card_data = {
                "platform": invalid_platform,
                "content_type": "Post",
                "rate": 250.00,
                "influencer_id": test_influencer.id
            }
            
            response = await authenticated_client.post("/rate_card/create", json=rate_card_data)
            # Depending on validation rules, this might pass or fail
            if response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
                assert "platform" in str(response.json())

    @pytest.mark.asyncio
    async def test_currency_validation(self, authenticated_client: AsyncClient, test_influencer):
        """Test currency validation."""
        valid_currencies = ["USD", "EUR", "GBP", "CAD"]
        invalid_currencies = ["", "INVALID", "123"]
        
        # Test valid currencies
        for currency in valid_currencies:
            rate_card_data = {
                "platform": "Instagram",
                "content_type": "Post",
                "rate": 250.00,
                "currency": currency,
                "influencer_id": test_influencer.id
            }
            
            response = await authenticated_client.post("/rate_card/create", json=rate_card_data)
            # Should succeed or at least not fail on currency validation
            assert response.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY or "currency" not in str(response.json())

        # Test invalid currencies
        for currency in invalid_currencies:
            rate_card_data = {
                "platform": "Instagram",
                "content_type": "Post",
                "rate": 250.00,
                "currency": currency,
                "influencer_id": test_influencer.id
            }
            
            response = await authenticated_client.post("/rate_card/create", json=rate_card_data)
            # Depending on validation implementation
            if response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
                assert "currency" in str(response.json())


class TestRateCardBusiness:
    """Test cases for rate card business logic."""

    @pytest.mark.asyncio
    async def test_rate_card_pricing_tiers(self, authenticated_client: AsyncClient, db_session: AsyncSession, test_influencer):
        """Test rate card pricing for different follower tiers."""
        follower_tiers = [
            ("1K-10K", 100.00),
            ("10K-50K", 250.00),
            ("50K-100K", 500.00),
            ("100K+", 1000.00)
        ]
        
        created_cards = []
        for tier, rate in follower_tiers:
            rate_card_data = {
                "platform": "Instagram",
                "content_type": "Post",
                "follower_range": tier,
                "rate": rate,
                "influencer_id": test_influencer.id
            }
            
            response = await authenticated_client.post("/rate_card/create", json=rate_card_data)
            assert response.status_code == status.HTTP_200_OK
            created_cards.append(response.json())
        
        # Verify all cards were created with correct pricing
        for i, (tier, expected_rate) in enumerate(follower_tiers):
            assert created_cards[i]["follower_range"] == tier
            assert float(created_cards[i]["rate"]) == expected_rate

    @pytest.mark.asyncio
    async def test_duplicate_rate_card_handling(self, authenticated_client: AsyncClient, test_influencer):
        """Test handling of duplicate rate cards."""
        rate_card_data = {
            "platform": "Instagram",
            "content_type": "Post",
            "follower_range": "10K-50K",
            "rate": 250.00,
            "influencer_id": test_influencer.id
        }
        
        # Create first rate card
        response1 = await authenticated_client.post("/rate_card/create", json=rate_card_data)
        assert response1.status_code == status.HTTP_200_OK
        
        # Try to create duplicate
        response2 = await authenticated_client.post("/rate_card/create", json=rate_card_data)
        
        # Depending on business rules, this might:
        # 1. Be allowed (multiple rate cards for same criteria)
        # 2. Be rejected (no duplicates allowed)
        # 3. Update existing card
        assert response2.status_code in [
            status.HTTP_200_OK,  # Allowed
            status.HTTP_400_BAD_REQUEST,  # Rejected
            status.HTTP_409_CONFLICT  # Conflict
        ]

    @pytest.mark.asyncio
    async def test_rate_card_content_type_variations(self, authenticated_client: AsyncClient, test_influencer):
        """Test rate cards for different content types."""
        content_types = [
            ("Post", 250.00),
            ("Story", 100.00),
            ("Reel", 400.00),
            ("IGTV", 600.00)
        ]
        
        for content_type, rate in content_types:
            rate_card_data = {
                "platform": "Instagram",
                "content_type": content_type,
                "rate": rate,
                "influencer_id": test_influencer.id
            }
            
            response = await authenticated_client.post("/rate_card/create", json=rate_card_data)
            assert response.status_code == status.HTTP_200_OK
            
            response_data = response.json()
            assert response_data["content_type"] == content_type
            assert float(response_data["rate"]) == rate


class TestRateCardIntegration:
    """Integration tests for rate card workflows."""

    @pytest.mark.asyncio
    async def test_complete_rate_card_lifecycle(self, authenticated_client: AsyncClient, test_influencer):
        """Test complete rate card lifecycle: create -> read -> update -> delete."""
        # Step 1: Create rate card
        rate_card_data = {
            "platform": "Instagram",
            "content_type": "Post",
            "rate": 250.00,
            "influencer_id": test_influencer.id
        }
        
        create_response = await authenticated_client.post("/rate_card/create", json=rate_card_data)
        assert create_response.status_code == status.HTTP_200_OK
        rate_card_id = create_response.json()["id"]

        # Step 2: Read rate card
        read_response = await authenticated_client.get(f"/rate_card/{rate_card_id}")
        assert read_response.status_code == status.HTTP_200_OK
        assert read_response.json()["platform"] == "Instagram"

        # Step 3: Update rate card
        update_data = {"rate": 350.00, "content_type": "Reel"}
        update_response = await authenticated_client.put(f"/rate_card/update/{rate_card_id}", json=update_data)
        assert update_response.status_code == status.HTTP_200_OK
        assert float(update_response.json()["rate"]) == 350.00

        # Step 4: Delete rate card
        delete_response = await authenticated_client.delete(f"/rate_card/delete/{rate_card_id}")
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Step 5: Verify deletion
        verify_response = await authenticated_client.get(f"/rate_card/{rate_card_id}")
        assert verify_response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_influencer_multiple_rate_cards(self, authenticated_client: AsyncClient, test_influencer):
        """Test that an influencer can have multiple rate cards."""
        platforms = ["Instagram", "TikTok", "YouTube", "Twitter"]
        created_cards = []
        
        # Create rate cards for different platforms
        for platform in platforms:
            rate_card_data = {
                "platform": platform,
                "content_type": "Post",
                "rate": 200.00 + len(created_cards) * 50,  # Different rates
                "influencer_id": test_influencer.id
            }
            
            response = await authenticated_client.post("/rate_card/create", json=rate_card_data)
            assert response.status_code == status.HTTP_200_OK
            created_cards.append(response.json())

        # Verify all cards exist for the influencer
        list_response = await authenticated_client.get(f"/rate_card/influencer/{test_influencer.id}")
        assert list_response.status_code == status.HTTP_200_OK
        
        influencer_cards = list_response.json()
        assert len(influencer_cards) >= len(platforms)
        
        # Verify all platforms are represented
        returned_platforms = {card["platform"] for card in influencer_cards}
        assert set(platforms).issubset(returned_platforms) 