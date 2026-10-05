"""
AURA Backend — Maintenance Record Model
==========================================
Robot maintenance history tracking.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, DateTime, Text, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    robot_id = Column(
        UUID(as_uuid=True),
        ForeignKey("robots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type = Column(String(50), nullable=False)  # "firmware_update", "battery_replacement", "sensor_calibration"
    description = Column(Text, nullable=True)
    performed_by = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    parts_replaced = Column(JSONB, nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    robot = relationship("Robot", back_populates="maintenance_records")

    __table_args__ = (
        Index("ix_maintenance_robot_created", "robot_id", "created_at"),
    )

    def __repr__(self):
        return f"<MaintenanceRecord {self.type} robot={self.robot_id}>"
