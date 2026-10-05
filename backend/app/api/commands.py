"""
AURA Backend — Command Routes
================================
API endpoints for issuing commands to robots.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.dependencies import OperatorUser, CurrentUser
from app.services.robot_service import RobotService
from app.schemas.command import CommandRequest, CommandResponse
from app.core.logging import get_logger

router = APIRouter(prefix="/robots", tags=["Commands"])
logger = get_logger("command_api")


@router.post("/{robot_id}/command", response_model=CommandResponse)
async def send_command(
    robot_id: UUID,
    request: CommandRequest,
    current_user: OperatorUser,
    db: AsyncSession = Depends(get_db)
):
    """
    Send a general command to the robot.
    Requires OPERATOR or ADMIN role.
    """
    service = RobotService(db)
    cmd = await service.send_command(
        robot_id=robot_id,
        command_type=request.command,
        user_id=current_user.id,
        parameters=request.parameters or ({"speed": request.speed} if request.speed else None),
        source="api"
    )
    return {
        "success": True,
        "command_id": cmd.id,
        "command": cmd.command.value,
        "status": cmd.status.value,
        "message": f"Command {cmd.command.value} sent successfully."
    }


@router.post("/{robot_id}/stop", response_model=CommandResponse)
async def stop_robot(
    robot_id: UUID,
    current_user: OperatorUser,
    db: AsyncSession = Depends(get_db)
):
    """Convenience endpoint to stop robot movement."""
    service = RobotService(db)
    cmd = await service.send_command(
        robot_id=robot_id,
        command_type="STOP",
        user_id=current_user.id
    )
    return {
        "success": True,
        "command_id": cmd.id,
        "command": "STOP",
        "status": cmd.status.value,
        "message": "Stop command sent."
    }


@router.post("/{robot_id}/emergency-stop", response_model=CommandResponse)
async def emergency_stop(
    robot_id: UUID,
    current_user: OperatorUser,
    db: AsyncSession = Depends(get_db)
):
    """
    EMERGENCY STOP - overrides all other commands and enters EMERGENCY mode.
    """
    service = RobotService(db)
    cmd = await service.send_command(
        robot_id=robot_id,
        command_type="EMERGENCY_STOP",
        user_id=current_user.id
    )
    return {
        "success": True,
        "command_id": cmd.id,
        "command": "EMERGENCY_STOP",
        "status": cmd.status.value,
        "message": "CRITICAL: Emergency stop activated."
    }


@router.post("/{robot_id}/patrol/start", response_model=CommandResponse)
async def start_patrol(
    robot_id: UUID,
    current_user: OperatorUser,
    db: AsyncSession = Depends(get_db)
):
    """Start autonomous patrol."""
    service = RobotService(db)
    cmd = await service.send_command(
        robot_id=robot_id,
        command_type="START_PATROL",
        user_id=current_user.id
    )
    return {
        "success": True,
        "command_id": cmd.id,
        "command": "START_PATROL",
        "status": cmd.status.value,
        "message": "Patrol started."
    }


@router.post("/{robot_id}/return-home", response_model=CommandResponse)
async def return_home(
    robot_id: UUID,
    current_user: OperatorUser,
    db: AsyncSession = Depends(get_db)
):
    """Command robot to return to home position."""
    service = RobotService(db)
    cmd = await service.send_command(
        robot_id=robot_id,
        command_type="RETURN_HOME",
        user_id=current_user.id
    )
    return {
        "success": True,
        "command_id": cmd.id,
        "command": "RETURN_HOME",
        "status": cmd.status.value,
        "message": "Returning home."
    }
