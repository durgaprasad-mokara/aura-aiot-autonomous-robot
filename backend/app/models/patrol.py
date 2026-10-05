"""
AURA Backend — Patrol Models
===============================
Patrol routes, waypoints, and session tracking.
"""

import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Float, Integer, DateTime, Enum, Text, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class PatrolStatus(str, enum.Enum):
    """Patrol session status."""
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"
    PAUSED = "PAUSED"


class PatrolRoute(Base):
    """A named patrol route consisting of ordered waypoints."""
    __tablename__ = "patrol_routes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Integer, default=1, nullable=False)
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
    points = relationship(
        "PatrolPoint", back_populates="route",
        cascade="all, delete-orphan",
        order_by="PatrolPoint.sequence_order",
    )
    sessions = relationship("PatrolSession", back_populates="route")

    def __repr__(self):
        return f"<PatrolRoute {self.name}>"


class PatrolPoint(Base):
    """A waypoint in a patrol route."""
    __tablename__ = "patrol_points"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    route_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patrol_routes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(100), nullable=False)  # e.g., "Entrance", "Hallway"
    x = Column(Float, nullable=False, default=0.0)
    y = Column(Float, nullable=False, default=0.0)
    sequence_order = Column(Integer, nullable=False)
    dwell_time_seconds = Column(Integer, nullable=True, default=5)  # time to stay at point

    # Relationships
    route = relationship("PatrolRoute", back_populates="points")

    __table_args__ = (
        Index("ix_patrol_points_route_order", "route_id", "sequence_order"),
    )

    def __repr__(self):
        return f"<PatrolPoint {self.name} ({self.x}, {self.y}) seq={self.sequence_order}>"


class PatrolSession(Base):
    """A single patrol execution session."""
    __tablename__ = "patrol_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    robot_id = Column(
        UUID(as_uuid=True),
        ForeignKey("robots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    route_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patrol_routes.id", ondelete="SET NULL"),
        nullable=True,
    )
    status = Column(
        Enum(PatrolStatus), nullable=False, default=PatrolStatus.SCHEDULED
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    points_visited = Column(Integer, nullable=True, default=0)
    total_points = Column(Integer, nullable=True, default=0)
    distance_covered = Column(Float, nullable=True, default=0.0)
    battery_consumed = Column(Float, nullable=True, default=0.0)
    alerts_count = Column(Integer, nullable=True, default=0)
    detections_count = Column(Integer, nullable=True, default=0)

    # Relationships
    robot = relationship("Robot", back_populates="patrol_sessions")
    route = relationship("PatrolRoute", back_populates="sessions")

    __table_args__ = (
        Index("ix_patrol_sessions_robot_started", "robot_id", "started_at"),
    )

    def __repr__(self):
        return f"<PatrolSession robot={self.robot_id} [{self.status.value}]>"
