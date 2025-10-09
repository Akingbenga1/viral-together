from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# from app.api.profile.profile_models import UserRead
from app.core.security import verify_token
from app.schemas.user import UserCreate, User, UserRead
from app.schemas.token import Token, TokenData
from app.services.auth import hash_password, verify_password, create_access_token
from app.db.models import User as UserModel, Role, UserRole, PasswordResetToken
from app.services.role_management import RoleManagementService
from app.schemas.password_reset import ForgotPasswordRequest, ForgotPasswordResponse, ResetPasswordRequest, ResetPasswordResponse
import secrets
import uuid
from datetime import datetime, timedelta
from app.db.session import get_db
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import timedelta
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/register", response_model=User)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    print("api register call ====> ", user.username, user.email)
    try:
        # Check if username already exists
        db_user = await db.execute(select(UserModel).where(UserModel.username == user.username))
        if db_user.fetchone():
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # Check if email already exists
        db_email = await db.execute(select(UserModel).where(UserModel.email == user.email))
        if db_email.fetchone():
            raise HTTPException(status_code=400, detail="This email address is already registered. Please use a different email or try logging in.")
        
        new_user = UserModel(
            username=user.username,
            email=user.email,
            hashed_password=hash_password(user.password),
            first_name=" ",
            last_name=" "
        )
        db.add(new_user)
        await db.commit()  # Commit the transaction
        await db.refresh(new_user)
        
        # Assign 'user' role to the newly created user
        role_service = RoleManagementService(db)
        user_role_result = await db.execute(select(Role).where(Role.name == "user"))
        user_role = user_role_result.scalars().first()
        
        if user_role:
            await role_service.assign_role_to_user(new_user.id, user_role.id)
            logger.info(f"Assigned 'user' role to new user {new_user.id}")
        else:
            logger.warning("'user' role not found in database")

    except SQLAlchemyError as e:
        print("error ====> ", e)
        await db.rollback()  # Rollback in case of error
        raise HTTPException(status_code=500, detail=str(e))  # Raise an HTTP exception with the error message

    return User(username=new_user.username) 

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # Try to find user by username or email
    user_result = await db.execute(
        select(UserModel).where(
            (UserModel.username == form_data.username) | 
            (UserModel.email == form_data.username)
        )
    )
    user = user_result.scalars().first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.username}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}


# Dependency to get the current authenticated user
async def get_current_user_dependency(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> UserRead:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # Verify the token and get the user's username
    username_data: TokenData = verify_token(token, credentials_exception)
    if not username_data or not username_data.username:
        raise credentials_exception
        
    # Fetch user from database with their roles
    # Note: We use username from token since that's what we store in the token
    result = await db.execute(
        select(UserModel)
        .options(selectinload(UserModel.roles))
        .where(UserModel.username == username_data.username)
    )
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    
    # Check if user has influencer role and get influencer_id
    influencer_id = None
    for role in user.roles:
        if role.name == "influencer":
            # Fetch the influencer record for this user
            from app.db.models.influencer import Influencer
            influencer_result = await db.execute(
                select(Influencer).where(Influencer.user_id == user.id)
            )
            influencer = influencer_result.scalars().first()
            if influencer:
                influencer_id = influencer.id
            break
        
    logger.info("user ====> %s", user)
    # Create UserRead with influencer_id
    user_data = UserRead.from_orm(user)
    user_data.influencer_id = influencer_id
    return user_data

# Route to get current user (for API calls)
@router.post("/user", response_model=UserRead)
async def get_current_user(current_user: UserRead = Depends(get_current_user_dependency)):
    return current_user

# Route 1: Protected endpoint to view profile details
@router.get("/profile", response_model=UserRead)
async def read_user_profile(current_user: UserRead = Depends(get_current_user_dependency)):
    return current_user


# Route 2: Protected endpoint to view sensitive data
@router.get("/data")
async def get_sensitive_data(current_user: UserRead = Depends(get_current_user_dependency)):
    return {"message": "This is sensitive data that requires authentication", "user": current_user.username}


# Route 3: Protected endpoint to update user settings
@router.post("/protected/update-settings")
async def update_user_settings(current_user: UserRead = Depends(get_current_user_dependency), settings: dict = {}):
    # Simulate updating user settings (in a real app, you would update the database)
    return {"message": f"Settings updated for user {current_user.username}", "new_settings": settings}


# Route 4: Protected endpoint to delete an account
@router.delete("/protected/delete-account")
async def delete_user_account(current_user: UserRead = Depends(get_current_user_dependency), db: AsyncSession = Depends(get_db)):
    # Simulate deleting the user account (you would delete the user from the database)
    # Note: This is also vulnerable to SQL injection and should be updated.
    await db.execute(select(UserModel).where(UserModel.username == current_user.username))
    await db.commit()
    return {"message": f"Account for user {current_user.username} has been deleted"}

# Password Reset Endpoints

@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Handle forgot password request
    Accepts either email or username
    """
    try:
        # Find user by email or username
        user_result = await db.execute(
            select(UserModel).where(
                (UserModel.email == request.email_or_username) | 
                (UserModel.username == request.email_or_username)
            )
        )
        user = user_result.scalars().first()
        
        if not user:
            # For security, return success even if user doesn't exist
            return ForgotPasswordResponse(
                message="If an account with that email or username exists, we've sent a password reset link.",
                success=True
            )
        
        # Generate secure token
        reset_token = secrets.token_urlsafe(32)
        
        # Set expiration time (1 hour from now)
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        # Create password reset token record
        reset_token_record = PasswordResetToken(
            user_id=user.id,
            token=reset_token,
            expires_at=expires_at,
            is_used=False
        )
        
        db.add(reset_token_record)
        await db.commit()
        
        # Generate reset URL (you may need to adjust the base URL)
        reset_url = f"http://localhost:3000/auth/reset-password?token={reset_token}"
        
        # Send email via Celery task
        from app.tasks.password_reset_tasks import send_password_reset_email
        send_password_reset_email.delay(
            user_id=user.id,
            reset_token=reset_token,
            reset_url=reset_url
        )
        
        logger.info(f"Password reset token created for user {user.id}")
        
        return ForgotPasswordResponse(
            message="If an account with that email or username exists, we've sent a password reset link.",
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error in forgot password: {str(e)}")
        return ForgotPasswordResponse(
            message="If an account with that email or username exists, we've sent a password reset link.",
            success=True
        )

@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Handle password reset with token
    """
    try:
        # Find the reset token
        token_result = await db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token == request.token,
                PasswordResetToken.is_used == False,
                PasswordResetToken.expires_at > datetime.utcnow()
            )
        )
        reset_token_record = token_result.scalars().first()
        
        if not reset_token_record:
            return ResetPasswordResponse(
                message="Invalid or expired reset token.",
                success=False
            )
        
        # Get the user
        user_result = await db.execute(
            select(UserModel).where(UserModel.id == reset_token_record.user_id)
        )
        user = user_result.scalars().first()
        
        if not user:
            return ResetPasswordResponse(
                message="User not found.",
                success=False
            )
        
        # Update user password
        user.hashed_password = hash_password(request.new_password)
        
        # Mark token as used
        reset_token_record.is_used = True
        
        await db.commit()
        
        logger.info(f"Password reset successfully for user {user.id}")
        
        return ResetPasswordResponse(
            message="Password has been reset successfully. You can now login with your new password.",
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error in reset password: {str(e)}")
        return ResetPasswordResponse(
            message="An error occurred while resetting your password. Please try again.",
            success=False
        )
