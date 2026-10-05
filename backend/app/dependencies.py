"""
AURA Backend — FastAPI Dependencies
======================================
Shared dependencies for dependency injection in API routes.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import jwt

from app.database import get_db
from app.config import get_settings
from app.core.security import decode_token
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.models.user import User, UserRole

security_scheme = HTTPBearer()
settings = get_settings()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Extract and validate the current user from JWT token."""
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise AuthenticationError("Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")

    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.PyJWTError:
        raise AuthenticationError("Invalid token")

    # Fetch user from database
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        raise AuthenticationError("User not found")
    if not user.is_active:
        raise AuthenticationError("User account is deactivated")

    return user


async def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require ADMIN role."""
    if current_user.role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")
    return current_user


async def require_operator(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require OPERATOR or ADMIN role."""
    if current_user.role not in (UserRole.ADMIN, UserRole.OPERATOR):
        raise AuthorizationError("Operator access required")
    return current_user


async def require_viewer(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require any authenticated user (VIEWER, OPERATOR, or ADMIN)."""
    return current_user


# Type aliases for cleaner route signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_admin)]
OperatorUser = Annotated[User, Depends(require_operator)]
ViewerUser = Annotated[User, Depends(require_viewer)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
