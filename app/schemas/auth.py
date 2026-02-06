"""Authentication Pydantic schemas."""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str


class UserResponse(BaseModel):
    """User response schema."""
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class CurrentUser(BaseModel):
    """Current authenticated user schema."""
    id: str
    email: str
    role: str
    
    class Config:
        from_attributes = True
