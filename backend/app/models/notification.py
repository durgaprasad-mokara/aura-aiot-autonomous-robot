"""
AURA Backend — Notification Model
====================================
User-facing notifications (alerts, system messages, etc.).
"""

import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, DateTime, Enum, Text, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class NotificationType(str, enum.Enum):
    """Notification category."""
    ALERT = "ALERT"
    SYSTEM = "SYSTEM"
    ROBOT_EVENT = "ROBOT_EVENT"
    INFO = "INFO"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,  # null = broadcast to all users
        index=True,
    )
    type = Column(Enum(NotificationType), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    data = Column(JSONB, nullable=True)  # Extra context
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    def __repr__(self):
        return f"<Notification [{self.type.value}] {self.title}>"
