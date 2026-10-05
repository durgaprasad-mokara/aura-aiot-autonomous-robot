"""
AURA Backend — Alerts Routes
===============================
API endpoints for global alert management.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.dependencies import ViewerUser, OperatorUser
from app.services.alert_service import AlertService
from app.schemas.alert import AlertListResponse, AlertResponse, AlertAcknowledgeRequest

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=AlertListResponse, dependencies=[Depends(ViewerUser)])
async def list_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get all alerts across all robots."""
    service = AlertService(db)
    alerts, total = await service.get_alerts(
        status=status, severity=severity, skip=skip, limit=limit
    )
    return {"data": alerts, "total": total}


@router.get("/{alert_id}", response_model=AlertResponse, dependencies=[Depends(ViewerUser)])
async def get_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get alert details."""
    service = AlertService(db)
    alert = await service.get_alert(alert_id)
    return alert


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: UUID,
    request: AlertAcknowledgeRequest,
    current_user: OperatorUser,
    db: AsyncSession = Depends(get_db)
):
    """
    Acknowledge an alert.
    Requires OPERATOR or ADMIN role.
    """
    service = AlertService(db)
    alert = await service.acknowledge_alert(alert_id, user_id=current_user.id)
    # TODO: Log request.notes in AuditLog if provided
    return alert
