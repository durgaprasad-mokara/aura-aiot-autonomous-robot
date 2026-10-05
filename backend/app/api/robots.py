"""
AURA Backend — Robot Routes
==============================
API endpoints for robot management and telemetry.
"""

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.dependencies import ViewerUser, AdminUser, OperatorUser
from app.services.robot_service import RobotService
from app.services.telemetry_service import TelemetryService
from app.services.alert_service import AlertService
from app.schemas.robot import (
    RobotCreate, RobotUpdate, RobotResponse, RobotListResponse
)
from app.schemas.telemetry import TelemetryListResponse, TelemetryLatestResponse
from app.schemas.alert import AlertListResponse

router = APIRouter(prefix="/robots", tags=["Robots"])


@router.get("", response_model=RobotListResponse, dependencies=[Depends(ViewerUser)])
async def list_robots(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get all registered robots."""
    service = RobotService(db)
    robots, total = await service.get_all_robots(skip=skip, limit=limit)
    return {"data": robots, "total": total}


@router.post("", response_model=RobotResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(AdminUser)])
async def create_robot(
    request: RobotCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new robot (Admin only)."""
    service = RobotService(db)
    robot = await service.create_robot(**request.model_dump())
    return robot


@router.get("/{robot_id}", response_model=RobotResponse, dependencies=[Depends(ViewerUser)])
async def get_robot(
    robot_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get robot details."""
    service = RobotService(db)
    robot = await service.get_robot(robot_id)
    return robot


@router.put("/{robot_id}", response_model=RobotResponse, dependencies=[Depends(AdminUser)])
async def update_robot(
    robot_id: UUID,
    request: RobotUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update robot metadata (Admin only)."""
    service = RobotService(db)
    robot = await service.update_robot(robot_id, **request.model_dump(exclude_unset=True))
    return robot


@router.delete("/{robot_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(AdminUser)])
async def delete_robot(
    robot_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a robot (Admin only)."""
    service = RobotService(db)
    await service.delete_robot(robot_id)


# ========================
# Telemetry Sub-routes
# ========================

@router.get("/{robot_id}/telemetry", response_model=TelemetryListResponse, dependencies=[Depends(ViewerUser)])
async def get_robot_telemetry(
    robot_id: UUID,
    hours: int = Query(1, ge=1, le=720),
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get historical telemetry for a robot."""
    # Ensure robot exists
    await RobotService(db).get_robot(robot_id)
    
    service = TelemetryService(db)
    records, total = await service.get_history(robot_id, hours=hours, skip=skip, limit=limit)
    return {"data": records, "total": total}


@router.get("/{robot_id}/telemetry/latest", response_model=TelemetryLatestResponse, dependencies=[Depends(ViewerUser)])
async def get_latest_telemetry(
    robot_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get the most recent telemetry snapshot."""
    await RobotService(db).get_robot(robot_id)
    service = TelemetryService(db)
    record = await service.get_latest(robot_id)
    return {"data": record}


# ========================
# Alert Sub-routes
# ========================

@router.get("/{robot_id}/alerts", response_model=AlertListResponse, dependencies=[Depends(ViewerUser)])
async def get_robot_alerts(
    robot_id: UUID,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get alerts for a specific robot."""
    await RobotService(db).get_robot(robot_id)
    service = AlertService(db)
    alerts, total = await service.get_alerts(
        robot_id=robot_id, status=status, severity=severity, skip=skip, limit=limit
    )
    return {"data": alerts, "total": total}
