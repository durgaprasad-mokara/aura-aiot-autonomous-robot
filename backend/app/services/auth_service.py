"""
AURA Backend — Auth Service
==============================
Business logic for authentication and user management.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import AuthenticationError, NotFoundError, ConflictError
from app.core.logging import get_logger

logger = get_logger("auth_service")


class AuthService:
    """Handles authentication and user management operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(
        self, name: str, email: str, password: str, role: str = "VIEWER"
    ) -> User:
        """Register a new user."""
        # Check if email already exists
        result = await self.db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise ConflictError(f"User with email '{email}' already exists")

        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=UserRole(role),
        )
        self.db.add(user)
        await self.db.flush()

        logger.info("user_registered", user_id=str(user.id), email=email, role=role)
        return user

    async def login(self, email: str, password: str) -> dict:
        """Authenticate user and return tokens."""
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            logger.warning("login_failed", email=email)
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        # Update last login
        user.last_login = datetime.now(timezone.utc)
        await self.db.flush()

        # Generate tokens
        access_token = create_access_token(subject=user.id, role=user.role.value)
        refresh_token = create_refresh_token(subject=user.id)

        logger.info("user_logged_in", user_id=str(user.id), email=email)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user,
        }

    async def refresh_tokens(self, refresh_token: str) -> dict:
        """Refresh access token using refresh token."""
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise AuthenticationError("Invalid token type")

            user_id = payload.get("sub")
            result = await self.db.execute(select(User).where(User.id == UUID(user_id)))
            user = result.scalar_one_or_none()

            if not user or not user.is_active:
                raise AuthenticationError("User not found or inactive")

            new_access = create_access_token(subject=user.id, role=user.role.value)
            new_refresh = create_refresh_token(subject=user.id)

            return {
                "access_token": new_access,
                "refresh_token": new_refresh,
            }
        except Exception as e:
            raise AuthenticationError(f"Token refresh failed: {str(e)}")

    async def get_user_by_id(self, user_id: UUID) -> User:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User", str(user_id))
        return user

    async def get_all_users(self, skip: int = 0, limit: int = 50) -> tuple[list[User], int]:
        """Get paginated user list."""
        # Count total
        count_result = await self.db.execute(select(func.count(User.id)))
        total = count_result.scalar()

        # Fetch users
        result = await self.db.execute(
            select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
        )
        users = list(result.scalars().all())

        return users, total

    async def update_user(self, user_id: UUID, **kwargs) -> User:
        """Update user fields."""
        user = await self.get_user_by_id(user_id)

        for key, value in kwargs.items():
            if value is not None:
                if key == "role":
                    setattr(user, key, UserRole(value))
                elif key == "password":
                    user.password_hash = hash_password(value)
                else:
                    setattr(user, key, value)

        await self.db.flush()
        logger.info("user_updated", user_id=str(user_id), fields=list(kwargs.keys()))
        return user

    async def delete_user(self, user_id: UUID) -> None:
        """Delete a user."""
        user = await self.get_user_by_id(user_id)
        await self.db.delete(user)
        logger.info("user_deleted", user_id=str(user_id))
