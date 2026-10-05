"""
AURA Backend — Alert Schemas
===============================
Request/response models for alert management.
"""

from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class AlertResponse(BaseModel):
    """Alert details response."""
    id: UUID
    robot_id: UUID
    type: str
    severity: str
    title: str
    message: str
    status: str
    source: Optional[str] = None
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[UUID] = None

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    """Alert list response."""
    success: bool = True
    data: list[AlertResponse]
    total: int


class AlertAcknowledgeRequest(BaseModel):
    """Alert acknowledgement."""
    notes: Optional[str] = Field(None, max_length=500)
