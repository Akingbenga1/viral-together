from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union
import logging

from app.db.session import get_db
from app.api.auth import get_current_user_dependency
from app.schemas.user import UserRead
from app.services.user_service import UserService
from app.api.users.user_models import (
    UserProfileUpdate, 
    UserPasswordUpdate, 
    UserProfileResponse,
    UserUpdateResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["user-profile"])


@router.put("/profile/update", response_model=UserUpdateResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: UserRead = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user profile information.
    
    This endpoint allows authenticated users to update their own profile information
    including first name, last name, email, and mobile number.
    
    - **first_name**: User's first name (optional)
    - **last_name**: User's last name (optional) 
    - **email**: User's email address (optional, must be unique)
    - **mobile_number**: User's mobile number (optional)
    
    Returns the updated user profile information.
    """
    logger.info(f"User {current_user.id} ({current_user.username}) updating profile")
    try:
        user_service = UserService(db)
        
        # Update the user profile
        updated_user = await user_service.update_user_profile(
            user_id=current_user.id,
            profile_update=profile_update
        )
        
        # Convert to response model
        user_response = UserProfileResponse(
            id=updated_user.id,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
            username=updated_user.username,
            email=updated_user.email,
            mobile_number=updated_user.mobile_number,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )
        
        logger.info(f"User {current_user.id} profile updated successfully")
        return UserUpdateResponse(
            message="Profile updated successfully",
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating user profile for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating your profile"
        )


@router.put("/profile/password", response_model=UserUpdateResponse)
async def update_user_password(
    password_update: UserPasswordUpdate,
    current_user: UserRead = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user password.
    
    This endpoint allows authenticated users to update their password.
    The user must provide their current password for verification.
    
    - **current_password**: User's current password (required for verification)
    - **new_password**: New password (must meet security requirements)
    - **confirm_password**: Confirmation of new password (must match new_password)
    
    Password requirements:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter  
    - Contains at least one digit
    
    Returns the updated user profile information.
    """
    logger.info(f"User {current_user.id} ({current_user.username}) updating password")
    try:
        user_service = UserService(db)
        
        # Update the user password
        updated_user = await user_service.update_user_password(
            user_id=current_user.id,
            password_update=password_update
        )
        
        # Convert to response model
        user_response = UserProfileResponse(
            id=updated_user.id,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
            username=updated_user.username,
            email=updated_user.email,
            mobile_number=updated_user.mobile_number,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )
        
        logger.info(f"User {current_user.id} password updated successfully")
        return UserUpdateResponse(
            message="Password updated successfully",
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating password for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating your password"
        )


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: UserRead = Depends(get_current_user_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's profile information.
    
    This endpoint returns the authenticated user's profile information
    including personal details and account information.
    
    Returns the user's profile information.
    """
    logger.info(f"User {current_user.id} ({current_user.username}) retrieving profile")
    try:
        user_service = UserService(db)
        
        # Get the user profile
        user = await user_service.get_user_profile(user_id=current_user.id)
        
        # Convert to response model
        user_response = UserProfileResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            email=user.email,
            mobile_number=user.mobile_number,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        return user_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting user profile for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving your profile"
        )
