"""
AURA Backend — Alert Service
===============================
Business logic for alert creation, retrieval, and acknowledgement.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertType, AlertSeverity, AlertStatus
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger

logger = get_logger("alert_service")


class AlertService:
    """Handles alert lifecycle management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_alert(
        self,
        robot_id: UUID,
        alert_type: str,
        severity: str,
        title: str,
        message: str,
        source: str = "system",
    ) -> Alert:
        """Create a new alert."""
        alert = Alert(
            robot_id=robot_id,
            type=AlertType(alert_type),
            severity=AlertSeverity(severity),
            title=title,
            message=message,
            source=source,
        )
        self.db.add(alert)
        await self.db.flush()

        logger.info(
            "alert_created",
            alert_id=str(alert.id),
            robot_id=str(robot_id),
            type=alert_type,
            severity=severity,
        )
        return alert

    async def get_alert(self, alert_id: UUID) -> Alert:
        """Get alert by ID."""
        result = await self.db.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            raise NotFoundError("Alert", str(alert_id))
        return alert

    async def get_alerts(
        self,
        robot_id: Optional[UUID] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Alert], int]:
        """Get filtered, paginated alert list."""
        conditions = []
        if robot_id:
            conditions.append(Alert.robot_id == robot_id)
        if severity:
            conditions.append(Alert.severity == AlertSeverity(severity))
        if status:
            conditions.append(Alert.status == AlertStatus(status))

        where_clause = and_(*conditions) if conditions else True

        # Count
        count_result = await self.db.execute(
            select(func.count(Alert.id)).where(where_clause)
        )
        total = count_result.scalar()

        # Fetch
        result = await self.db.execute(
            select(Alert)
            .where(where_clause)
            .order_by(Alert.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        alerts = list(result.scalars().all())

        return alerts, total

    async def acknowledge_alert(self, alert_id: UUID, user_id: UUID) -> Alert:
        """Acknowledge an alert."""
        alert = await self.get_alert(alert_id)
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now(timezone.utc)
        alert.acknowledged_by = user_id
        await self.db.flush()

        logger.info("alert_acknowledged", alert_id=str(alert_id), user_id=str(user_id))
        return alert

    async def get_active_count(self, robot_id: Optional[UUID] = None) -> dict:
        """Get count of active alerts by severity."""
        conditions = [Alert.status == AlertStatus.ACTIVE]
        if robot_id:
            conditions.append(Alert.robot_id == robot_id)

        # Critical count
        crit_result = await self.db.execute(
            select(func.count(Alert.id)).where(
                and_(*conditions, Alert.severity == AlertSeverity.CRITICAL)
            )
        )
        critical = crit_result.scalar()

        # Warning count
        warn_result = await self.db.execute(
            select(func.count(Alert.id)).where(
                and_(*conditions, Alert.severity == AlertSeverity.WARNING)
            )
        )
        warnings = warn_result.scalar()

        return {"critical": critical, "warnings": warnings, "total": critical + warnings}
