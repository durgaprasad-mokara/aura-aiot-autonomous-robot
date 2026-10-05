"""
AURA Backend — Robot Command Model
=====================================
Commands issued to robots, with audit trail.
"""

import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, DateTime, Enum, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class CommandType(str, enum.Enum):
    """Available robot commands."""
    MOVE_FORWARD = "MOVE_FORWARD"
    MOVE_BACKWARD = "MOVE_BACKWARD"
    TURN_LEFT = "TURN_LEFT"
    TURN_RIGHT = "TURN_RIGHT"
    ROTATE_LEFT = "ROTATE_LEFT"
    ROTATE_RIGHT = "ROTATE_RIGHT"
    STOP = "STOP"
    START_PATROL = "START_PATROL"
    STOP_PATROL = "STOP_PATROL"
    RETURN_HOME = "RETURN_HOME"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    SET_SPEED = "SET_SPEED"


class CommandStatus(str, enum.Enum):
    """Command execution status."""
    PENDING = "PENDING"
    SENT = "SENT"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


class RobotCommand(Base):
    __tablename__ = "robot_commands"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    robot_id = Column(
        UUID(as_uuid=True),
        ForeignKey("robots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    issued_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    command = Column(Enum(CommandType), nullable=False)
    parameters = Column(JSONB, nullable=True)  # e.g., {"speed": 60}
    status = Column(
        Enum(CommandStatus), nullable=False, default=CommandStatus.PENDING
    )
    source = Column(String(50), nullable=True, default="api")  # "api", "ai_agent", "scheduler"
    error_message = Column(String(500), nullable=True)
    issued_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    executed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    robot = relationship("Robot", back_populates="commands")
    issued_by_user = relationship("User", back_populates="commands_issued")

    __table_args__ = (
        Index("ix_commands_robot_issued", "robot_id", "issued_at"),
    )

    def __repr__(self):
        return f"<RobotCommand {self.command.value} → {self.robot_id} [{self.status.value}]>"
