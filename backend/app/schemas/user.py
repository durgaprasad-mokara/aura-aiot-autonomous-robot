"""
AURA Backend — User Schemas
==============================
Request/response models for user management.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserCreate(BaseModel):
    """Create a new user (admin only)."""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(default="VIEWER", pattern="^(ADMIN|OPERATOR|VIEWER)$")


class UserUpdate(BaseModel):
    """Update user fields."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[str] = Field(None, pattern="^(ADMIN|OPERATOR|VIEWER)$")
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """User details response."""
    id: UUID
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Paginated user list."""
    success: bool = True
    data: list[UserResponse]
    total: int
