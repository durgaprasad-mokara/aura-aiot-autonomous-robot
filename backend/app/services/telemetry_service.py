"""
AURA Backend — Telemetry Service
====================================
Business logic for telemetry ingestion, storage, and retrieval.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.telemetry import Telemetry
from app.models.robot import Robot
from app.core.logging import get_logger

logger = get_logger("telemetry_service")


class TelemetryService:
    """Handles telemetry data ingestion and retrieval."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def store_telemetry(
        self,
        robot_id: UUID,
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        gas_level: Optional[float] = None,
        distance: Optional[float] = None,
        battery: Optional[float] = None,
        speed: Optional[float] = None,
        cpu_usage: Optional[float] = None,
        memory_usage: Optional[float] = None,
        timestamp: Optional[datetime] = None,
    ) -> Telemetry:
        """Store a telemetry record and update robot status."""
        telemetry = Telemetry(
            robot_id=robot_id,
            temperature=temperature,
            humidity=humidity,
            gas_level=gas_level,
            distance=distance,
            battery=battery,
            speed=speed,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            timestamp=timestamp or datetime.now(timezone.utc),
        )
        self.db.add(telemetry)

        # Also update robot's battery in the robots table
        if battery is not None:
            result = await self.db.execute(select(Robot).where(Robot.id == robot_id))
            robot = result.scalar_one_or_none()
            if robot:
                robot.battery = battery
                robot.last_seen = datetime.now(timezone.utc)

        await self.db.flush()
        return telemetry

    async def get_latest(self, robot_id: UUID) -> Optional[Telemetry]:
        """Get the most recent telemetry for a robot."""
        result = await self.db.execute(
            select(Telemetry)
            .where(Telemetry.robot_id == robot_id)
            .order_by(Telemetry.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_history(
        self,
        robot_id: UUID,
        hours: int = 1,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Telemetry], int]:
        """Get telemetry history for a time range."""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        # Count
        count_result = await self.db.execute(
            select(func.count(Telemetry.id)).where(
                and_(
                    Telemetry.robot_id == robot_id,
                    Telemetry.timestamp >= since,
                )
            )
        )
        total = count_result.scalar()

        # Fetch
        result = await self.db.execute(
            select(Telemetry)
            .where(
                and_(
                    Telemetry.robot_id == robot_id,
                    Telemetry.timestamp >= since,
                )
            )
            .order_by(Telemetry.timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        records = list(result.scalars().all())

        return records, total
