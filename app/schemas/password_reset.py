from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request"""
    email_or_username: str
    
    @validator('email_or_username')
    def validate_email_or_username(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Email or username is required')
        return v.strip()

class ForgotPasswordResponse(BaseModel):
    """Schema for forgot password response"""
    message: str
    success: bool = True

class ResetPasswordRequest(BaseModel):
    """Schema for reset password request"""
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if not v or len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class ResetPasswordResponse(BaseModel):
    """Schema for reset password response"""
    message: str
    success: bool = True

class PasswordResetTokenResponse(BaseModel):
    """Schema for password reset token response"""
    id: int
    user_id: int
    token: str
    is_used: bool
    expires_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True
