from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.dependencies import require_any_role
from app.schemas.user import UserRead
from app.schemas.role import Role
from app.services.role_management import RoleManagementService
from app.db.session import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/role-management", tags=["role-management"])

@router.get("/users/{user_id}/roles", response_model=List[Role])
async def get_user_roles(
    user_id: int, 
    current_user: UserRead = Depends(require_any_role(["admin", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    """Get all roles for a specific user"""
    try:
        role_service = RoleManagementService(db)
        roles = await role_service.get_user_roles(user_id)
        return roles
    except Exception as e:
        logger.error(f"Error getting user roles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user roles"
        )

@router.post("/users/{user_id}/roles/{role_id}")
async def assign_role_to_user(
    user_id: int, 
    role_id: int, 
    current_user: UserRead = Depends(require_any_role(["admin", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    """Assign a role to a user"""
    try:
        role_service = RoleManagementService(db)
        success = await role_service.assign_role_to_user(user_id, role_id)
        
        if success:
            return {"message": f"Role {role_id} assigned to user {user_id} successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to assign role to user"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning role to user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign role to user"
        )

@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role_from_user(
    user_id: int, 
    role_id: int, 
    current_user: UserRead = Depends(require_any_role(["admin", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    """Remove a role from a user"""
    try:
        role_service = RoleManagementService(db)
        success = await role_service.remove_role_from_user(user_id, role_id)
        
        if success:
            return {"message": f"Role {role_id} removed from user {user_id} successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to remove role from user"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing role from user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove role from user"
        )

@router.get("/roles", response_model=List[Role])
async def get_all_roles(
    current_user: UserRead = Depends(require_any_role(["admin", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    """Get all available roles"""
    try:
        role_service = RoleManagementService(db)
        roles = await role_service.get_all_roles()
        return roles
    except Exception as e:
        logger.error(f"Error getting all roles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get roles"
        )

@router.get("/users", response_model=List[UserRead])
async def get_all_users_with_roles(
    current_user: UserRead = Depends(require_any_role(["admin", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    """Get all users with their roles"""
    try:
        role_service = RoleManagementService(db)
        users = await role_service.get_all_users_with_roles()
        return users
    except Exception as e:
        logger.error(f"Error getting users with roles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get users"
        )

@router.get("/users/{user_id}", response_model=UserRead)
async def get_user_by_id(
    user_id: int,
    current_user: UserRead = Depends(require_any_role(["admin", "super_admin"])),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific user with their roles"""
    try:
        role_service = RoleManagementService(db)
        user = await role_service.get_user_by_id(user_id)
        
        if user:
            return user
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user by id: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )
