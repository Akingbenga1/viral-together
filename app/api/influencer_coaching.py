from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
import secrets
import string
from datetime import datetime

from app.db.session import get_db
from app.api.auth import get_current_user_dependency
from app.db.models.influencer_coaching import (
    InfluencerCoachingGroup, 
    InfluencerCoachingMember, 
    InfluencerCoachingSession, 
    InfluencerCoachingMessage
)
from app.db.models.influencer import Influencer
from app.schemas.influencer_coaching import (
    InfluencerCoachingGroupCreate, 
    InfluencerCoachingGroupUpdate, 
    InfluencerCoachingGroup as InfluencerCoachingGroupSchema,
    InfluencerCoachingMemberCreate, 
    InfluencerCoachingMemberUpdate, 
    InfluencerCoachingMember as InfluencerCoachingMemberSchema,
    InfluencerCoachingSessionCreate, 
    InfluencerCoachingSessionUpdate, 
    InfluencerCoachingSession as InfluencerCoachingSessionSchema,
    InfluencerCoachingMessageCreate, 
    InfluencerCoachingMessage as InfluencerCoachingMessageSchema,
    JoinCoachingGroupRequest,
    JoinGroupResponse, 
    GenerateJoinCodeResponse
)
from app.db.models.user import User

router = APIRouter()

def generate_join_code(length: int = 8) -> str:
    """Generate a random join code"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

async def get_current_influencer(db: AsyncSession, current_user: User) -> Influencer:
    """Get the current user's influencer profile"""
    result = await db.execute(select(Influencer).filter(Influencer.user_id == current_user.id))
    influencer = result.scalars().first()
    
    if not influencer:
        # Check if user has influencer role
        from app.db.models import UserRole, Role
        role_result = await db.execute(
            select(Role).join(UserRole).filter(
                UserRole.user_id == current_user.id,
                Role.name == "influencer"
            )
        )
        has_influencer_role = role_result.scalar_one_or_none() is not None
        
        if has_influencer_role:
            # User has influencer role but no profile - create a basic one
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Creating basic influencer profile for user {current_user.id} who has influencer role but no profile")
            
            from app.db.models.country import Country
            
            # Get a default country (US as fallback)
            country_result = await db.execute(select(Country).filter(Country.code == "US"))
            default_country = country_result.scalar_one_or_none()
            
            if not default_country:
                # If no US country, get any country
                country_result = await db.execute(select(Country).limit(1))
                default_country = country_result.scalar_one_or_none()
            
            if not default_country:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="No countries found in database. Please contact administrator."
                )
            
            # Create basic influencer profile
            influencer = Influencer(
                user_id=current_user.id,
                bio="",
                base_country_id=default_country.id,
                availability=True
            )
            db.add(influencer)
            await db.commit()
            await db.refresh(influencer)
            logger.info(f"Successfully created influencer profile with ID {influencer.id} for user {current_user.id}")
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You need to have an influencer role to access coaching features. Please contact an administrator."
            )
    
    return influencer

# Coaching Group Endpoints
@router.post("/coaching-groups/", response_model=InfluencerCoachingGroupSchema)
async def create_coaching_group(
    group_data: InfluencerCoachingGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Create a new coaching group"""
    influencer = await get_current_influencer(db, current_user)
    
    # Generate unique join code
    join_code = generate_join_code()
    while True:
        result = await db.execute(select(InfluencerCoachingGroup).filter(InfluencerCoachingGroup.join_code == join_code))
        if not result.scalar_one_or_none():
            break
        join_code = generate_join_code()
    
    # Validate price for paid groups
    if group_data.is_paid and not group_data.price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price is required for paid coaching groups"
        )
    
    db_group = InfluencerCoachingGroup(
        coach_influencer_id=influencer.id,
        join_code=join_code,
        **group_data.dict()
    )
    db.add(db_group)
    await db.commit()
    await db.refresh(db_group)
    return db_group

@router.get("/coaching-groups/", response_model=List[InfluencerCoachingGroupSchema])
async def get_my_coaching_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Get all coaching groups created by the current influencer"""
    influencer = await get_current_influencer(db, current_user)
    result = await db.execute(select(InfluencerCoachingGroup).filter(
        InfluencerCoachingGroup.coach_influencer_id == influencer.id
    ))
    groups = result.scalars().all()
    return groups

@router.get("/coaching-groups/{group_id}", response_model=InfluencerCoachingGroupSchema)
async def get_coaching_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Get a specific coaching group"""
    influencer = await get_current_influencer(db, current_user)
    result = await db.execute(select(InfluencerCoachingGroup).filter(
        and_(
            InfluencerCoachingGroup.id == group_id,
            InfluencerCoachingGroup.coach_influencer_id == influencer.id
        )
    ))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coaching group not found"
        )
    return group

@router.put("/coaching-groups/{group_id}", response_model=InfluencerCoachingGroupSchema)
async def update_coaching_group(
    group_id: int,
    group_data: InfluencerCoachingGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Update a coaching group"""
    influencer = await get_current_influencer(db, current_user)
    result = await db.execute(
        select(InfluencerCoachingGroup).filter(
            and_(
                InfluencerCoachingGroup.id == group_id,
                InfluencerCoachingGroup.coach_influencer_id == influencer.id
            )
        )
    )
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coaching group not found"
        )
    
    # Update fields
    update_data = group_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(group, field, value)
    
    await db.commit()
    await db.refresh(group)
    return group

@router.delete("/coaching-groups/{group_id}")
async def delete_coaching_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Delete a coaching group (only group coach can do this)"""
    influencer = await get_current_influencer(db, current_user)
    
    # Verify user is the coach of this group
    result = await db.execute(
        select(InfluencerCoachingGroup).filter(
            and_(
                InfluencerCoachingGroup.id == group_id,
                InfluencerCoachingGroup.coach_influencer_id == influencer.id
            )
        )
    )
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coaching group not found or you are not the coach"
        )
    
    # Check if group has members
    if group.current_members > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete group with {group.current_members} members. Consider archiving instead."
        )
    
    # Delete the group (cascade will handle related records)
    await db.delete(group)
    await db.commit()
    
    return {"message": "Coaching group deleted successfully"}

@router.patch("/coaching-groups/{group_id}/archive")
async def archive_coaching_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Archive a coaching group (only group coach can do this)"""
    influencer = await get_current_influencer(db, current_user)
    
    # Verify user is the coach of this group
    result = await db.execute(
        select(InfluencerCoachingGroup).filter(
            and_(
                InfluencerCoachingGroup.id == group_id,
                InfluencerCoachingGroup.coach_influencer_id == influencer.id
            )
        )
    )
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coaching group not found or you are not the coach"
        )
    
    # Archive the group by setting is_active to False
    group.is_active = False
    await db.commit()
    await db.refresh(group)
    
    return {"message": f"Coaching group '{group.name}' has been archived successfully"}

@router.post("/coaching-groups/{group_id}/generate-code", response_model=GenerateJoinCodeResponse)
async def regenerate_join_code(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Regenerate join code for a coaching group"""
    influencer = await get_current_influencer(db, current_user)
    result = await db.execute(
        select(InfluencerCoachingGroup).filter(
            and_(
                InfluencerCoachingGroup.id == group_id,
                InfluencerCoachingGroup.coach_influencer_id == influencer.id
            )
        )
    )
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coaching group not found"
        )
    
    # Generate new unique join code
    join_code = generate_join_code()
    while True:
        result = await db.execute(
            select(InfluencerCoachingGroup).filter(InfluencerCoachingGroup.join_code == join_code)
        )
        if not result.scalar_one_or_none():
            break
        join_code = generate_join_code()
    
    group.join_code = join_code
    await db.commit()
    
    return GenerateJoinCodeResponse(
        join_code=join_code,
        group_id=group_id,
        message="Join code regenerated successfully"
    )

# Public Group Info Endpoint (no auth required)
@router.get("/coaching-groups/info/{join_code}")
async def get_group_info_by_code(
    join_code: str,
    db: AsyncSession = Depends(get_db)
):
    """Get public information about a coaching group by join code"""
    result = await db.execute(
        select(InfluencerCoachingGroup).filter(
            and_(
                InfluencerCoachingGroup.join_code == join_code,
                InfluencerCoachingGroup.is_active == True
            )
        )
    )
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coaching group not found or inactive"
        )
    
    return {
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "is_paid": group.is_paid,
        "price": group.price,
        "currency": group.currency,
        "current_members": group.current_members,
        "max_members": group.max_members,
        "is_active": group.is_active
    }

# Join Group Endpoints
@router.post("/coaching-groups/join", response_model=JoinGroupResponse)
async def join_coaching_group(
    join_data: JoinCoachingGroupRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Join a coaching group using join code"""
    influencer = await get_current_influencer(db, current_user)
    
    # Find group by join code
    result = await db.execute(
        select(InfluencerCoachingGroup).filter(
            and_(
                InfluencerCoachingGroup.join_code == join_data.join_code,
                InfluencerCoachingGroup.is_active == True
            )
        )
    )
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid join code or group is inactive"
        )
    
    # Check if already a member
    result = await db.execute(
        select(InfluencerCoachingMember).filter(
            and_(
                InfluencerCoachingMember.group_id == group.id,
                InfluencerCoachingMember.member_influencer_id == influencer.id
            )
        )
    )
    existing_member = result.scalar_one_or_none()
    
    if existing_member:
        return JoinGroupResponse(
            success=False,
            message="You are already a member of this coaching group",
            group=group
        )
    
    # Check if group is full
    if group.max_members and group.current_members >= group.max_members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coaching group is full"
        )
    
    # Determine payment status
    payment_status = "free"
    if group.is_paid:
        if join_data.payment_reference:
            payment_status = "paid"
        else:
            payment_status = "pending"
    
    # Create member record
    member = InfluencerCoachingMember(
        group_id=group.id,
        member_influencer_id=influencer.id,
        payment_status=payment_status,
        payment_reference=join_data.payment_reference
    )
    db.add(member)
    
    # Update group member count
    group.current_members += 1
    
    await db.commit()
    await db.refresh(member)
    await db.refresh(group)
    
    return JoinGroupResponse(
        success=True,
        message="Successfully joined coaching group",
        group=group,
        member=member
    )

@router.get("/coaching-groups/joined", response_model=List[InfluencerCoachingGroupSchema])
async def get_joined_coaching_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Get all coaching groups the current influencer has joined"""
    influencer = await get_current_influencer(db, current_user)
    
    # Get groups where user is a member
    result = await db.execute(select(InfluencerCoachingMember).filter(
        and_(
            InfluencerCoachingMember.member_influencer_id == influencer.id,
            InfluencerCoachingMember.is_active == True
        )
    ))
    memberships = result.scalars().all()
    
    group_ids = [membership.group_id for membership in memberships]
    if not group_ids:
        return []
    
    result = await db.execute(select(InfluencerCoachingGroup).filter(
        InfluencerCoachingGroup.id.in_(group_ids)
    ))
    groups = result.scalars().all()
    
    return groups

# Session Endpoints
@router.post("/coaching-groups/{group_id}/sessions", response_model=InfluencerCoachingSessionSchema)
async def create_coaching_session(
    group_id: int,
    session_data: InfluencerCoachingSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Create a new coaching session (only group coach can do this)"""
    influencer = await get_current_influencer(db, current_user)
    
    # Verify user is the coach of this group
    result = await db.execute(
        select(InfluencerCoachingGroup).filter(
            and_(
                InfluencerCoachingGroup.id == group_id,
                InfluencerCoachingGroup.coach_influencer_id == influencer.id
            )
        )
    )
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coaching group not found or you are not the coach"
        )
    
    session = InfluencerCoachingSession(
        group_id=group_id,
        **session_data.dict()
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

@router.get("/coaching-groups/{group_id}/sessions", response_model=List[InfluencerCoachingSessionSchema])
async def get_coaching_sessions(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Get all sessions for a coaching group (members and coach can access)"""
    influencer = await get_current_influencer(db, current_user)
    
    # Check if user is coach or member
    result = await db.execute(
        select(InfluencerCoachingGroup).filter(InfluencerCoachingGroup.id == group_id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coaching group not found"
        )
    
    is_coach = group.coach_influencer_id == influencer.id
    result = await db.execute(
        select(InfluencerCoachingMember).filter(
            and_(
                InfluencerCoachingMember.group_id == group_id,
                InfluencerCoachingMember.member_influencer_id == influencer.id,
                InfluencerCoachingMember.is_active == True
            )
        )
    )
    is_member = result.scalar_one_or_none()
    
    if not is_coach and not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member or coach to view sessions"
        )
    
    result = await db.execute(
        select(InfluencerCoachingSession).filter(
            InfluencerCoachingSession.group_id == group_id
        ).order_by(InfluencerCoachingSession.session_date.desc())
    )
    sessions = result.scalars().all()
    
    return sessions

# Message Endpoints
@router.post("/coaching-groups/{group_id}/messages", response_model=InfluencerCoachingMessageSchema)
async def send_message(
    group_id: int,
    message_data: InfluencerCoachingMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Send a message to a coaching group"""
    influencer = await get_current_influencer(db, current_user)
    
    # Check if user is coach or member
    result = await db.execute(
        select(InfluencerCoachingGroup).filter(InfluencerCoachingGroup.id == group_id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coaching group not found"
        )
    
    is_coach = group.coach_influencer_id == influencer.id
    result = await db.execute(
        select(InfluencerCoachingMember).filter(
            and_(
                InfluencerCoachingMember.group_id == group_id,
                InfluencerCoachingMember.member_influencer_id == influencer.id,
                InfluencerCoachingMember.is_active == True
            )
        )
    )
    is_member = result.scalar_one_or_none()
    
    if not is_coach and not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member or coach to send messages"
        )
    
    # Only coach can make announcements
    if message_data.is_announcement and not is_coach:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the coach can make announcements"
        )
    
    message = InfluencerCoachingMessage(
        group_id=group_id,
        sender_influencer_id=influencer.id,
        **message_data.dict()
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message

@router.get("/coaching-groups/{group_id}/messages", response_model=List[InfluencerCoachingMessageSchema])
async def get_messages(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Get all messages for a coaching group"""
    influencer = await get_current_influencer(db, current_user)
    
    # Check if user is coach or member
    result = await db.execute(
        select(InfluencerCoachingGroup).filter(InfluencerCoachingGroup.id == group_id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coaching group not found"
        )
    
    is_coach = group.coach_influencer_id == influencer.id
    result = await db.execute(
        select(InfluencerCoachingMember).filter(
            and_(
                InfluencerCoachingMember.group_id == group_id,
                InfluencerCoachingMember.member_influencer_id == influencer.id,
                InfluencerCoachingMember.is_active == True
            )
        )
    )
    is_member = result.scalar_one_or_none()
    
    if not is_coach and not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member or coach to view messages"
        )
    
    result = await db.execute(
        select(InfluencerCoachingMessage).filter(
            InfluencerCoachingMessage.group_id == group_id
        ).order_by(InfluencerCoachingMessage.created_at.desc())
    )
    messages = result.scalars().all()
    
    return messages
