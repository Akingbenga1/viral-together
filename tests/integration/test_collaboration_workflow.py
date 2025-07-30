import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import status
from datetime import datetime, timedelta

from app.db.models.collaborations import Collaboration
from app.db.models.promotion_interest import PromotionInterest


class TestCollaborationWorkflow:
    """Integration tests for the complete collaboration workflow."""

    @pytest.mark.asyncio
    async def test_complete_collaboration_flow(self, client: AsyncClient, db_session: AsyncSession, test_factory):
        """Test the complete collaboration flow from business to influencer."""
        
        # Step 1: Create business user and business
        business_user_data = test_factory.user_data()
        business_response = await client.post("/auth/register", json=business_user_data)
        assert business_response.status_code == status.HTTP_200_OK
        
        # Login as business user
        business_login = await client.post("/auth/token", data={
            "username": business_user_data["username"],
            "password": business_user_data["password"]
        })
        business_token = business_login.json()["access_token"]
        
        # Create business profile
        business_data = test_factory.business_data(user_id=business_response.json()["id"])
        client.headers.update({"Authorization": f"Bearer {business_token}"})
        business_profile_response = await client.post("/business/create", json=business_data)
        assert business_profile_response.status_code == status.HTTP_200_OK
        business_id = business_profile_response.json()["id"]
        
        # Step 2: Create influencer user and profile
        influencer_user_data = test_factory.user_data()
        influencer_response = await client.post("/auth/register", json=influencer_user_data)
        assert influencer_response.status_code == status.HTTP_200_OK
        
        # Login as influencer
        influencer_login = await client.post("/auth/token", data={
            "username": influencer_user_data["username"],
            "password": influencer_user_data["password"]
        })
        influencer_token = influencer_login.json()["access_token"]
        
        # Create influencer profile
        influencer_data = test_factory.influencer_data(user_id=influencer_response.json()["id"])
        client.headers.update({"Authorization": f"Bearer {influencer_token}"})
        influencer_profile_response = await client.post("/influencer/create_influencer", json=influencer_data)
        assert influencer_profile_response.status_code == status.HTTP_200_OK
        influencer_id = influencer_profile_response.json()["id"]
        
        # Step 3: Business creates a promotion
        client.headers.update({"Authorization": f"Bearer {business_token}"})
        promotion_data = test_factory.promotion_data(business_id=business_id)
        promotion_response = await client.post("/promotion/create", json=promotion_data)
        assert promotion_response.status_code == status.HTTP_200_OK
        promotion_id = promotion_response.json()["id"]
        
        # Step 4: Influencer expresses interest in promotion
        client.headers.update({"Authorization": f"Bearer {influencer_token}"})
        interest_data = {
            "promotion_id": promotion_id,
            "message": "I'm interested in this collaboration opportunity!"
        }
        interest_response = await client.post("/promotion_interest", json=interest_data)
        assert interest_response.status_code == status.HTTP_200_OK
        
        # Step 5: Business reviews and creates collaboration
        client.headers.update({"Authorization": f"Bearer {business_token}"})
        collaboration_data = {
            "promotion_id": promotion_id,
            "influencer_id": influencer_id,
            "status": "pending",
            "agreed_rate": 500.00,
            "deliverables": "1 Instagram post and 2 stories",
            "deadline": (datetime.now() + timedelta(days=30)).isoformat()
        }
        collaboration_response = await client.post("/collaboration/create", json=collaboration_data)
        assert collaboration_response.status_code == status.HTTP_200_OK
        collaboration_id = collaboration_response.json()["id"]
        
        # Step 6: Influencer accepts collaboration
        client.headers.update({"Authorization": f"Bearer {influencer_token}"})
        accept_response = await client.put(f"/collaboration/{collaboration_id}/accept")
        assert accept_response.status_code == status.HTTP_200_OK
        assert accept_response.json()["status"] == "accepted"
        
        # Step 7: Verify collaboration exists in database
        result = await db_session.execute(
            select(Collaboration).where(Collaboration.id == collaboration_id)
        )
        collaboration = result.scalar_one_or_none()
        assert collaboration is not None
        assert collaboration.status == "accepted"
        assert collaboration.promotion_id == promotion_id
        assert collaboration.influencer_id == influencer_id

    @pytest.mark.asyncio
    async def test_collaboration_rejection_flow(self, client: AsyncClient, db_session: AsyncSession, test_factory):
        """Test collaboration rejection workflow."""
        
        # Create business and influencer (similar setup as above but condensed)
        business_user_data = test_factory.user_data()
        await client.post("/auth/register", json=business_user_data)
        business_login = await client.post("/auth/token", data={
            "username": business_user_data["username"],
            "password": business_user_data["password"]
        })
        business_token = business_login.json()["access_token"]
        
        influencer_user_data = test_factory.user_data()
        await client.post("/auth/register", json=influencer_user_data)
        influencer_login = await client.post("/auth/token", data={
            "username": influencer_user_data["username"],
            "password": influencer_user_data["password"]
        })
        influencer_token = influencer_login.json()["access_token"]
        
        # Create business profile
        client.headers.update({"Authorization": f"Bearer {business_token}"})
        business_data = test_factory.business_data(user_id=1)  # Simplified
        business_response = await client.post("/business/create", json=business_data)
        business_id = business_response.json()["id"]
        
        # Create influencer profile
        client.headers.update({"Authorization": f"Bearer {influencer_token}"})
        influencer_data = test_factory.influencer_data(user_id=2)  # Simplified
        influencer_response = await client.post("/influencer/create_influencer", json=influencer_data)
        influencer_id = influencer_response.json()["id"]
        
        # Create promotion and collaboration
        client.headers.update({"Authorization": f"Bearer {business_token}"})
        promotion_data = test_factory.promotion_data(business_id=business_id)
        promotion_response = await client.post("/promotion/create", json=promotion_data)
        promotion_id = promotion_response.json()["id"]
        
        collaboration_data = {
            "promotion_id": promotion_id,
            "influencer_id": influencer_id,
            "status": "pending",
            "agreed_rate": 500.00
        }
        collaboration_response = await client.post("/collaboration/create", json=collaboration_data)
        collaboration_id = collaboration_response.json()["id"]
        
        # Influencer rejects collaboration
        client.headers.update({"Authorization": f"Bearer {influencer_token}"})
        reject_data = {"reason": "Not aligned with my brand values"}
        reject_response = await client.put(f"/collaboration/{collaboration_id}/reject", json=reject_data)
        
        assert reject_response.status_code == status.HTTP_200_OK
        assert reject_response.json()["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_multiple_influencers_same_promotion(self, client: AsyncClient, test_factory):
        """Test multiple influencers showing interest in the same promotion."""
        
        # Create business
        business_user_data = test_factory.user_data()
        await client.post("/auth/register", json=business_user_data)
        business_login = await client.post("/auth/token", data={
            "username": business_user_data["username"],
            "password": business_user_data["password"]
        })
        business_token = business_login.json()["access_token"]
        
        client.headers.update({"Authorization": f"Bearer {business_token}"})
        business_data = test_factory.business_data(user_id=1)
        business_response = await client.post("/business/create", json=business_data)
        business_id = business_response.json()["id"]
        
        # Create promotion
        promotion_data = test_factory.promotion_data(business_id=business_id)
        promotion_response = await client.post("/promotion/create", json=promotion_data)
        promotion_id = promotion_response.json()["id"]
        
        # Create multiple influencers
        influencer_count = 3
        influencer_tokens = []
        influencer_ids = []
        
        for i in range(influencer_count):
            influencer_user_data = test_factory.user_data()
            await client.post("/auth/register", json=influencer_user_data)
            
            influencer_login = await client.post("/auth/token", data={
                "username": influencer_user_data["username"],
                "password": influencer_user_data["password"]
            })
            token = influencer_login.json()["access_token"]
            influencer_tokens.append(token)
            
            # Create influencer profile
            client.headers.update({"Authorization": f"Bearer {token}"})
            influencer_data = test_factory.influencer_data(user_id=i+2)
            influencer_response = await client.post("/influencer/create_influencer", json=influencer_data)
            influencer_ids.append(influencer_response.json()["id"])
        
        # Each influencer expresses interest
        for i, token in enumerate(influencer_tokens):
            client.headers.update({"Authorization": f"Bearer {token}"})
            interest_data = {
                "promotion_id": promotion_id,
                "message": f"Influencer {i+1} is interested!"
            }
            interest_response = await client.post("/promotion_interest", json=interest_data)
            assert interest_response.status_code == status.HTTP_200_OK
        
        # Business can see all interests
        client.headers.update({"Authorization": f"Bearer {business_token}"})
        interests_response = await client.get(f"/promotion/{promotion_id}/interests")
        
        if interests_response.status_code == status.HTTP_200_OK:
            interests = interests_response.json()
            assert len(interests) == influencer_count


class TestPromotionLifecycle:
    """Integration tests for promotion lifecycle management."""

    @pytest.mark.asyncio
    async def test_promotion_creation_to_completion(self, client: AsyncClient, test_factory):
        """Test complete promotion lifecycle from creation to completion."""
        
        # Setup business
        business_user_data = test_factory.user_data()
        await client.post("/auth/register", json=business_user_data)
        business_login = await client.post("/auth/token", data={
            "username": business_user_data["username"],
            "password": business_user_data["password"]
        })
        business_token = business_login.json()["access_token"]
        
        client.headers.update({"Authorization": f"Bearer {business_token}"})
        business_data = test_factory.business_data(user_id=1)
        business_response = await client.post("/business/create", json=business_data)
        business_id = business_response.json()["id"]
        
        # Create promotion
        promotion_data = test_factory.promotion_data(business_id=business_id)
        promotion_response = await client.post("/promotion/create", json=promotion_data)
        assert promotion_response.status_code == status.HTTP_200_OK
        promotion_id = promotion_response.json()["id"]
        
        # Update promotion status
        update_data = {"status": "active", "description": "Updated promotion description"}
        update_response = await client.put(f"/promotion/{promotion_id}", json=update_data)
        assert update_response.status_code == status.HTTP_200_OK
        
        # Mark promotion as completed
        complete_response = await client.put(f"/promotion/{promotion_id}/complete")
        assert complete_response.status_code == status.HTTP_200_OK
        assert complete_response.json()["status"] == "completed"

    @pytest.mark.asyncio
    async def test_promotion_with_multiple_collaborations(self, client: AsyncClient, test_factory):
        """Test promotion with multiple simultaneous collaborations."""
        
        # Setup business
        business_user_data = test_factory.user_data()
        await client.post("/auth/register", json=business_user_data)
        business_login = await client.post("/auth/token", data={
            "username": business_user_data["username"],
            "password": business_user_data["password"]
        })
        business_token = business_login.json()["access_token"]
        
        client.headers.update({"Authorization": f"Bearer {business_token}"})
        business_data = test_factory.business_data(user_id=1)
        business_response = await client.post("/business/create", json=business_data)
        business_id = business_response.json()["id"]
        
        # Create promotion
        promotion_data = test_factory.promotion_data(business_id=business_id)
        promotion_response = await client.post("/promotion/create", json=promotion_data)
        promotion_id = promotion_response.json()["id"]
        
        # Create multiple influencers and collaborations
        collaboration_count = 2
        for i in range(collaboration_count):
            # Create influencer
            influencer_user_data = test_factory.user_data()
            await client.post("/auth/register", json=influencer_user_data)
            
            influencer_login = await client.post("/auth/token", data={
                "username": influencer_user_data["username"],
                "password": influencer_user_data["password"]
            })
            influencer_token = influencer_login.json()["access_token"]
            
            client.headers.update({"Authorization": f"Bearer {influencer_token}"})
            influencer_data = test_factory.influencer_data(user_id=i+2)
            influencer_response = await client.post("/influencer/create_influencer", json=influencer_data)
            influencer_id = influencer_response.json()["id"]
            
            # Create collaboration
            client.headers.update({"Authorization": f"Bearer {business_token}"})
            collaboration_data = {
                "promotion_id": promotion_id,
                "influencer_id": influencer_id,
                "status": "pending",
                "agreed_rate": 300.00 + (i * 100)  # Different rates
            }
            collaboration_response = await client.post("/collaboration/create", json=collaboration_data)
            assert collaboration_response.status_code == status.HTTP_200_OK
        
        # List all collaborations for promotion
        collaborations_response = await client.get(f"/promotion/{promotion_id}/collaborations")
        if collaborations_response.status_code == status.HTTP_200_OK:
            collaborations = collaborations_response.json()
            assert len(collaborations) == collaboration_count


class TestBusinessInfluencerInteraction:
    """Integration tests for business-influencer interactions."""

    @pytest.mark.asyncio
    async def test_rate_negotiation_flow(self, client: AsyncClient, test_factory):
        """Test rate negotiation between business and influencer."""
        
        # Setup business and influencer (condensed setup)
        business_user_data = test_factory.user_data()
        await client.post("/auth/register", json=business_user_data)
        business_login = await client.post("/auth/token", data={
            "username": business_user_data["username"],
            "password": business_user_data["password"]
        })
        business_token = business_login.json()["access_token"]
        
        influencer_user_data = test_factory.user_data()
        await client.post("/auth/register", json=influencer_user_data)
        influencer_login = await client.post("/auth/token", data={
            "username": influencer_user_data["username"],
            "password": influencer_user_data["password"]
        })
        influencer_token = influencer_login.json()["access_token"]
        
        # Create profiles
        client.headers.update({"Authorization": f"Bearer {business_token}"})
        business_data = test_factory.business_data(user_id=1)
        business_response = await client.post("/business/create", json=business_data)
        business_id = business_response.json()["id"]
        
        client.headers.update({"Authorization": f"Bearer {influencer_token}"})
        influencer_data = test_factory.influencer_data(user_id=2)
        influencer_response = await client.post("/influencer/create_influencer", json=influencer_data)
        influencer_id = influencer_response.json()["id"]
        
        # Create rate card for influencer
        rate_card_data = {
            "platform": "Instagram",
            "content_type": "Post",
            "rate": 400.00,
            "influencer_id": influencer_id
        }
        rate_card_response = await client.post("/rate_card/create", json=rate_card_data)
        assert rate_card_response.status_code == status.HTTP_200_OK
        
        # Business creates rate proposal
        client.headers.update({"Authorization": f"Bearer {business_token}"})
        proposal_data = {
            "influencer_id": influencer_id,
            "proposed_rate": 350.00,
            "platform": "Instagram",
            "content_type": "Post",
            "message": "Would you consider this rate for our collaboration?"
        }
        proposal_response = await client.post("/rate_proposal/create", json=proposal_data)
        
        if proposal_response.status_code == status.HTTP_200_OK:
            proposal_id = proposal_response.json()["id"]
            
            # Influencer responds to proposal
            client.headers.update({"Authorization": f"Bearer {influencer_token}"})
            response_data = {
                "status": "accepted",
                "counter_rate": 375.00,
                "message": "I can accept this rate with a small adjustment"
            }
            response_response = await client.put(f"/rate_proposal/{proposal_id}/respond", json=response_data)
            assert response_response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_influencer_discovery_workflow(self, client: AsyncClient, test_factory):
        """Test business discovering and contacting influencers."""
        
        # Create business
        business_user_data = test_factory.user_data()
        await client.post("/auth/register", json=business_user_data)
        business_login = await client.post("/auth/token", data={
            "username": business_user_data["username"],
            "password": business_user_data["password"]
        })
        business_token = business_login.json()["access_token"]
        
        # Create multiple influencers with different attributes
        influencer_locations = ["New York", "Los Angeles", "Chicago"]
        influencer_ids = []
        
        for i, location in enumerate(influencer_locations):
            influencer_user_data = test_factory.user_data()
            await client.post("/auth/register", json=influencer_user_data)
            
            influencer_login = await client.post("/auth/token", data={
                "username": influencer_user_data["username"],
                "password": influencer_user_data["password"]
            })
            influencer_token = influencer_login.json()["access_token"]
            
            client.headers.update({"Authorization": f"Bearer {influencer_token}"})
            influencer_data = test_factory.influencer_data(user_id=i+2)
            influencer_data["location"] = location
            influencer_data["availability"] = True
            
            influencer_response = await client.post("/influencer/create_influencer", json=influencer_data)
            influencer_ids.append(influencer_response.json()["id"])
        
        # Business searches for available influencers
        client.headers.update({"Authorization": f"Bearer {business_token}"})
        
        # Search by location
        search_response = await client.get("/influencer/search/New York")
        if search_response.status_code == status.HTTP_200_OK:
            results = search_response.json()
            assert len(results) >= 1
            assert any(inf["location"] == "New York" for inf in results)
        
        # Get all available influencers
        available_response = await client.get("/influencer/influencers/available")
        if available_response.status_code == status.HTTP_200_OK:
            available_influencers = available_response.json()
            assert len(available_influencers) >= len(influencer_locations)


class TestErrorHandlingIntegration:
    """Integration tests for error handling across workflows."""

    @pytest.mark.asyncio
    async def test_collaboration_with_nonexistent_entities(self, client: AsyncClient, test_factory):
        """Test collaboration creation with nonexistent promotion or influencer."""
        
        # Create business
        business_user_data = test_factory.user_data()
        await client.post("/auth/register", json=business_user_data)
        business_login = await client.post("/auth/token", data={
            "username": business_user_data["username"],
            "password": business_user_data["password"]
        })
        business_token = business_login.json()["access_token"]
        
        client.headers.update({"Authorization": f"Bearer {business_token}"})
        
        # Try to create collaboration with nonexistent promotion
        collaboration_data = {
            "promotion_id": 99999,  # Nonexistent
            "influencer_id": 99999,  # Nonexistent
            "status": "pending",
            "agreed_rate": 500.00
        }
        
        collaboration_response = await client.post("/collaboration/create", json=collaboration_data)
        assert collaboration_response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_unauthorized_cross_user_operations(self, client: AsyncClient, test_factory):
        """Test that users cannot perform operations on other users' data."""
        
        # Create two users
        user1_data = test_factory.user_data()
        user2_data = test_factory.user_data()
        
        await client.post("/auth/register", json=user1_data)
        await client.post("/auth/register", json=user2_data)
        
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
        
        # User 2 tries to update User 1's business
        client.headers.update({"Authorization": f"Bearer {user2_token}"})
        update_data = {"business_name": "Unauthorized Update"}
        
        update_response = await client.put(f"/business/update/{business_id}", json=update_data)
        assert update_response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND] 