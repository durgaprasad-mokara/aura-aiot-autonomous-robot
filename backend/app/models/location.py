"""
AURA Backend — Location Model
================================
Robot location tracking (for map-based navigation).
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Float, DateTime, Text, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Location(Base):
    """Named location / landmark within the operating environment."""
    __tablename__ = "locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    x = Column(Float, nullable=False, default=0.0)
    y = Column(Float, nullable=False, default=0.0)
    floor = Column(String(20), nullable=True, default="1")
    zone = Column(String(50), nullable=True)  # e.g., "A", "B", "C"
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_locations_name", "name"),
    )

    def __repr__(self):
        return f"<Location {self.name} ({self.x}, {self.y})>"
