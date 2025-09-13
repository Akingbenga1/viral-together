from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import logging

from app.db.session import get_db
from app.api.auth import get_current_user_dependency
from app.schemas.user import UserRead
from app.core.dependencies import require_any_role
from app.services.user_service import UserService
from app.api.admin.admin_user_models import (
    AdminUserProfileUpdate, 
    AdminUserProfileResponse,
    AdminUserUpdateResponse,
    AdminUserListResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin-users"])


@router.put("/users/{user_id}/profile_update", response_model=AdminUserUpdateResponse)
async def admin_update_user_profile(
    user_id: int = Path(..., description="ID of the user to update"),
    profile_update: AdminUserProfileUpdate = Body(...),
    current_user: UserRead = Depends(require_any_role(["admin", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin endpoint to update any user's profile information and password.
    
    This endpoint allows administrators and super administrators to update
    any user's profile information including first name, last name, email,
    mobile number, username, and password.
    
    **Access Control**: Only users with 'admin' or 'super_admin' roles can access this endpoint.
    
    **Parameters:**
    - **user_id**: ID of the user whose profile will be updated
    - **first_name**: User's first name (optional)
    - **last_name**: User's last name (optional) 
    - **email**: User's email address (optional, must be unique)
    - **mobile_number**: User's mobile number (optional)
    - **username**: User's username (optional, must be unique)
    - **new_password**: New password (optional, must meet security requirements)
    - **confirm_password**: Confirmation of new password (optional, must match new_password)
    
    **Password Requirements (if updating password):**
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter  
    - Contains at least one digit
    - confirm_password must match new_password
    
    **Returns:** Updated user profile information with admin audit trail.
    """
    logger.info(f"Admin {current_user.id} ({current_user.username}) updating user {user_id} profile")
    try:
        user_service = UserService(db)
        
        # Update the user profile
        updated_user = await user_service.admin_update_user_profile(
            target_user_id=user_id,
            profile_update=profile_update,
            admin_user_id=current_user.id
        )
        
        # Convert to response model
        user_response = AdminUserProfileResponse(
            id=updated_user.id,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
            username=updated_user.username,
            email=updated_user.email,
            mobile_number=updated_user.mobile_number,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at
        )
        
        logger.info(f"Admin {current_user.id} successfully updated user {user_id} profile")
        return AdminUserUpdateResponse(
            message=f"User profile updated successfully by admin {current_user.username}",
            user=user_response,
            updated_by=current_user.username
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in admin update user profile for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating the user profile"
        )


@router.get("/users/{user_id}/profile", response_model=AdminUserProfileResponse)
async def admin_get_user_profile(
    user_id: int = Path(..., description="ID of the user whose profile to retrieve"),
    current_user: UserRead = Depends(require_any_role(["admin", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin endpoint to get any user's profile information.
    
    This endpoint allows administrators and super administrators to retrieve
    any user's profile information for administrative purposes.
    
    **Access Control**: Only users with 'admin' or 'super_admin' roles can access this endpoint.
    
    **Parameters:**
    - **user_id**: ID of the user whose profile to retrieve
    
    **Returns:** User's profile information.
    """
    logger.info(f"Admin {current_user.id} ({current_user.username}) retrieving user {user_id} profile")
    try:
        user_service = UserService(db)
        
        # Get the user profile
        user = await user_service.admin_get_user_profile(
            target_user_id=user_id,
            admin_user_id=current_user.id
        )
        
        # Convert to response model
        user_response = AdminUserProfileResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            email=user.email,
            mobile_number=user.mobile_number,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        logger.info(f"Admin {current_user.id} successfully retrieved user {user_id} profile")
        return user_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in admin get user profile for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving the user profile"
        )


@router.get("/users", response_model=List[AdminUserListResponse])
async def admin_list_users(
    current_user: UserRead = Depends(require_any_role(["admin", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin endpoint to list all users.
    
    This endpoint allows administrators and super administrators to retrieve
    a list of all users in the system for administrative purposes.
    
    **Access Control**: Only users with 'admin' or 'super_admin' roles can access this endpoint.
    
    **Returns:** List of all users with their basic profile information.
    """
    logger.info(f"Admin {current_user.id} ({current_user.username}) listing all users")
    try:
        user_service = UserService(db)
        
        # Get all users with ordering by id
        from app.services.role_management import RoleManagementService
        role_service = RoleManagementService(db)
        users = await role_service.get_all_users_with_roles_ordered()
        
        # Convert to response model
        user_responses = []
        for user in users:
            user_response = AdminUserListResponse(
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                username=user.username,
                email=user.email,
                mobile_number=user.mobile_number,
                created_at=user.created_at,
                updated_at=user.updated_at,
                is_active=True,  # Assuming all users are active
                roles=user.roles or []  # Include roles data
            )
            user_responses.append(user_response)
        
        logger.info(f"Admin {current_user.id} successfully listed {len(user_responses)} users")
        return user_responses
        
    except Exception as e:
        logger.error(f"Unexpected error in admin list users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving the user list"
        )
