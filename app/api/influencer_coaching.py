from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
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
    JoinGroupResponse,
    GenerateJoinCodeResponse
)
from app.db.models.user import User

router = APIRouter()

def generate_join_code(length: int = 8) -> str:
    """Generate a random join code"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def get_current_influencer(db: Session, current_user: User) -> Influencer:
    """Get the current user's influencer profile"""
    influencer = db.query(Influencer).filter(Influencer.user_id == current_user.id).first()
    if not influencer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Influencer profile not found. Please create an influencer profile first."
        )
    return influencer

# Coaching Group Endpoints
@router.post("/coaching-groups/", response_model=InfluencerCoachingGroupSchema)
def create_coaching_group(
    group_data: InfluencerCoachingGroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Create a new coaching group"""
    influencer = get_current_influencer(db, current_user)
    
    # Generate unique join code
    join_code = generate_join_code()
    while db.query(InfluencerCoachingGroup).filter(InfluencerCoachingGroup.join_code == join_code).first():
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
    db.commit()
    db.refresh(db_group)
    return db_group

@router.get("/coaching-groups/", response_model=List[InfluencerCoachingGroupSchema])
def get_my_coaching_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Get all coaching groups created by the current influencer"""
    influencer = get_current_influencer(db, current_user)
    groups = db.query(InfluencerCoachingGroup).filter(
        InfluencerCoachingGroup.coach_influencer_id == influencer.id
    ).all()
    return groups

@router.get("/coaching-groups/{group_id}", response_model=InfluencerCoachingGroupSchema)
def get_coaching_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Get a specific coaching group"""
    influencer = get_current_influencer(db, current_user)
    group = db.query(InfluencerCoachingGroup).filter(
        and_(
            InfluencerCoachingGroup.id == group_id,
            InfluencerCoachingGroup.coach_influencer_id == influencer.id
        )
    ).first()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coaching group not found"
        )
    return group

@router.put("/coaching-groups/{group_id}", response_model=InfluencerCoachingGroupSchema)
def update_coaching_group(
    group_id: int,
    group_data: InfluencerCoachingGroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Update a coaching group"""
    influencer = get_current_influencer(db, current_user)
    group = db.query(InfluencerCoachingGroup).filter(
        and_(
            InfluencerCoachingGroup.id == group_id,
            InfluencerCoachingGroup.coach_influencer_id == influencer.id
        )
    ).first()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coaching group not found"
        )
    
    # Update fields
    update_data = group_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(group, field, value)
    
    db.commit()
    db.refresh(group)
    return group

@router.post("/coaching-groups/{group_id}/generate-code", response_model=GenerateJoinCodeResponse)
def regenerate_join_code(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Regenerate join code for a coaching group"""
    influencer = get_current_influencer(db, current_user)
    group = db.query(InfluencerCoachingGroup).filter(
        and_(
            InfluencerCoachingGroup.id == group_id,
            InfluencerCoachingGroup.coach_influencer_id == influencer.id
        )
    ).first()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coaching group not found"
        )
    
    # Generate new unique join code
    join_code = generate_join_code()
    while db.query(InfluencerCoachingGroup).filter(InfluencerCoachingGroup.join_code == join_code).first():
        join_code = generate_join_code()
    
    group.join_code = join_code
    db.commit()
    
    return GenerateJoinCodeResponse(
        join_code=join_code,
        group_id=group_id,
        message="Join code regenerated successfully"
    )

# Public Group Info Endpoint (no auth required)
@router.get("/coaching-groups/info/{join_code}")
def get_group_info_by_code(
    join_code: str,
    db: Session = Depends(get_db)
):
    """Get public information about a coaching group by join code"""
    group = db.query(InfluencerCoachingGroup).filter(
        and_(
            InfluencerCoachingGroup.join_code == join_code,
            InfluencerCoachingGroup.is_active == True
        )
    ).first()
    
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
def join_coaching_group(
    join_data: InfluencerCoachingMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Join a coaching group using join code"""
    influencer = get_current_influencer(db, current_user)
    
    # Find group by join code
    group = db.query(InfluencerCoachingGroup).filter(
        and_(
            InfluencerCoachingGroup.join_code == join_data.join_code,
            InfluencerCoachingGroup.is_active == True
        )
    ).first()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid join code or group is inactive"
        )
    
    # Check if already a member
    existing_member = db.query(InfluencerCoachingMember).filter(
        and_(
            InfluencerCoachingMember.group_id == group.id,
            InfluencerCoachingMember.member_influencer_id == influencer.id
        )
    ).first()
    
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
    
    db.commit()
    db.refresh(member)
    
    return JoinGroupResponse(
        success=True,
        message="Successfully joined coaching group",
        group=group,
        member=member
    )

@router.get("/coaching-groups/joined", response_model=List[InfluencerCoachingGroupSchema])
def get_joined_coaching_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Get all coaching groups the current influencer has joined"""
    influencer = get_current_influencer(db, current_user)
    
    # Get groups where user is a member
    memberships = db.query(InfluencerCoachingMember).filter(
        and_(
            InfluencerCoachingMember.member_influencer_id == influencer.id,
            InfluencerCoachingMember.is_active == True
        )
    ).all()
    
    group_ids = [membership.group_id for membership in memberships]
    groups = db.query(InfluencerCoachingGroup).filter(
        InfluencerCoachingGroup.id.in_(group_ids)
    ).all()
    
    return groups

# Session Endpoints
@router.post("/coaching-groups/{group_id}/sessions", response_model=InfluencerCoachingSessionSchema)
def create_coaching_session(
    group_id: int,
    session_data: InfluencerCoachingSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Create a new coaching session (only group coach can do this)"""
    influencer = get_current_influencer(db, current_user)
    
    # Verify user is the coach of this group
    group = db.query(InfluencerCoachingGroup).filter(
        and_(
            InfluencerCoachingGroup.id == group_id,
            InfluencerCoachingGroup.coach_influencer_id == influencer.id
        )
    ).first()
    
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
    db.commit()
    db.refresh(session)
    return session

@router.get("/coaching-groups/{group_id}/sessions", response_model=List[InfluencerCoachingSessionSchema])
def get_coaching_sessions(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Get all sessions for a coaching group (members and coach can access)"""
    influencer = get_current_influencer(db, current_user)
    
    # Check if user is coach or member
    group = db.query(InfluencerCoachingGroup).filter(InfluencerCoachingGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coaching group not found"
        )
    
    is_coach = group.coach_influencer_id == influencer.id
    is_member = db.query(InfluencerCoachingMember).filter(
        and_(
            InfluencerCoachingMember.group_id == group_id,
            InfluencerCoachingMember.member_influencer_id == influencer.id,
            InfluencerCoachingMember.is_active == True
        )
    ).first()
    
    if not is_coach and not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member or coach to view sessions"
        )
    
    sessions = db.query(InfluencerCoachingSession).filter(
        InfluencerCoachingSession.group_id == group_id
    ).order_by(InfluencerCoachingSession.session_date.desc()).all()
    
    return sessions

# Message Endpoints
@router.post("/coaching-groups/{group_id}/messages", response_model=InfluencerCoachingMessageSchema)
def send_message(
    group_id: int,
    message_data: InfluencerCoachingMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Send a message to a coaching group"""
    influencer = get_current_influencer(db, current_user)
    
    # Check if user is coach or member
    group = db.query(InfluencerCoachingGroup).filter(InfluencerCoachingGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coaching group not found"
        )
    
    is_coach = group.coach_influencer_id == influencer.id
    is_member = db.query(InfluencerCoachingMember).filter(
        and_(
            InfluencerCoachingMember.group_id == group_id,
            InfluencerCoachingMember.member_influencer_id == influencer.id,
            InfluencerCoachingMember.is_active == True
        )
    ).first()
    
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
    db.commit()
    db.refresh(message)
    return message

@router.get("/coaching-groups/{group_id}/messages", response_model=List[InfluencerCoachingMessageSchema])
def get_messages(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Get all messages for a coaching group"""
    influencer = get_current_influencer(db, current_user)
    
    # Check if user is coach or member
    group = db.query(InfluencerCoachingGroup).filter(InfluencerCoachingGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coaching group not found"
        )
    
    is_coach = group.coach_influencer_id == influencer.id
    is_member = db.query(InfluencerCoachingMember).filter(
        and_(
            InfluencerCoachingMember.group_id == group_id,
            InfluencerCoachingMember.member_influencer_id == influencer.id,
            InfluencerCoachingMember.is_active == True
        )
    ).first()
    
    if not is_coach and not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member or coach to view messages"
        )
    
    messages = db.query(InfluencerCoachingMessage).filter(
        InfluencerCoachingMessage.group_id == group_id
    ).order_by(InfluencerCoachingMessage.created_at.desc()).all()
    
    return messages
