"""
AURA Backend — Centralized Exceptions
========================================
Custom exception classes and centralized error handling.
All API errors return a consistent JSON structure.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Any, Optional


# ========================
# Custom Exception Classes
# ========================

class AuraBaseException(Exception):
    """Base exception for all AURA application errors."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        details: Optional[Any] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class AuthenticationError(AuraBaseException):
    """Authentication failures."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            code="AUTHENTICATION_ERROR",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthorizationError(AuraBaseException):
    """Insufficient permissions."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            code="AUTHORIZATION_ERROR",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class NotFoundError(AuraBaseException):
    """Resource not found."""

    def __init__(self, resource: str, identifier: Any = None):
        msg = f"{resource} not found"
        if identifier:
            msg = f"{resource} '{identifier}' not found"
        super().__init__(
            code="NOT_FOUND",
            message=msg,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ConflictError(AuraBaseException):
    """Resource already exists or state conflict."""

    def __init__(self, message: str):
        super().__init__(
            code="CONFLICT",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )


class RobotOfflineError(AuraBaseException):
    """Robot is offline and cannot receive commands."""

    def __init__(self, robot_id: str):
        super().__init__(
            code="ROBOT_OFFLINE",
            message=f"Robot '{robot_id}' is currently offline.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class CommandRejectedError(AuraBaseException):
    """Command rejected by safety checks."""

    def __init__(self, reason: str):
        super().__init__(
            code="COMMAND_REJECTED",
            message=f"Command rejected: {reason}",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class MQTTError(AuraBaseException):
    """MQTT communication error."""

    def __init__(self, message: str = "MQTT communication error"):
        super().__init__(
            code="MQTT_ERROR",
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class ValidationError(AuraBaseException):
    """Custom validation error."""

    def __init__(self, message: str, details: Any = None):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


# ========================
# Exception Handlers
# ========================

def create_error_response(code: str, message: str, details: Any = None) -> dict:
    """Create consistent error response body."""
    response = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }
    if details:
        response["error"]["details"] = details
    return response


async def aura_exception_handler(request: Request, exc: AuraBaseException) -> JSONResponse:
    """Handle all custom AURA exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(exc.code, exc.message, exc.details),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic/FastAPI validation errors."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            "VALIDATION_ERROR",
            "Request validation failed",
            errors,
        ),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler — never expose internal details."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            "INTERNAL_ERROR",
            "An unexpected error occurred. Please try again later.",
        ),
    )
