"""
AURA Backend — Telemetry & Sensor Reading Models
===================================================
Stores robot telemetry snapshots and individual sensor readings.
Indexes on robot_id + timestamp for efficient time-range queries.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Float, DateTime, ForeignKey, Index, String
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Telemetry(Base):
    """Aggregated telemetry snapshot from a robot."""
    __tablename__ = "telemetry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    robot_id = Column(
        UUID(as_uuid=True),
        ForeignKey("robots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    gas_level = Column(Float, nullable=True)
    distance = Column(Float, nullable=True)
    battery = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    cpu_usage = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    robot = relationship("Robot", back_populates="telemetry")

    # Composite index for common query pattern: robot + time range
    __table_args__ = (
        Index("ix_telemetry_robot_timestamp", "robot_id", "timestamp"),
    )

    def __repr__(self):
        return f"<Telemetry robot={self.robot_id} t={self.timestamp}>"


class SensorReading(Base):
    """Individual sensor readings for detailed tracking."""
    __tablename__ = "sensor_readings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    robot_id = Column(
        UUID(as_uuid=True),
        ForeignKey("robots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sensor_type = Column(String(50), nullable=False)  # e.g., "ultrasonic", "dht22", "mq2"
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=True)  # e.g., "cm", "°C", "ppm"
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    robot = relationship("Robot", back_populates="sensor_readings")

    __table_args__ = (
        Index("ix_sensor_robot_type_timestamp", "robot_id", "sensor_type", "timestamp"),
    )

    def __repr__(self):
        return f"<SensorReading {self.sensor_type}={self.value} robot={self.robot_id}>"
