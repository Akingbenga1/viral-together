from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
import uuid

from app.db.session import get_db
from app.db.models import Influencer, InfluencerFansRequest, Country, InfluencerSocialMedia
from app.schemas.influencer_fans_request import (
    InfluencerFansRequestCreate,
    InfluencerFansRequestRead,
    InfluencerFansRequestUpdate,
    InfluencerFansRequestsByCountry,
    InfluencerListItem,
    InfluencerListResponse
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/influencers/public", response_model=InfluencerListResponse, status_code=status.HTTP_200_OK)
async def get_public_influencers_list(
    page: int = 1,
    limit: int = 12,
    country_id: Optional[int] = None,
    name_search: Optional[str] = None,
    username_search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of all influencers with their basic info and social media handles.
    This endpoint is public and doesn't require authentication.

    Pagination parameters:
    - page: Page number (default: 1)
    - limit: Items per page (default: 12)

    Search parameters (OR logic - results match ANY of the provided filters):
    - country_id: Filter by base country ID
    - name_search: Search by first name or last name (case-insensitive)
    - username_search: Search by username/handle (case-insensitive)

    Example: If you search with name_search="John" and country_id=1, you'll get:
    - All influencers with "John" in their name (from any country), OR
    - All influencers from country 1 (with any name)
    """
    try:
        # Build base query for counting
        count_query = select(func.count(Influencer.id))

        # Build query for fetching data
        query = (
            select(Influencer)
            .options(
                selectinload(Influencer.user),
                selectinload(Influencer.base_country),
                selectinload(Influencer.social_media_accounts)
            )
        )

        # Apply filters to both queries using OR logic
        filters = []
        need_user_join = False

        # Filter by country if provided
        if country_id:
            filters.append(Influencer.base_country_id == country_id)

        # Search by name (first_name or last_name)
        if name_search:
            search_term = f"%{name_search}%"
            name_filter = func.lower(func.concat(User.first_name, ' ', User.last_name)).like(func.lower(search_term))
            filters.append(name_filter)
            need_user_join = True

        # Search by username
        if username_search:
            search_term = f"%{username_search}%"
            username_filter = func.lower(User.username).like(func.lower(search_term))
            filters.append(username_filter)
            need_user_join = True

        # Add User join if needed for name or username search
        if need_user_join:
            count_query = count_query.join(User, User.id == Influencer.user_id)
            query = query.join(User, User.id == Influencer.user_id)

        # Apply all filters with OR logic (any filter can match)
        if filters:
            count_query = count_query.where(or_(*filters))
            query = query.where(or_(*filters))

        # Get total count
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Calculate pagination
        skip = (page - 1) * limit
        total_pages = (total + limit - 1) // limit if total > 0 else 0

        # Add pagination to main query
        query = query.offset(skip).limit(limit)

        result = await db.execute(query)
        influencers = result.scalars().all()

        # Transform to response format
        influencer_list = []
        for influencer in influencers:
            # Count total requests for this influencer (handle table not existing)
            total_requests = 0
            try:
                count_query = select(func.count(InfluencerFansRequest.id)).where(
                    InfluencerFansRequest.influencer_id == influencer.id
                )
                count_result = await db.execute(count_query)
                total_requests = count_result.scalar() or 0
            except Exception as count_error:
                # Table might not exist yet if migration hasn't been run
                logger.warning(f"Could not count requests (table may not exist): {str(count_error)}")
                total_requests = 0

            # Get social media handles
            social_media_handles = []
            for sm in influencer.social_media_accounts:
                social_media_handles.append({
                    "platform_id": sm.social_media_platform_id,
                    "handle": sm.handle,
                    "follower_count": sm.follower_count
                })

            influencer_list.append(InfluencerListItem(
                id=influencer.id,
                user_id=influencer.user_id,
                username=influencer.user.username,
                first_name=influencer.user.first_name,
                last_name=influencer.user.last_name,
                bio=influencer.bio,
                profile_image_url=influencer.profile_image_url,
                base_country_id=influencer.base_country_id,
                base_country_name=influencer.base_country.name if influencer.base_country else None,
                social_media_handles=social_media_handles,
                total_requests=total_requests
            ))

        return InfluencerListResponse(
            data=influencer_list,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages
        )

    except Exception as e:
        logger.error(f"Error fetching public influencers list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch influencers: {str(e)}"
        )


@router.post("/influencers/{influencer_id}/invite-requests", response_model=InfluencerFansRequestRead, status_code=status.HTTP_201_CREATED)
async def create_invite_request(
    influencer_id: int,
    request_data: InfluencerFansRequestCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new invite request for an influencer.
    This endpoint does not require authentication - anyone can send invite requests.
    """
    try:
        # Verify influencer exists
        influencer_query = await db.execute(
            select(Influencer).where(Influencer.id == influencer_id)
        )
        influencer = influencer_query.scalars().first()

        if not influencer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Influencer with ID {influencer_id} not found"
            )

        # Verify country exists
        country_query = await db.execute(
            select(Country).where(Country.id == request_data.country_id)
        )
        country = country_query.scalars().first()

        if not country:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Country with ID {request_data.country_id} not found"
            )

        # Create the request
        new_request = InfluencerFansRequest(
            uuid=str(uuid.uuid4()),
            influencer_id=influencer_id,
            requester_name=request_data.requester_name,
            requester_email=request_data.requester_email,
            country_id=request_data.country_id,
            city_name=request_data.city_name,
            latitude=request_data.latitude,
            longitude=request_data.longitude,
            country_code=request_data.country_code,
            country_name=request_data.country_name,
            region_name=request_data.region_name,
            region_code=request_data.region_code,
            message=request_data.message,
            status='pending'
        )

        db.add(new_request)
        await db.commit()
        await db.refresh(new_request)

        logger.info(f"Created invite request {new_request.id} for influencer {influencer_id}")

        return new_request

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating invite request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create invite request: {str(e)}"
        )


@router.get("/influencers/{influencer_id}/invite-requests", response_model=List[InfluencerFansRequestsByCountry], status_code=status.HTTP_200_OK)
async def get_influencer_invite_requests(
    influencer_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all invite requests for a specific influencer, grouped by country.
    This endpoint is public.
    """
    try:
        # Verify influencer exists
        influencer_query = await db.execute(
            select(Influencer).where(Influencer.id == influencer_id)
        )
        influencer = influencer_query.scalars().first()

        if not influencer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Influencer with ID {influencer_id} not found"
            )

        # Get all requests for this influencer
        requests_query = await db.execute(
            select(InfluencerFansRequest)
            .options(selectinload(InfluencerFansRequest.country))
            .where(InfluencerFansRequest.influencer_id == influencer_id)
            .order_by(desc(InfluencerFansRequest.created_at))
        )
        requests = requests_query.scalars().all()

        # Group by country
        grouped_by_country = {}
        for req in requests:
            country_id = req.country_id
            if country_id not in grouped_by_country:
                grouped_by_country[country_id] = {
                    "country_id": country_id,
                    "country_name": req.country.name if req.country else "Unknown",
                    "country_code": req.country_code,
                    "request_count": 0,
                    "requests": []
                }

            grouped_by_country[country_id]["request_count"] += 1
            grouped_by_country[country_id]["requests"].append(req)

        # Convert to list and sort by request count
        result = list(grouped_by_country.values())
        result.sort(key=lambda x: x["request_count"], reverse=True)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching invite requests for influencer {influencer_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch invite requests: {str(e)}"
        )


@router.get("/influencers/{influencer_id}/invite-requests/all", response_model=List[InfluencerFansRequestRead], status_code=status.HTTP_200_OK)
async def get_all_invite_requests_for_influencer(
    influencer_id: int,
    skip: int = 0,
    limit: int = 100,
    country_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all invite requests for a specific influencer with optional filters.
    """
    try:
        # Build query
        query = select(InfluencerFansRequest).where(
            InfluencerFansRequest.influencer_id == influencer_id
        )

        # Apply filters
        if country_id:
            query = query.where(InfluencerFansRequest.country_id == country_id)

        if status_filter:
            query = query.where(InfluencerFansRequest.status == status_filter)

        # Order by created_at desc and apply pagination
        query = query.order_by(desc(InfluencerFansRequest.created_at)).offset(skip).limit(limit)

        result = await db.execute(query)
        requests = result.scalars().all()

        return requests

    except Exception as e:
        logger.error(f"Error fetching all invite requests: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch invite requests: {str(e)}"
        )


@router.patch("/invite-requests/{request_id}", response_model=InfluencerFansRequestRead, status_code=status.HTTP_200_OK)
async def update_invite_request(
    request_id: int,
    update_data: InfluencerFansRequestUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an invite request (status, message, etc.).
    This endpoint does not require authentication.
    """
    try:
        # Get the request
        query = await db.execute(
            select(InfluencerFansRequest).where(InfluencerFansRequest.id == request_id)
        )
        invite_request = query.scalars().first()

        if not invite_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invite request with ID {request_id} not found"
            )

        # Update fields
        if update_data.status:
            invite_request.status = update_data.status

        if update_data.message:
            invite_request.message = update_data.message

        invite_request.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(invite_request)

        logger.info(f"Updated invite request {request_id}")

        return invite_request

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating invite request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update invite request: {str(e)}"
        )


@router.delete("/invite-requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invite_request(
    request_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an invite request.
    This endpoint does not require authentication.
    """
    try:
        # Get the request
        query = await db.execute(
            select(InfluencerFansRequest).where(InfluencerFansRequest.id == request_id)
        )
        invite_request = query.scalars().first()

        if not invite_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invite request with ID {request_id} not found"
            )

        await db.delete(invite_request)
        await db.commit()

        logger.info(f"Deleted invite request {request_id}")

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting invite request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete invite request: {str(e)}"
        )
