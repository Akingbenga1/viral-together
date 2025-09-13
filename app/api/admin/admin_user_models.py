from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator, ValidationInfo
from datetime import datetime
from app.schemas.role import Role


class AdminUserProfileUpdate(BaseModel):
    """Schema for admin updating any user's profile information and password"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None
    username: Optional[str] = None  # Admin can update username
    new_password: Optional[str] = None  # Admin can update password
    confirm_password: Optional[str] = None  # Confirmation for password update
    
    @field_validator('first_name', 'last_name', 'username')
    @classmethod
    def validate_names(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('Name fields cannot be empty strings')
        return v.strip() if v else v
    
    @field_validator('mobile_number')
    @classmethod
    def validate_mobile_number(cls, v):
        if v is not None and v.strip():
            # Basic mobile number validation - remove spaces and check length
            cleaned = v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if not cleaned.isdigit() or len(cleaned) < 10:
                raise ValueError('Invalid mobile number format')
        return v
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if v is not None:
            if len(v) < 8:
                raise ValueError('Password must be at least 8 characters long')
            if not any(c.isupper() for c in v):
                raise ValueError('Password must contain at least one uppercase letter')
            if not any(c.islower() for c in v):
                raise ValueError('Password must contain at least one lowercase letter')
            if not any(c.isdigit() for c in v):
                raise ValueError('Password must contain at least one digit')
        return v
    
    @field_validator('confirm_password')
    @classmethod
    def validate_confirm_password(cls, v, info: ValidationInfo):
        if v is not None and 'new_password' in info.data:
            if info.data['new_password'] is not None and v != info.data['new_password']:
                raise ValueError('Passwords do not match')
        return v


class AdminUserProfileResponse(BaseModel):
    """Response schema for admin user profile operations"""
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


class AdminUserUpdateResponse(BaseModel):
    """Response schema for successful admin user updates"""
    message: str
    user: AdminUserProfileResponse
    updated_by: str  # Admin who performed the update


class AdminUserListResponse(BaseModel):
    """Response schema for listing users (admin view)"""
    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    username: str
    email: Optional[str]
    mobile_number: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    roles: List[Role] = []
    
    class Config:
        from_attributes = True
