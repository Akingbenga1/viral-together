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
from app.db.models import User as UserModel
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
    print("api reguster call ====> ", user.username, user.password)
    try:
        db_user = await db.execute(select(UserModel).where(UserModel.username == user.username))
        if db_user.fetchone():
            raise HTTPException(status_code=400, detail="Username already registered")
        
        new_user = UserModel(
            username=user.username,
            hashed_password=hash_password(user.password),
            first_name="Gbenga",
            last_name="Akinba"
        )
        db.add(new_user)
        await db.commit()  # Commit the transaction

    except SQLAlchemyError as e:
        print("error ====> ", e)
        await db.rollback()  # Rollback in case of error
        raise HTTPException(status_code=500, detail=str(e))  # Raise an HTTP exception with the error message

    return User(username=new_user.username) 

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # Note: This query should be updated to use the ORM to load roles as well if needed upon login.
    # For now, focusing on get_current_user as requested.
    user_result = await db.execute(select(UserModel).where(UserModel.username == form_data.username))
    user = user_result.scalars().first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.username}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}


# Dependency to get the current authenticated user
@router.post("/user", response_model=UserRead)
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> UserRead:
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
    result = await db.execute(
        select(UserModel)
        .options(selectinload(UserModel.roles))
        .where(UserModel.username == username_data.username)
    )
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
        
    logger.info("user ====> %s", user)
    # The UserRead schema with orm_mode=True will handle the conversion
    return UserRead.from_orm(user)

# Route 1: Protected endpoint to view profile details
@router.get("/profile", response_model=UserRead)
async def read_user_profile(current_user: UserRead = Depends(get_current_user)):
    return current_user


# Route 2: Protected endpoint to view sensitive data
@router.get("/data")
async def get_sensitive_data(current_user: UserRead = Depends(get_current_user)):
    return {"message": "This is sensitive data that requires authentication", "user": current_user.username}


# Route 3: Protected endpoint to update user settings
@router.post("/protected/update-settings")
async def update_user_settings(current_user: UserRead = Depends(get_current_user), settings: dict = {}):
    # Simulate updating user settings (in a real app, you would update the database)
    return {"message": f"Settings updated for user {current_user.username}", "new_settings": settings}


# Route 4: Protected endpoint to delete an account
@router.delete("/protected/delete-account")
async def delete_user_account(current_user: UserRead = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Simulate deleting the user account (you would delete the user from the database)
    # Note: This is also vulnerable to SQL injection and should be updated.
    await db.execute(select(UserModel).where(UserModel.username == current_user.username))
    await db.commit()
    return {"message": f"Account for user {current_user.username} has been deleted"}
