"""
AURA Backend — Robot Model
============================
Robot device registration and status tracking.
"""

import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Float, DateTime, Enum, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class RobotStatus(str, enum.Enum):
    """Robot connectivity and operational status."""
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    MAINTENANCE = "MAINTENANCE"
    ERROR = "ERROR"


class RobotMode(str, enum.Enum):
    """Robot operational mode."""
    MANUAL = "MANUAL"
    AUTONOMOUS = "AUTONOMOUS"
    RETURN_HOME = "RETURN_HOME"
    EMERGENCY = "EMERGENCY"


class Robot(Base):
    __tablename__ = "robots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    device_id = Column(String(50), unique=True, nullable=False, index=True)
    serial_number = Column(String(100), unique=True, nullable=True)
    status = Column(
        Enum(RobotStatus), nullable=False, default=RobotStatus.OFFLINE
    )
    mode = Column(
        Enum(RobotMode), nullable=False, default=RobotMode.MANUAL
    )
    battery = Column(Float, nullable=True, default=100.0)
    firmware_version = Column(String(50), nullable=True)
    ip_address = Column(String(45), nullable=True)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    home_x = Column(Float, nullable=True, default=0.0)
    home_y = Column(Float, nullable=True, default=0.0)
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    telemetry = relationship("Telemetry", back_populates="robot", cascade="all, delete-orphan")
    sensor_readings = relationship("SensorReading", back_populates="robot", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="robot", cascade="all, delete-orphan")
    commands = relationship("RobotCommand", back_populates="robot", cascade="all, delete-orphan")
    detections = relationship("Detection", back_populates="robot", cascade="all, delete-orphan")
    patrol_sessions = relationship("PatrolSession", back_populates="robot", cascade="all, delete-orphan")
    maintenance_records = relationship("MaintenanceRecord", back_populates="robot", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Robot {self.name} ({self.device_id}) [{self.status.value}]>"
