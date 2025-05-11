from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str

class User(BaseModel):
    username: str

    class Config:
        orm_mode = True


class UserRead(BaseModel):
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    username: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
    

class UserCreate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: str
    password: str