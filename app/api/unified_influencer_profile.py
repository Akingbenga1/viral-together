from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional
from app.core.dependencies import get_db, get_current_user
from app.db.models.influencer import Influencer
from app.db.models.location import InfluencerOperationalLocation
from app.db.models.influencer_coaching import InfluencerCoachingGroup, InfluencerCoachingMember
from app.db.models.rate_card import RateCard
from app.db.models.influencers_targets import InfluencersTargets
from app.db.models.social_media_platform import SocialMediaPlatform
from app.db.models.user import User
from app.db.models.country import Country
from app.schemas.unified_influencer_profile import UnifiedInfluencerProfile, UnifiedInfluencerProfileResponse
from app.core.query_helpers import safe_scalar_one_or_none
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/unified-influencer-profile", tags=["unified-influencer-profile"])

@router.get("/{influencer_id}", response_model=UnifiedInfluencerProfileResponse)
async def get_unified_influencer_profile(
    influencer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get unified influencer profile containing all associated data in a single response.
    
    This endpoint replaces the need for multiple API calls by gathering:
    - Core influencer data with user and country info
    - Operational locations
    - Coaching groups (as coach and member)
    - Rate cards with platform info
    - Rate summary statistics
    - Influencer targets/goals
    - Social media platforms
    """
    try:
        logger.info(f"Fetching unified profile for influencer ID: {influencer_id}")
        
        # 1. Get core influencer data with all relationships
        influencer_query = (
            select(Influencer)
            .options(
                selectinload(Influencer.user),
                selectinload(Influencer.base_country),
                selectinload(Influencer.collaboration_countries),
                selectinload(Influencer.operational_locations),
                selectinload(Influencer.rate_cards).selectinload(RateCard.platform),
                selectinload(Influencer.coaching_groups),
                selectinload(Influencer.coaching_memberships).selectinload(InfluencerCoachingMember.group)
            )
            .where(Influencer.id == influencer_id)
        )
        
        result = await db.execute(influencer_query)
        influencer = await safe_scalar_one_or_none(result)
        
        if not influencer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Influencer with ID {influencer_id} not found"
            )
        
        logger.info(f"Found influencer: {influencer.user.first_name} {influencer.user.last_name}")
        
        # 2. Get influencer targets
        targets_query = select(InfluencersTargets).where(InfluencersTargets.user_id == influencer.user_id)
        targets_result = await db.execute(targets_query)
        influencer_targets = await safe_scalar_one_or_none(targets_result)
        
        # 3. Get all social media platforms
        platforms_query = select(SocialMediaPlatform)
        platforms_result = await db.execute(platforms_query)
        social_media_platforms = platforms_result.scalars().all()
        
        # 4. Calculate rate summary
        rate_summary = None
        if influencer.rate_cards:
            rates = [card.calculate_total_rate() for card in influencer.rate_cards]
            rate_summary = {
                "average_rate": sum(rates) / len(rates) if rates else None,
                "min_rate": min(rates) if rates else None,
                "max_rate": max(rates) if rates else None,
                "total_cards": len(influencer.rate_cards)
            }
        
        # 5. Get coaching groups where this influencer is a member
        member_groups_query = (
            select(InfluencerCoachingGroup)
            .join(InfluencerCoachingMember)
            .where(InfluencerCoachingMember.member_influencer_id == influencer_id)
        )
        member_groups_result = await db.execute(member_groups_query)
        coaching_groups_as_member = member_groups_result.scalars().all()
        
        # 6. Build the unified response using the factory method
        unified_profile = UnifiedInfluencerProfileResponse.from_sqlalchemy_models(
            influencer=influencer,
            operational_locations=influencer.operational_locations,
            coaching_groups_as_coach=influencer.coaching_groups,
            coaching_groups_as_member=coaching_groups_as_member,
            rate_cards=influencer.rate_cards,
            rate_summary=rate_summary,
            influencer_targets=influencer_targets,
            social_media_platforms=social_media_platforms
        )
        
        logger.info(f"Successfully gathered unified profile with {unified_profile.total_data_points} data points")
        
        return unified_profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching unified influencer profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching unified influencer profile: {str(e)}"
        )

@router.get("/user/{user_id}", response_model=UnifiedInfluencerProfileResponse)
async def get_unified_influencer_profile_by_user_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get unified influencer profile by user ID instead of influencer ID.
    This is useful when you have the user ID but need to find the associated influencer.
    """
    try:
        logger.info(f"Fetching unified profile for user ID: {user_id}")
        
        # First find the influencer by user_id
        influencer_query = (
            select(Influencer)
            .where(Influencer.user_id == user_id)
        )
        
        result = await db.execute(influencer_query)
        influencer = await safe_scalar_one_or_none(result)
        
        if not influencer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No influencer found for user ID {user_id}"
            )
        
        # Use the existing endpoint logic
        return await get_unified_influencer_profile(influencer.id, db, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching unified influencer profile by user ID: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching unified influencer profile: {str(e)}"
        )

@router.get("/", response_model=List[UnifiedInfluencerProfileResponse])
async def get_all_unified_influencer_profiles(
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get all unified influencer profiles with pagination.
    Use with caution as this can be resource-intensive.
    """
    try:
        logger.info(f"Fetching {limit} unified profiles starting from offset {offset}")
        
        # Get influencers with pagination
        influencers_query = (
            select(Influencer)
            .options(
                selectinload(Influencer.user),
                selectinload(Influencer.base_country),
                selectinload(Influencer.collaboration_countries),
                selectinload(Influencer.operational_locations),
                selectinload(Influencer.rate_cards).selectinload(RateCard.platform),
                selectinload(Influencer.coaching_groups),
                selectinload(Influencer.coaching_memberships).selectinload(InfluencerCoachingMember.group)
            )
            .limit(limit)
            .offset(offset)
        )
        
        result = await db.execute(influencers_query)
        influencers = result.scalars().all()
        
        unified_profiles = []
        for influencer in influencers:
            # Get influencer targets
            targets_query = select(InfluencersTargets).where(InfluencersTargets.user_id == influencer.user_id)
            targets_result = await db.execute(targets_query)
            influencer_targets = await safe_scalar_one_or_none(targets_result)
            
            # Get coaching groups where this influencer is a member
            member_groups_query = (
                select(InfluencerCoachingGroup)
                .join(InfluencerCoachingMember)
                .where(InfluencerCoachingMember.member_influencer_id == influencer.id)
            )
            member_groups_result = await db.execute(member_groups_query)
            coaching_groups_as_member = member_groups_result.scalars().all()
            
            # Calculate rate summary
            rate_summary = None
            if influencer.rate_cards:
                rates = [card.calculate_total_rate() for card in influencer.rate_cards]
                rate_summary = {
                    "average_rate": sum(rates) / len(rates) if rates else None,
                    "min_rate": min(rates) if rates else None,
                    "max_rate": max(rates) if rates else None,
                    "total_cards": len(influencer.rate_cards)
                }
            
            # Get all social media platforms (same for all influencers)
            platforms_query = select(SocialMediaPlatform)
            platforms_result = await db.execute(platforms_query)
            social_media_platforms = platforms_result.scalars().all()
            
            unified_profile = UnifiedInfluencerProfileResponse.from_sqlalchemy_models(
                influencer=influencer,
                operational_locations=influencer.operational_locations,
                coaching_groups_as_coach=influencer.coaching_groups,
                coaching_groups_as_member=coaching_groups_as_member,
                rate_cards=influencer.rate_cards,
                rate_summary=rate_summary,
                influencer_targets=influencer_targets,
                social_media_platforms=social_media_platforms
            )
            
            unified_profiles.append(unified_profile)
        
        logger.info(f"Successfully fetched {len(unified_profiles)} unified profiles")
        return unified_profiles
        
    except Exception as e:
        logger.error(f"Error fetching all unified influencer profiles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching unified influencer profiles: {str(e)}"
        )
