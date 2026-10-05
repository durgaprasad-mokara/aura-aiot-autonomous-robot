"""
AURA Backend — Robot Service
===============================
Business logic for robot management, status, and command routing.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.robot import Robot, RobotStatus, RobotMode
from app.models.command import RobotCommand, CommandType, CommandStatus
from app.core.exceptions import NotFoundError, RobotOfflineError, CommandRejectedError, ConflictError
from app.core.logging import get_logger
from app.config import get_settings

logger = get_logger("robot_service")
settings = get_settings()


class RobotService:
    """Manages robot registration, status, and commands."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================
    # Robot CRUD
    # ========================

    async def create_robot(self, **kwargs) -> Robot:
        """Register a new robot."""
        # Check device_id uniqueness
        result = await self.db.execute(
            select(Robot).where(Robot.device_id == kwargs.get("device_id"))
        )
        if result.scalar_one_or_none():
            raise ConflictError(f"Robot with device_id '{kwargs['device_id']}' already exists")

        robot = Robot(**kwargs)
        self.db.add(robot)
        await self.db.flush()
        logger.info("robot_created", robot_id=str(robot.id), device_id=robot.device_id)
        return robot

    async def get_robot(self, robot_id: UUID) -> Robot:
        """Get robot by ID."""
        result = await self.db.execute(select(Robot).where(Robot.id == robot_id))
        robot = result.scalar_one_or_none()
        if not robot:
            raise NotFoundError("Robot", str(robot_id))
        return robot

    async def get_robot_by_device_id(self, device_id: str) -> Optional[Robot]:
        """Get robot by device_id (used for MQTT message routing)."""
        result = await self.db.execute(select(Robot).where(Robot.device_id == device_id))
        return result.scalar_one_or_none()

    async def get_all_robots(self, skip: int = 0, limit: int = 50) -> tuple[list[Robot], int]:
        """Get paginated robot list."""
        count_result = await self.db.execute(select(func.count(Robot.id)))
        total = count_result.scalar()

        result = await self.db.execute(
            select(Robot).order_by(Robot.created_at.desc()).offset(skip).limit(limit)
        )
        robots = list(result.scalars().all())
        return robots, total

    async def update_robot(self, robot_id: UUID, **kwargs) -> Robot:
        """Update robot fields."""
        robot = await self.get_robot(robot_id)
        for key, value in kwargs.items():
            if value is not None:
                if key == "status":
                    setattr(robot, key, RobotStatus(value))
                elif key == "mode":
                    setattr(robot, key, RobotMode(value))
                else:
                    setattr(robot, key, value)
        await self.db.flush()
        logger.info("robot_updated", robot_id=str(robot_id))
        return robot

    async def delete_robot(self, robot_id: UUID) -> None:
        """Delete a robot and all associated data."""
        robot = await self.get_robot(robot_id)
        await self.db.delete(robot)
        logger.info("robot_deleted", robot_id=str(robot_id))

    # ========================
    # Status Management
    # ========================

    async def update_heartbeat(self, device_id: str) -> Optional[Robot]:
        """Update robot last_seen on heartbeat. Returns robot or None."""
        robot = await self.get_robot_by_device_id(device_id)
        if robot:
            robot.last_seen = datetime.now(timezone.utc)
            if robot.status == RobotStatus.OFFLINE:
                robot.status = RobotStatus.ONLINE
                logger.info("robot_online", device_id=device_id)
            await self.db.flush()
        return robot

    async def mark_offline(self, robot_id: UUID) -> None:
        """Mark robot as offline (heartbeat timeout)."""
        robot = await self.get_robot(robot_id)
        robot.status = RobotStatus.OFFLINE
        await self.db.flush()
        logger.warning("robot_offline", robot_id=str(robot_id), device_id=robot.device_id)

    # ========================
    # Command Processing
    # ========================

    async def validate_command(self, robot: Robot, command_type: str) -> None:
        """Validate command against safety rules."""
        # Emergency stop check
        if robot.mode == RobotMode.EMERGENCY and command_type != "EMERGENCY_STOP":
            # Allow only STOP commands in emergency
            if command_type not in ("STOP",):
                raise CommandRejectedError("Robot is in EMERGENCY mode. Only STOP is allowed.")

        # Robot must be online (except for EMERGENCY_STOP)
        if robot.status == RobotStatus.OFFLINE and command_type != "EMERGENCY_STOP":
            raise RobotOfflineError(robot.device_id)

        # Battery check for movement commands
        movement_commands = {
            "MOVE_FORWARD", "MOVE_BACKWARD", "TURN_LEFT", "TURN_RIGHT",
            "ROTATE_LEFT", "ROTATE_RIGHT", "START_PATROL"
        }
        if command_type in movement_commands:
            if robot.battery is not None and robot.battery < settings.ROBOT_CRITICAL_BATTERY:
                raise CommandRejectedError(
                    f"Battery critically low ({robot.battery}%). Cannot execute movement."
                )

    async def send_command(
        self,
        robot_id: UUID,
        command_type: str,
        user_id: Optional[UUID] = None,
        parameters: Optional[dict] = None,
        source: str = "api",
    ) -> RobotCommand:
        """Create and queue a command for a robot."""
        robot = await self.get_robot(robot_id)

        # Validate command
        await self.validate_command(robot, command_type)

        # Handle mode changes
        if command_type == "EMERGENCY_STOP":
            robot.mode = RobotMode.EMERGENCY
        elif command_type == "START_PATROL":
            robot.mode = RobotMode.AUTONOMOUS
        elif command_type == "RETURN_HOME":
            robot.mode = RobotMode.RETURN_HOME
        elif command_type == "STOP_PATROL":
            robot.mode = RobotMode.MANUAL
        elif command_type in ("MOVE_FORWARD", "MOVE_BACKWARD", "TURN_LEFT", "TURN_RIGHT"):
            if robot.mode != RobotMode.MANUAL:
                robot.mode = RobotMode.MANUAL

        # Create command record
        cmd = RobotCommand(
            robot_id=robot_id,
            issued_by=user_id,
            command=CommandType(command_type),
            parameters=parameters,
            status=CommandStatus.PENDING,
            source=source,
        )
        self.db.add(cmd)
        await self.db.flush()

        logger.info(
            "command_created",
            command_id=str(cmd.id),
            robot_id=str(robot_id),
            command=command_type,
            source=source,
        )
        return cmd
