"""
AURA Backend — Command Schemas
=================================
Request/response models for robot commands.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any
from uuid import UUID
from datetime import datetime


class CommandRequest(BaseModel):
    """Robot command request."""
    command: str = Field(
        ...,
        pattern="^(MOVE_FORWARD|MOVE_BACKWARD|TURN_LEFT|TURN_RIGHT|ROTATE_LEFT|ROTATE_RIGHT|STOP|START_PATROL|STOP_PATROL|RETURN_HOME|EMERGENCY_STOP|SET_SPEED)$",
    )
    speed: Optional[int] = Field(None, ge=0, le=100)
    parameters: Optional[dict[str, Any]] = None


class CommandResponse(BaseModel):
    """Command execution response."""
    success: bool = True
    command_id: UUID
    command: str
    status: str
    message: str


class CommandHistoryResponse(BaseModel):
    """Command history record."""
    id: UUID
    robot_id: UUID
    command: str
    parameters: Optional[dict[str, Any]] = None
    status: str
    source: Optional[str] = None
    issued_at: datetime
    executed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MQTTCommandPayload(BaseModel):
    """Command payload sent over MQTT to the robot."""
    robot_id: str
    command: str
    speed: Optional[int] = None
    parameters: Optional[dict[str, Any]] = None
    timestamp: datetime
