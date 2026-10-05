# AURA — MQTT Documentation

## Overview

AURA uses **MQTT** as the primary message bus for all IoT communication between the backend and robots (or the simulator). We use **Eclipse Mosquitto** as the broker.

## Topic Structure

All topics follow the pattern: `robot/{robot_device_id}/{channel}`

| Topic | Direction | QoS | Description |
|-------|-----------|-----|-------------|
| `robot/+/telemetry` | Robot → Cloud | 0 | Continuous sensor telemetry streams. |
| `robot/+/command` | Cloud → Robot | 1 | Commands issued to the robot (move, stop, etc.). |
| `robot/+/status` | Robot → Cloud | 1 | Status changes (e.g. mode changed to AUTONOMOUS). |
| `robot/+/heartbeat`| Robot → Cloud | 0 | Liveness ping sent every N seconds. |
| `robot/+/sensor` | Robot → Cloud | 0 | Raw individual sensor readings (if needed). |
| `robot/+/alert` | Robot → Cloud | 2 | Emergency alerts generated locally by the robot. |
| `robot/+/detection` | Robot → Cloud | 1 | AI object detection events (YOLO bounding boxes). |

## Payload Formats

### Telemetry (`robot/{id}/telemetry`)

```json
{
  "robot_id": "AURA-001",
  "timestamp": "2026-10-05T10:30:00Z",
  "battery": 82.5,
  "temperature": 28.4,
  "humidity": 61.0,
  "gas_level": 12.0,
  "distance": 45.0,
  "speed": 0.5,
  "cpu_usage": 34.0,
  "memory_usage": 52.0
}
```

### Command (`robot/{id}/command`)

```json
{
  "robot_id": "AURA-001",
  "command": "MOVE_FORWARD",
  "speed": 60,
  "parameters": {},
  "timestamp": "2026-10-05T10:31:00Z"
}
```

### Heartbeat (`robot/{id}/heartbeat`)

```json
{
  "robot_id": "AURA-001",
  "status": "ONLINE",
  "timestamp": "2026-10-05T10:30:00Z"
}
```

### Alert (`robot/{id}/alert`)

```json
{
  "robot_id": "AURA-001",
  "type": "OBSTACLE_DETECTED",
  "severity": "WARNING",
  "message": "Obstacle detected at 15cm. Stopped automatically.",
  "timestamp": "2026-10-05T10:30:00Z"
}
```
