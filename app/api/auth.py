from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_token
from app.schemas.user import UserCreate, User
from app.schemas.token import Token, TokenData
from app.services.auth import hash_password, verify_password, create_access_token
from app.db.models import User as UserModel
from app.db.session import get_db
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import timedelta
from sqlalchemy.sql import text

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/register", response_model=User)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # print("api reguster call ====> ", user.username, user.password)
    db_user = await db.execute(text(f"SELECT * FROM users WHERE username = '{user.username}'"))
    if db_user.fetchone():
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = UserModel(username=user.username, hashed_password=hash_password(user.password), first_name="Gbenga", last_name="Akinba")
    db.add(new_user)
    # await db.commit()
    return User(username=new_user.username)

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await db.execute(text(f"SELECT * FROM users WHERE username = '{form_data.username}'"))
    user = user.fetchone()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.username}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}


# Dependency to get the current authenticated user
@router.post("/user", response_model=User)
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # Verify the token and get the user's username
    username: TokenData = verify_token(token, credentials_exception)
    if username is None:
        raise credentials_exception
    # Fetch user from database
    result = await db.execute(text(f"SELECT * FROM users WHERE username = '{username.username}'"))
    user = result.fetchone()
    if user is None:
        raise credentials_exception
    return User(username=user.username)


# Route 1: Protected endpoint to view profile details
@router.get("/profile", response_model=User)
async def read_user_profile(current_user: User = Depends(get_current_user)):
    return current_user


# Route 2: Protected endpoint to view sensitive data
@router.get("/data")
async def get_sensitive_data(current_user: User = Depends(get_current_user)):
    return {"message": "This is sensitive data that requires authentication", "user": current_user.username}


# Route 3: Protected endpoint to update user settings
@router.post("/protected/update-settings")
async def update_user_settings(current_user: User = Depends(get_current_user), settings: dict = {}):
    # Simulate updating user settings (in a real app, you would update the database)
    return {"message": f"Settings updated for user {current_user.username}", "new_settings": settings}


# Route 4: Protected endpoint to delete an account
@router.delete("/protected/delete-account")
async def delete_user_account(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Simulate deleting the user account (you would delete the user from the database)
    await db.execute(f"DELETE FROM users WHERE username = '{current_user.username}'")
    await db.commit()
    return {"message": f"Account for user {current_user.username} has been deleted"}
