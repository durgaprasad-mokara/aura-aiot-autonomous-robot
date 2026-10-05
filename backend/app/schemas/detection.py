"""
AURA Backend — Detection Schemas
===================================
Request/response models for AI detections.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any
from uuid import UUID
from datetime import datetime


class DetectionResponse(BaseModel):
    """Object detection response."""
    id: UUID
    robot_id: UUID
    object_type: str
    confidence: float
    bounding_box: Optional[dict[str, Any]] = None
    image_path: Optional[str] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


class DetectionListResponse(BaseModel):
    """Detection list response."""
    success: bool = True
    data: list[DetectionResponse]
    total: int


class DetectionIngest(BaseModel):
    """Incoming detection from MQTT."""
    robot_id: str
    object_type: str = Field(..., min_length=1, max_length=50)
    confidence: float = Field(..., ge=0, le=1)
    bounding_box: Optional[dict[str, Any]] = None
    image_path: Optional[str] = None
    timestamp: datetime
