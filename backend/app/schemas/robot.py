"""
AURA Backend — Robot Schemas
===============================
Request/response models for robot management.
"""

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class RobotCreate(BaseModel):
    """Register a new robot."""
    name: str = Field(..., min_length=2, max_length=100)
    device_id: str = Field(..., min_length=2, max_length=50)
    serial_number: Optional[str] = Field(None, max_length=100)
    firmware_version: Optional[str] = Field(None, max_length=50)
    ip_address: Optional[str] = Field(None, max_length=45)
    home_x: Optional[float] = 0.0
    home_y: Optional[float] = 0.0
    description: Optional[str] = None


class RobotUpdate(BaseModel):
    """Update robot fields."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    firmware_version: Optional[str] = Field(None, max_length=50)
    ip_address: Optional[str] = Field(None, max_length=45)
    home_x: Optional[float] = None
    home_y: Optional[float] = None
    description: Optional[str] = None


class RobotResponse(BaseModel):
    """Robot details response."""
    id: UUID
    name: str
    device_id: str
    serial_number: Optional[str] = None
    status: str
    mode: str
    battery: Optional[float] = None
    firmware_version: Optional[str] = None
    ip_address: Optional[str] = None
    last_seen: Optional[datetime] = None
    home_x: Optional[float] = None
    home_y: Optional[float] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RobotListResponse(BaseModel):
    """Robot list response."""
    success: bool = True
    data: list[RobotResponse]
    total: int


class RobotStatusResponse(BaseModel):
    """Lightweight robot status for dashboard."""
    id: UUID
    name: str
    device_id: str
    status: str
    mode: str
    battery: Optional[float] = None
    last_seen: Optional[datetime] = None

    model_config = {"from_attributes": True}
