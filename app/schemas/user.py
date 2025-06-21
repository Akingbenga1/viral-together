from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.schemas.role import Role

class UserCreate(BaseModel):
    username: str
    password: str

class User(BaseModel):
    username: str
    stripe_customer_id: Optional[str] = None
    class Config:
        orm_mode = True


class UserRead(BaseModel):
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    username: str
    stripe_customer_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    email: Optional[str] = None
    mobile_number: Optional[str] = None
    roles: list[Role] = []
    class Config:
        orm_mode = True
    

class UserCreate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: str
    password: str
    email: Optional[str] = None
    mobile_number: Optional[str] = None