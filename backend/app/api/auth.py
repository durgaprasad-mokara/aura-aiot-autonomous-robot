"""
AURA Backend — Auth Routes
=============================
API endpoints for authentication and user management.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.dependencies import CurrentUser, AdminUser
from app.services.auth_service import AuthService
from app.schemas.auth import (
    LoginRequest, LoginResponse, RegisterRequest,
    RefreshRequest, TokenResponse, UserResponse
)
from app.schemas.user import UserListResponse, UserCreate, UserUpdate
from app.core.logging import get_logger

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = get_logger("auth_api")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user (public)."""
    service = AuthService(db)
    user = await service.register(
        name=request.name,
        email=request.email,
        password=request.password,
        role=request.role
    )
    return user


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate and get tokens."""
    service = AuthService(db)
    result = await service.login(request.email, request.password)
    return result


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token."""
    service = AuthService(db)
    result = await service.refresh_tokens(request.refresh_token)
    return result


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    """Get current logged-in user profile."""
    return current_user


# ========================
# User Management (Admin)
# ========================

@router.get("/users", response_model=UserListResponse, dependencies=[Depends(AdminUser)])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get all users (Admin only)."""
    service = AuthService(db)
    users, total = await service.get_all_users(skip=skip, limit=limit)
    return {"data": users, "total": total}


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(AdminUser)])
async def create_user(
    request: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new user (Admin only)."""
    service = AuthService(db)
    user = await service.register(
        name=request.name,
        email=request.email,
        password=request.password,
        role=request.role
    )
    return user


@router.put("/users/{user_id}", response_model=UserResponse, dependencies=[Depends(AdminUser)])
async def update_user(
    user_id: UUID,
    request: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a user (Admin only)."""
    service = AuthService(db)
    user = await service.update_user(user_id, **request.model_dump(exclude_unset=True))
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(AdminUser)])
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a user (Admin only)."""
    service = AuthService(db)
    await service.delete_user(user_id)
