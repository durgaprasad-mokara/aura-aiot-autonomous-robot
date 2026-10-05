"""
AURA Backend — WebSockets
============================
Handles real-time updates for clients connected to the dashboard.
"""

import json
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from app.database import get_db
from app.config import get_settings
from app.core.security import decode_token
from app.core.logging import get_logger

logger = get_logger("websocket")
settings = get_settings()

router = APIRouter(prefix="/ws", tags=["WebSocket"])


class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""
    def __init__(self):
        # robot_id -> list of connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # dashboard connections (global)
        self.dashboard_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, robot_id: Optional[str] = None):
        await websocket.accept()
        if robot_id:
            if robot_id not in self.active_connections:
                self.active_connections[robot_id] = []
            self.active_connections[robot_id].append(websocket)
        else:
            self.dashboard_connections.append(websocket)
        logger.debug("ws_connected", robot_id=robot_id)

    def disconnect(self, websocket: WebSocket, robot_id: Optional[str] = None):
        if robot_id:
            if robot_id in self.active_connections:
                self.active_connections[robot_id].remove(websocket)
        else:
            if websocket in self.dashboard_connections:
                self.dashboard_connections.remove(websocket)
        logger.debug("ws_disconnected", robot_id=robot_id)

    async def broadcast_to_robot(self, robot_id: str, message: dict):
        """Send message to all clients watching a specific robot."""
        if robot_id in self.active_connections:
            for connection in self.active_connections[robot_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

    async def broadcast_to_dashboard(self, message: dict):
        """Send message to all clients on the main dashboard."""
        for connection in self.dashboard_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


async def get_ws_user(token: str):
    """Authenticate WebSocket connection."""
    try:
        payload = decode_token(token)
        return payload.get("sub")
    except Exception:
        return None


@router.websocket("/dashboard")
async def websocket_dashboard(websocket: WebSocket, token: str):
    """WebSocket endpoint for global dashboard updates."""
    user_id = await get_ws_user(token)
    if not user_id:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket)
    try:
        while True:
            # Keep alive
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/robots/{robot_id}")
async def websocket_robot(websocket: WebSocket, robot_id: str, token: str):
    """WebSocket endpoint for specific robot updates."""
    user_id = await get_ws_user(token)
    if not user_id:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, robot_id)
    try:
        while True:
            # Client can send simple commands via WS if needed, 
            # but usually REST API is preferred for commands.
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, robot_id)
