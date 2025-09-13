from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from typing import Optional
import logging

from app.db.models import User as UserModel
from app.core.security import hash_password, verify_password
from app.api.users.user_models import UserProfileUpdate, UserPasswordUpdate, UserProfileResponse
from app.api.admin.admin_user_models import AdminUserProfileUpdate

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: int) -> Optional[UserModel]:
        """Get user by ID"""
        try:
            result = await self.db.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            return result.scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user"
            )

    async def get_user_by_username(self, username: str) -> Optional[UserModel]:
        """Get user by username"""
        try:
            result = await self.db.execute(
                select(UserModel).where(UserModel.username == username)
            )
            return result.scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by username {username}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user"
            )

    async def update_user_profile(
        self, 
        user_id: int, 
        profile_update: UserProfileUpdate
    ) -> UserModel:
        """Update user profile information"""
        try:
            # Get the user
            user = await self.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Check if email is being updated and if it's already taken
            if profile_update.email and profile_update.email != user.email:
                existing_user = await self.db.execute(
                    select(UserModel).where(UserModel.email == profile_update.email)
                )
                if existing_user.scalars().first():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email address is already in use"
                    )

            # Prepare update data
            update_data = {}
            if profile_update.first_name is not None:
                update_data['first_name'] = profile_update.first_name
            if profile_update.last_name is not None:
                update_data['last_name'] = profile_update.last_name
            if profile_update.email is not None:
                update_data['email'] = profile_update.email
            if profile_update.mobile_number is not None:
                update_data['mobile_number'] = profile_update.mobile_number

            # Update the user
            if update_data:
                await self.db.execute(
                    update(UserModel)
                    .where(UserModel.id == user_id)
                    .values(**update_data)
                )
                await self.db.commit()

                # Refresh the user object
                await self.db.refresh(user)

            return user

        except HTTPException:
            raise
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error updating user profile for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user profile"
            )

    async def update_user_password(
        self, 
        user_id: int, 
        password_update: UserPasswordUpdate
    ) -> UserModel:
        """Update user password"""
        try:
            # Get the user
            user = await self.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Verify current password
            if not verify_password(password_update.current_password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )

            # Hash new password
            new_hashed_password = hash_password(password_update.new_password)

            # Update password
            await self.db.execute(
                update(UserModel)
                .where(UserModel.id == user_id)
                .values(hashed_password=new_hashed_password)
            )
            await self.db.commit()

            # Refresh the user object
            await self.db.refresh(user)

            return user

        except HTTPException:
            raise
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error updating password for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )

    async def get_user_profile(self, user_id: int) -> UserModel:
        """Get user profile information"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            return user
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error getting user profile for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user profile"
            )

    # Admin-specific methods
    async def admin_update_user_profile(
        self, 
        target_user_id: int, 
        profile_update: AdminUserProfileUpdate,
        admin_user_id: int
    ) -> UserModel:
        """Admin update any user's profile information"""
        try:
            # Get the target user
            user = await self.get_user_by_id(target_user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target user not found"
                )

            # Check if email is being updated and if it's already taken
            if profile_update.email and profile_update.email != user.email:
                existing_user = await self.db.execute(
                    select(UserModel).where(UserModel.email == profile_update.email)
                )
                if existing_user.scalars().first():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Email address is already in use"
                    )

            # Check if username is being updated and if it's already taken
            if profile_update.username and profile_update.username != user.username:
                existing_user = await self.db.execute(
                    select(UserModel).where(UserModel.username == profile_update.username)
                )
                if existing_user.scalars().first():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username is already in use"
                    )

            # Prepare update data
            update_data = {}
            if profile_update.first_name is not None:
                update_data['first_name'] = profile_update.first_name
            if profile_update.last_name is not None:
                update_data['last_name'] = profile_update.last_name
            if profile_update.email is not None:
                update_data['email'] = profile_update.email
            if profile_update.mobile_number is not None:
                update_data['mobile_number'] = profile_update.mobile_number
            if profile_update.username is not None:
                update_data['username'] = profile_update.username
            
            # Handle password update if provided
            if profile_update.new_password is not None:
                new_hashed_password = hash_password(profile_update.new_password)
                update_data['hashed_password'] = new_hashed_password

            # Update the user
            if update_data:
                await self.db.execute(
                    update(UserModel)
                    .where(UserModel.id == target_user_id)
                    .values(**update_data)
                )
                await self.db.commit()

                # Refresh the user object
                await self.db.refresh(user)

            logger.info(f"Admin user {admin_user_id} updated profile for user {target_user_id}")
            return user

        except HTTPException:
            raise
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error in admin update user profile for user {target_user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user profile"
            )


    async def admin_get_user_profile(self, target_user_id: int, admin_user_id: int) -> UserModel:
        """Admin get any user's profile information"""
        try:
            user = await self.get_user_by_id(target_user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target user not found"
                )
            
            logger.info(f"Admin user {admin_user_id} accessed profile for user {target_user_id}")
            return user
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error in admin get user profile for user {target_user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user profile"
            )
