from typing import Optional
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile information"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('Name fields cannot be empty strings')
        return v.strip() if v else v
    
    @validator('mobile_number')
    def validate_mobile_number(cls, v):
        if v is not None:
            # Basic mobile number validation - remove spaces and check length
            cleaned = v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if not cleaned.isdigit() or len(cleaned) < 10:
                raise ValueError('Invalid mobile number format')
        return v


class UserPasswordUpdate(BaseModel):
    """Schema for updating user password"""
    current_password: str
    new_password: str
    confirm_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('confirm_password')
    def validate_confirm_password(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class UserProfileResponse(BaseModel):
    """Response schema for user profile operations"""
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    username: str
    email: Optional[str]
    mobile_number: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdateResponse(BaseModel):
    """Response schema for successful user updates"""
    message: str
    user: UserProfileResponse
