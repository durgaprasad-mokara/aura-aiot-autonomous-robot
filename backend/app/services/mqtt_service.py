"""
AURA Backend — MQTT Service
==============================
Manages connection to the Mosquitto broker, subscription to topics,
and message routing to backend services.
"""

import json
import asyncio
from typing import Any, Callable, Dict
import paho.mqtt.client as mqtt

from app.config import get_settings
from app.core.logging import get_logger
from app.database import async_session_factory
from app.services.telemetry_service import TelemetryService
from app.services.robot_service import RobotService
from app.schemas.telemetry import TelemetryIngest
from app.schemas.detection import DetectionIngest
from pydantic import ValidationError

logger = get_logger("mqtt_service")
settings = get_settings()


class MQTTClientService:
    """Singleton-ish MQTT service for the FastAPI backend."""

    def __init__(self):
        self.client = mqtt.Client(client_id=settings.MQTT_CLIENT_ID, protocol=mqtt.MQTTv5)
        self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
        
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        
        self.connected = False
        self.loop = asyncio.get_event_loop()
        
        # Callbacks for specific topics
        self.callbacks: Dict[str, Callable] = {
            "robot/+/telemetry": self.handle_telemetry,
            "robot/+/heartbeat": self.handle_heartbeat,
            "robot/+/status": self.handle_status,
            "robot/+/detection": self.handle_detection,
            "robot/+/alert": self.handle_alert,
        }

    def start(self):
        """Connect to broker and start loop."""
        try:
            logger.info("mqtt_connecting", host=settings.MQTT_HOST, port=settings.MQTT_PORT)
            self.client.connect(settings.MQTT_HOST, settings.MQTT_PORT, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error("mqtt_connection_failed", error=str(e))

    def stop(self):
        """Disconnect from broker."""
        self.client.loop_stop()
        self.client.disconnect()

    def on_connect(self, client, userdata, flags, rc, properties=None):
        """Callback when connected to broker."""
        if rc == 0:
            self.connected = True
            logger.info("mqtt_connected")
            # Subscribe to all relevant topics
            for topic in self.callbacks.keys():
                client.subscribe(topic, qos=1)
                logger.debug("mqtt_subscribed", topic=topic)
        else:
            logger.error("mqtt_connect_error", return_code=rc)

    def on_disconnect(self, client, userdata, rc, properties=None):
        """Callback when disconnected."""
        self.connected = False
        logger.warning("mqtt_disconnected", return_code=rc)

    def on_message(self, client, userdata, msg):
        """Global message callback. Routes to specific handlers."""
        topic = msg.topic
        payload = msg.payload.decode("utf-8")
        
        logger.debug("mqtt_message_received", topic=topic, size=len(payload))
        
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            logger.warning("mqtt_invalid_json", topic=topic, payload=payload[:100])
            return

        # Find matching route
        for route, handler in self.callbacks.items():
            if mqtt.topic_matches_sub(route, topic):
                # We schedule the async handler on the main event loop
                asyncio.run_coroutine_threadsafe(handler(topic, data), self.loop)
                return
                
        logger.debug("mqtt_unhandled_topic", topic=topic)

    def publish(self, topic: str, payload: dict, qos: int = 1):
        """Publish a message to the broker."""
        if not self.connected:
            logger.warning("mqtt_publish_dropped", reason="not connected", topic=topic)
            return
            
        json_payload = json.dumps(payload)
        self.client.publish(topic, json_payload, qos=qos)
        logger.debug("mqtt_published", topic=topic)

    # ========================
    # Topic Handlers (Async)
    # ========================

    async def handle_telemetry(self, topic: str, data: dict):
        """Handle incoming telemetry (robot/+/telemetry)."""
        try:
            # Validate payload
            telemetry = TelemetryIngest(**data)
            
            async with async_session_factory() as db:
                # Need to look up robot internal UUID by device_id
                robot_service = RobotService(db)
                robot = await robot_service.get_robot_by_device_id(telemetry.robot_id)
                
                if not robot:
                    logger.warning("mqtt_unknown_robot", device_id=telemetry.robot_id)
                    return
                    
                tel_service = TelemetryService(db)
                await tel_service.store_telemetry(
                    robot_id=robot.id,
                    temperature=telemetry.temperature,
                    humidity=telemetry.humidity,
                    gas_level=telemetry.gas_level,
                    distance=telemetry.distance,
                    battery=telemetry.battery,
                    speed=telemetry.speed,
                    cpu_usage=telemetry.cpu_usage,
                    memory_usage=telemetry.memory_usage,
                    timestamp=telemetry.timestamp,
                )
                await db.commit()
                
                # TODO: Check for anomalies and trigger alerts
                # TODO: Broadcast to WebSockets
                
        except ValidationError as e:
            logger.warning("mqtt_telemetry_validation_failed", error=str(e))
        except Exception as e:
            logger.error("mqtt_telemetry_error", error=str(e))

    async def handle_heartbeat(self, topic: str, data: dict):
        """Handle incoming heartbeat (robot/+/heartbeat)."""
        robot_id = data.get("robot_id")
        if not robot_id:
            return
            
        async with async_session_factory() as db:
            robot_service = RobotService(db)
            await robot_service.update_heartbeat(robot_id)
            await db.commit()

    async def handle_status(self, topic: str, data: dict):
        """Handle status updates."""
        pass # Implementation pending

    async def handle_detection(self, topic: str, data: dict):
        """Handle AI detection events."""
        pass # Implementation pending

    async def handle_alert(self, topic: str, data: dict):
        """Handle robot-generated alerts."""
        pass # Implementation pending


# Global singleton instance
mqtt_client = MQTTClientService()
