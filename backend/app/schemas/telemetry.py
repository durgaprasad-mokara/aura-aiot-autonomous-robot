"""
AURA Backend — Telemetry Schemas
===================================
Validation models for telemetry data ingestion and retrieval.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime


class TelemetryIngest(BaseModel):
    """Incoming telemetry from MQTT — validates robot telemetry messages."""
    robot_id: str = Field(..., min_length=1)
    timestamp: datetime
    battery: Optional[float] = Field(None, ge=0, le=100)
    temperature: Optional[float] = Field(None, ge=-40, le=125)
    humidity: Optional[float] = Field(None, ge=0, le=100)
    gas_level: Optional[float] = Field(None, ge=0)
    distance: Optional[float] = Field(None, ge=0)
    speed: Optional[float] = Field(None, ge=0)
    cpu_usage: Optional[float] = Field(None, ge=0, le=100)
    memory_usage: Optional[float] = Field(None, ge=0, le=100)


class TelemetryResponse(BaseModel):
    """Telemetry record response."""
    id: UUID
    robot_id: UUID
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    gas_level: Optional[float] = None
    distance: Optional[float] = None
    battery: Optional[float] = None
    speed: Optional[float] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


class TelemetryListResponse(BaseModel):
    """Paginated telemetry list."""
    success: bool = True
    data: list[TelemetryResponse]
    total: int


class TelemetryLatestResponse(BaseModel):
    """Latest telemetry snapshot."""
    success: bool = True
    data: Optional[TelemetryResponse] = None
