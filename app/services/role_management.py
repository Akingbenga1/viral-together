from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.db.models import User, Role, UserRole
from app.schemas.user import UserRead
from app.schemas.role import Role as RoleSchema
import logging

logger = logging.getLogger(__name__)

class RoleManagementService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_roles(self, user_id: int) -> List[RoleSchema]:
        """Get all roles for a specific user"""
        try:
            result = await self.db.execute(
                select(User)
                .options(selectinload(User.roles))
                .where(User.id == user_id)
            )
            user = result.scalars().first()
            if not user:
                return []
            return [RoleSchema.from_orm(role) for role in user.roles]
        except Exception as e:
            logger.error(f"Error getting user roles: {e}")
            return []

    async def assign_role_to_user(self, user_id: int, role_id: int) -> bool:
        """Assign a role to a user"""
        try:
            # Check if user and role exist
            user_result = await self.db.execute(select(User).where(User.id == user_id))
            user = user_result.scalars().first()
            if not user:
                logger.error(f"User with id {user_id} not found")
                return False

            role_result = await self.db.execute(select(Role).where(Role.id == role_id))
            role = role_result.scalars().first()
            if not role:
                logger.error(f"Role with id {role_id} not found")
                return False

            # Check if role is already assigned
            existing_role = await self.db.execute(
                select(UserRole).where(
                    and_(UserRole.user_id == user_id, UserRole.role_id == role_id)
                )
            )
            if existing_role.scalars().first():
                logger.info(f"Role {role_id} already assigned to user {user_id}")
                return True

            # Assign the role
            user_role = UserRole(user_id=user_id, role_id=role_id)
            self.db.add(user_role)
            await self.db.commit()
            logger.info(f"Role {role_id} assigned to user {user_id}")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error assigning role to user: {e}")
            return False

    async def remove_role_from_user(self, user_id: int, role_id: int) -> bool:
        """Remove a role from a user"""
        try:
            # Check if the role assignment exists
            result = await self.db.execute(
                select(UserRole).where(
                    and_(UserRole.user_id == user_id, UserRole.role_id == role_id)
                )
            )
            user_role = result.scalars().first()
            if not user_role:
                logger.error(f"Role {role_id} not assigned to user {user_id}")
                return False

            # Remove the role
            await self.db.delete(user_role)
            await self.db.commit()
            logger.info(f"Role {role_id} removed from user {user_id}")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error removing role from user: {e}")
            return False

    async def get_all_roles(self) -> List[RoleSchema]:
        """Get all available roles"""
        try:
            result = await self.db.execute(select(Role))
            roles = result.scalars().all()
            return [RoleSchema.from_orm(role) for role in roles]
        except Exception as e:
            logger.error(f"Error getting all roles: {e}")
            return []

    async def get_all_users_with_roles(self) -> List[UserRead]:
        """Get all users with their roles"""
        try:
            result = await self.db.execute(
                select(User).options(selectinload(User.roles))
            )
            users = result.scalars().all()
            return [UserRead.from_orm(user) for user in users]
        except Exception as e:
            logger.error(f"Error getting users with roles: {e}")
            return []

    async def get_user_by_id(self, user_id: int) -> Optional[UserRead]:
        """Get a specific user with their roles"""
        try:
            result = await self.db.execute(
                select(User)
                .options(selectinload(User.roles))
                .where(User.id == user_id)
            )
            user = result.scalars().first()
            if user:
                return UserRead.from_orm(user)
            return None
        except Exception as e:
            logger.error(f"Error getting user by id: {e}")
            return None
