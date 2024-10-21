from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.schemas.user import UserCreate, User
from app.schemas.token import Token, TokenData
from app.db.session import get_db
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.sql import text

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Route 1: Protected endpoint to view profile details
@router.get("/profile", response_model=User)
async def read_user_profile(current_user: User = Depends(get_current_user)):
    return current_user


# Route 2: Protected endpoint to view sensitive data
@router.get("/data")
async def get_sensitive_data(current_user: User = Depends(get_current_user)):
    return {"message": "This is sensitive data that requires authentication", "user": current_user.username}


# Route 3: Protected endpoint to update user settings
@router.post("/update_settings")
async def update_user_settings(current_user: User = Depends(get_current_user), settings: dict = {}):
    # Simulate updating user settings (in a real app, you would update the database)
    return {"message": f"Settings updated for user {current_user.username}", "new_settings": settings}


# Route 4: Protected endpoint to delete an account
@router.delete("/delete_account")
async def delete_user_account(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Simulate deleting the user account (you would delete the user from the database)
    # await db.execute(text(f"DELETE FROM users WHERE username = '{current_user.username}'"))
    # await db.commit()
    return {"message": f"Account for user {current_user.username} has been deleted"}
