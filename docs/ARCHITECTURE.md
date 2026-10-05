# AURA — System Architecture

## 1. Architecture Overview

AURA follows a **layered clean architecture** with clear separation between presentation, business logic, data access, and IoT communication layers.

### Core Architecture Principle

```
PERCEIVE → UNDERSTAND → REASON → DECIDE → ACT → OBSERVE → LEARN → REPEAT
```

The robot operates as an **intelligent edge device**, not a simple remote-controlled vehicle. Local safety logic runs independently of cloud connectivity.

---

## 2. High-Level System Architecture

```mermaid
graph TB
    subgraph "Presentation Layer"
        WEB[Next.js Dashboard]
        MOBILE[Future: Mobile App]
    end

    subgraph "API Gateway Layer"
        REST[REST API - FastAPI]
        WS[WebSocket Server]
    end

    subgraph "Business Logic Layer"
        AUTH[Auth Service]
        ROBOT[Robot Service]
        TELEM[Telemetry Service]
        ALERT[Alert Service]
        NAV[Navigation Service]
        AI_SVC[AI Service]
        ANALYTICS[Analytics Service]
        NOTIFY[Notification Service]
    end

    subgraph "Data Layer"
        PG[(PostgreSQL)]
        CACHE[(Redis - Future)]
    end

    subgraph "IoT Layer"
        MQTT_BROKER[Mosquitto MQTT Broker]
        MQTT_CLIENT[MQTT Client Service]
    end

    subgraph "AI Layer"
        OBJ_DET[Object Detection - YOLO]
        ANOMALY[Anomaly Detection]
        NLP[NL Command Interpreter]
    end

    subgraph "Edge Layer"
        subgraph "Raspberry Pi"
            CAM[Camera Processing]
            AI_EDGE[Edge AI Inference]
            COORD[Robot Coordinator]
            LOCAL_SAFETY[Local Safety Logic]
        end
        subgraph "ESP32"
            MOTORS[Motor Control]
            SENSORS[Sensor Reading]
        end
    end

    subgraph "Simulator"
        SIM[Robot Simulator]
    end

    WEB --> REST
    WEB --> WS
    REST --> AUTH
    REST --> ROBOT
    REST --> TELEM
    REST --> ALERT
    REST --> NAV
    REST --> AI_SVC
    REST --> ANALYTICS
    WS --> ROBOT
    WS --> TELEM

    AUTH --> PG
    ROBOT --> PG
    TELEM --> PG
    ALERT --> PG
    NAV --> PG
    ANALYTICS --> PG

    ROBOT --> MQTT_CLIENT
    MQTT_CLIENT --> MQTT_BROKER

    AI_SVC --> OBJ_DET
    AI_SVC --> ANOMALY
    AI_SVC --> NLP

    MQTT_BROKER --> COORD
    MQTT_BROKER --> SIM
    COORD --> CAM
    COORD --> AI_EDGE
    COORD --> LOCAL_SAFETY
    COORD --> SENSORS
    COORD --> MOTORS
```

---

## 3. Component Architecture

```mermaid
graph LR
    subgraph "Frontend Components"
        DASH[Dashboard]
        ROBOT_LIST[Robot List]
        ROBOT_DETAIL[Robot Detail]
        CONTROL[Control Panel]
        CAMERA[Camera View]
        TELEM_UI[Telemetry Charts]
        ALERT_UI[Alert Center]
        ANALYTICS_UI[Analytics]
        AUTH_UI[Auth Pages]
    end

    subgraph "Backend Components"
        direction TB
        API_LAYER[API Layer<br/>Routes + Dependencies]
        SERVICE_LAYER[Service Layer<br/>Business Logic]
        MODEL_LAYER[Model Layer<br/>SQLAlchemy ORM]
        SCHEMA_LAYER[Schema Layer<br/>Pydantic Validation]
        CORE_LAYER[Core Layer<br/>Security + Config + Logging]
    end

    API_LAYER --> SERVICE_LAYER
    SERVICE_LAYER --> MODEL_LAYER
    API_LAYER --> SCHEMA_LAYER
    SERVICE_LAYER --> CORE_LAYER
```

---

## 4. Deployment Architecture

```mermaid
graph TB
    subgraph "Docker Compose Environment"
        subgraph "Frontend Container"
            NEXT[Next.js :3000]
        end
        subgraph "Backend Container"
            FAST[FastAPI :8000]
        end
        subgraph "Database Container"
            PGDB[(PostgreSQL :5432)]
        end
        subgraph "MQTT Container"
            MOSQ[Mosquitto :1883 / :9001]
        end
    end

    subgraph "Edge Device (Physical / Simulator)"
        ROBOT_EDGE[Robot Controller]
    end

    NEXT -->|REST + WS| FAST
    FAST -->|SQLAlchemy| PGDB
    FAST -->|Paho MQTT| MOSQ
    ROBOT_EDGE -->|MQTT| MOSQ

    USER((User)) -->|HTTPS| NEXT
```

---

## 5. Data Flow Architecture

### 5.1 Telemetry Flow

```mermaid
sequenceDiagram
    participant Robot as Robot/Simulator
    participant MQTT as MQTT Broker
    participant Backend as FastAPI Backend
    participant DB as PostgreSQL
    participant WS as WebSocket
    participant UI as Dashboard

    Robot->>MQTT: Publish telemetry (robot/{id}/telemetry)
    MQTT->>Backend: Deliver to subscribed client
    Backend->>Backend: Validate telemetry (Pydantic)
    Backend->>DB: Store telemetry record
    Backend->>Backend: Check anomaly thresholds
    alt Anomaly Detected
        Backend->>DB: Create alert
        Backend->>WS: Broadcast alert_created
    end
    Backend->>WS: Broadcast telemetry_update
    WS->>UI: Real-time update
```

### 5.2 Command Flow

```mermaid
sequenceDiagram
    participant User as Operator
    participant UI as Dashboard
    participant API as FastAPI
    participant Auth as Auth Service
    participant Safety as Safety Check
    participant MQTT as MQTT Broker
    participant Robot as Robot/Simulator

    User->>UI: Click "Move Forward"
    UI->>API: POST /api/v1/robots/{id}/command
    API->>Auth: Verify JWT + Check Role
    Auth-->>API: Authorized (OPERATOR/ADMIN)
    API->>Safety: Validate command safety
    Safety->>Safety: Check emergency_stop, battery, obstacles
    alt Safe
        Safety-->>API: Command approved
        API->>MQTT: Publish to robot/{id}/command
        MQTT->>Robot: Deliver command
        Robot->>Robot: Execute movement
        Robot->>MQTT: Publish status update
    else Unsafe
        Safety-->>API: Command rejected (reason)
        API-->>UI: Error response
    end
```

### 5.3 Alert Generation Flow

```mermaid
sequenceDiagram
    participant Robot as Robot/Simulator
    participant MQTT as MQTT Broker
    participant Backend as Backend
    participant Anomaly as Anomaly Detection
    participant DB as PostgreSQL
    participant WS as WebSocket
    participant UI as Dashboard

    Robot->>MQTT: Telemetry (gas_level: 65)
    MQTT->>Backend: Deliver telemetry
    Backend->>Anomaly: Check thresholds
    Anomaly->>Anomaly: gas_level > 50 → CRITICAL
    Anomaly-->>Backend: Alert: HIGH_GAS
    Backend->>DB: Store alert
    Backend->>WS: Broadcast alert_created
    WS->>UI: Show critical alert notification
    Backend->>MQTT: Publish robot/{id}/command (EMERGENCY_STOP)
    MQTT->>Robot: Emergency stop command
    Robot->>Robot: Stop all motors
```

---

## 6. Authentication & Authorization Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend as Next.js
    participant API as FastAPI
    participant Auth as Auth Service
    participant DB as PostgreSQL

    User->>Frontend: Enter credentials
    Frontend->>API: POST /api/v1/auth/login
    API->>Auth: Validate credentials
    Auth->>DB: Query user by email
    DB-->>Auth: User record
    Auth->>Auth: Verify password (bcrypt)
    Auth->>Auth: Generate JWT (access + refresh)
    Auth-->>API: Tokens
    API-->>Frontend: { access_token, refresh_token }
    Frontend->>Frontend: Store tokens

    Note over Frontend,API: Subsequent requests
    Frontend->>API: GET /api/v1/robots (Authorization: Bearer <token>)
    API->>Auth: Decode & verify JWT
    Auth->>Auth: Check role permissions
    Auth-->>API: User context
    API-->>Frontend: Robot data
```

---

## 7. MQTT Topic Architecture

```
robot/
├── {robot_id}/
│   ├── telemetry      # Sensor data (robot → backend)
│   ├── command         # Control commands (backend → robot)
│   ├── status          # Robot status updates (robot → backend)
│   ├── sensor          # Raw sensor readings (robot → backend)
│   ├── alert           # Robot-generated alerts (robot → backend)
│   ├── heartbeat       # Liveness signal (robot → backend)
│   ├── detection       # AI detection events (robot → backend)
│   ├── navigation      # Navigation updates (bidirectional)
│   └── system          # System events (bidirectional)
```

### Message Direction

| Topic | Direction | QoS |
|-------|-----------|-----|
| `telemetry` | Robot → Backend | 0 (at most once) |
| `command` | Backend → Robot | 1 (at least once) |
| `status` | Robot → Backend | 1 (at least once) |
| `heartbeat` | Robot → Backend | 0 (at most once) |
| `alert` | Robot → Backend | 2 (exactly once) |
| `detection` | Robot → Backend | 1 (at least once) |

---

## 8. Safety Architecture

Safety operates at two levels:

### Edge-Level Safety (Raspberry Pi)
- Runs locally, independent of cloud
- Obstacle detection → immediate stop
- Gas detection → emergency mode
- Battery critical → safe mode
- Communication timeout → stop and wait

### Backend-Level Safety
- Command validation before MQTT publish
- Permission checking (RBAC)
- Emergency stop override
- Alert generation and notification

```mermaid
graph TB
    CMD[Incoming Command] --> PERM{Permission Check}
    PERM -->|Denied| REJECT[Reject Command]
    PERM -->|Allowed| EMRG{Emergency Stop Active?}
    EMRG -->|Yes| REJECT
    EMRG -->|No| BATT{Battery OK?}
    BATT -->|Critical| SAFE[Enter Safe Mode]
    BATT -->|OK| OBS{Obstacle Clear?}
    OBS -->|Blocked| STOP[Stop + Alert]
    OBS -->|Clear| GAS{Gas Level Safe?}
    GAS -->|Dangerous| EMRG_MODE[Emergency Mode]
    GAS -->|Safe| EXEC[Execute Command]
```

---

## 9. Hardware Abstraction

```mermaid
classDiagram
    class RobotController {
        <<interface>>
        +move_forward(speed)
        +move_backward(speed)
        +turn_left(speed)
        +turn_right(speed)
        +stop()
        +emergency_stop()
        +get_status()
    }

    class SensorProvider {
        <<interface>>
        +read_distance() float
        +read_temperature() float
        +read_humidity() float
        +read_gas_level() float
        +read_battery() float
        +read_imu() IMUData
    }

    class CameraProvider {
        <<interface>>
        +capture_frame() Frame
        +start_stream()
        +stop_stream()
        +is_available() bool
    }

    class RealRobotController {
        -serial_connection
        +move_forward(speed)
        +stop()
    }

    class SimulatedRobotController {
        -virtual_position
        -virtual_heading
        +move_forward(speed)
        +stop()
    }

    class RealSensorProvider {
        -gpio_pins
        +read_distance() float
    }

    class SimulatedSensorProvider {
        -noise_generator
        +read_distance() float
    }

    RobotController <|.. RealRobotController
    RobotController <|.. SimulatedRobotController
    SensorProvider <|.. RealSensorProvider
    SensorProvider <|.. SimulatedSensorProvider
    CameraProvider <|.. RealCameraProvider
    CameraProvider <|.. MockCameraProvider
```

---

## 10. Scalability Design

### Per-Robot Isolation

- Each robot has dedicated MQTT topics (`robot/{id}/*`)
- Telemetry stored with `robot_id` foreign key + index
- WebSocket channels per robot (`/ws/robots/{id}`)
- Commands routed by robot ID

### Scaling Strategy

| Scale | Approach |
|-------|----------|
| 1 robot | Single Docker Compose |
| 10 robots | Same infra, connection pooling |
| 100 robots | Separate MQTT topics, async processing, read replicas |
| 1000+ robots | Microservices, message queues, time-series DB |

---

## 11. Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend Framework | FastAPI | Async-native, auto OpenAPI docs, Pydantic integration |
| Database | PostgreSQL | ACID, JSON support, proven at scale |
| ORM | SQLAlchemy 2.0 | Async support, mature ecosystem |
| IoT Protocol | MQTT | Lightweight, pub/sub, perfect for IoT |
| Frontend | Next.js 14 | SSR, app router, TypeScript, React ecosystem |
| Auth | JWT | Stateless, scalable, standard |
| AI/CV | YOLOv8 + OpenCV | Real-time detection, edge-deployable |
| Containerization | Docker Compose | Simple multi-service orchestration |

---

## 12. Directory Structure Rationale

```
backend/
├── app/
│   ├── api/          # HTTP route handlers (thin controllers)
│   ├── models/       # SQLAlchemy ORM models (data layer)
│   ├── schemas/      # Pydantic request/response models (validation)
│   ├── services/     # Business logic (domain layer)
│   ├── ai/           # AI/ML services (isolated concern)
│   └── core/         # Cross-cutting: config, security, logging, exceptions
```

This follows the **Repository/Service pattern**:
- **API layer** handles HTTP concerns only
- **Service layer** contains all business logic
- **Model layer** handles database mapping
- **Schema layer** handles validation and serialization
- Dependencies flow inward: API → Service → Model
