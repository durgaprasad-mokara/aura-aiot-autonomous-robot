"""
AURA Backend — Auth Schemas
==============================
Request/response models for authentication.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class RegisterRequest(BaseModel):
    """User registration request."""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(default="VIEWER", pattern="^(ADMIN|OPERATOR|VIEWER)$")


class TokenResponse(BaseModel):
    """JWT token pair response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class UserResponse(BaseModel):
    """User profile response."""
    id: UUID
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    """Complete login response with tokens and user info."""
    success: bool = True
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
