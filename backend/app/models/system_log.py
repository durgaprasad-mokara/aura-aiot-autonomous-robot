"""
AURA Backend — System Log & Audit Log Models
===============================================
Structured logging for system events and user audit trails.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, DateTime, Text, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class SystemLog(Base):
    """System-wide event logging."""
    __tablename__ = "system_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level = Column(String(20), nullable=False)  # "INFO", "WARNING", "ERROR", "CRITICAL"
    source = Column(String(100), nullable=False)  # "mqtt_service", "auth", "robot_service"
    message = Column(Text, nullable=False)
    metadata_json = Column(JSONB, nullable=True)
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("ix_system_logs_level_timestamp", "level", "timestamp"),
        Index("ix_system_logs_source", "source"),
    )

    def __repr__(self):
        return f"<SystemLog [{self.level}] {self.source}: {self.message[:50]}>"


class AuditLog(Base):
    """User action audit trail for security and compliance."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action = Column(String(100), nullable=False)  # "login", "send_command", "acknowledge_alert"
    resource_type = Column(String(50), nullable=True)  # "robot", "alert", "user"
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    details = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_logs_user_timestamp", "user_id", "timestamp"),
        Index("ix_audit_logs_action", "action"),
    )

    def __repr__(self):
        return f"<AuditLog {self.action} by user={self.user_id}>"
