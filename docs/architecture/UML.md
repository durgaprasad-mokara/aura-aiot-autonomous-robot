# AURA — UML Diagrams

## 1. Class Diagram — Core Domain Model

```mermaid
classDiagram
    class User {
        +UUID id
        +String name
        +String email
        +String password_hash
        +Role role
        +Boolean is_active
        +DateTime created_at
        +DateTime updated_at
        +DateTime last_login
        +verify_password(password) bool
    }

    class Role {
        <<enumeration>>
        ADMIN
        OPERATOR
        VIEWER
    }

    class Robot {
        +UUID id
        +String name
        +String device_id
        +String serial_number
        +RobotStatus status
        +RobotMode mode
        +Float battery
        +String firmware_version
        +String ip_address
        +DateTime last_seen
        +DateTime created_at
        +DateTime updated_at
    }

    class RobotStatus {
        <<enumeration>>
        ONLINE
        OFFLINE
        MAINTENANCE
        ERROR
    }

    class RobotMode {
        <<enumeration>>
        MANUAL
        AUTONOMOUS
        RETURN_HOME
        EMERGENCY
    }

    class Telemetry {
        +UUID id
        +UUID robot_id
        +Float temperature
        +Float humidity
        +Float gas_level
        +Float distance
        +Float battery
        +Float speed
        +Float cpu_usage
        +Float memory_usage
        +DateTime timestamp
    }

    class Alert {
        +UUID id
        +UUID robot_id
        +AlertType type
        +Severity severity
        +String title
        +String message
        +AlertStatus status
        +String source
        +DateTime created_at
        +DateTime acknowledged_at
        +UUID acknowledged_by
    }

    class AlertType {
        <<enumeration>>
        HIGH_GAS
        LOW_BATTERY
        HIGH_TEMPERATURE
        OBSTACLE_DETECTED
        COMMUNICATION_LOST
        SENSOR_FAILURE
        INTRUSION_DETECTED
        SYSTEM_ERROR
    }

    class Severity {
        <<enumeration>>
        INFO
        WARNING
        CRITICAL
    }

    class AlertStatus {
        <<enumeration>>
        ACTIVE
        ACKNOWLEDGED
        RESOLVED
    }

    class RobotCommand {
        +UUID id
        +UUID robot_id
        +UUID issued_by
        +CommandType command
        +JSON parameters
        +CommandStatus status
        +DateTime issued_at
        +DateTime executed_at
    }

    class CommandType {
        <<enumeration>>
        MOVE_FORWARD
        MOVE_BACKWARD
        TURN_LEFT
        TURN_RIGHT
        ROTATE_LEFT
        ROTATE_RIGHT
        STOP
        START_PATROL
        STOP_PATROL
        RETURN_HOME
        EMERGENCY_STOP
        SET_SPEED
    }

    class Detection {
        +UUID id
        +UUID robot_id
        +String object_type
        +Float confidence
        +JSON bounding_box
        +String image_path
        +DateTime timestamp
    }

    class PatrolSession {
        +UUID id
        +UUID robot_id
        +UUID patrol_route_id
        +DateTime started_at
        +DateTime completed_at
        +PatrolStatus status
        +Integer points_visited
        +Float distance_covered
        +Float battery_consumed
    }

    class PatrolPoint {
        +UUID id
        +UUID patrol_route_id
        +String name
        +Float x
        +Float y
        +Integer sequence_order
    }

    class SystemLog {
        +UUID id
        +String level
        +String source
        +String message
        +JSON metadata
        +DateTime timestamp
    }

    class AuditLog {
        +UUID id
        +UUID user_id
        +String action
        +String resource_type
        +UUID resource_id
        +JSON details
        +DateTime timestamp
    }

    User "1" --> "*" RobotCommand : issues
    User "1" --> "*" AuditLog : generates
    User "1" --> "*" Alert : acknowledges
    User --> Role

    Robot "1" --> "*" Telemetry : produces
    Robot "1" --> "*" Alert : triggers
    Robot "1" --> "*" RobotCommand : receives
    Robot "1" --> "*" Detection : generates
    Robot "1" --> "*" PatrolSession : executes
    Robot --> RobotStatus
    Robot --> RobotMode

    Alert --> AlertType
    Alert --> Severity
    Alert --> AlertStatus

    RobotCommand --> CommandType

    PatrolSession "1" --> "*" PatrolPoint : visits
```

---

## 2. Sequence Diagram — User Login

```mermaid
sequenceDiagram
    actor User
    participant UI as Next.js Frontend
    participant API as FastAPI Backend
    participant Auth as Auth Service
    participant DB as PostgreSQL

    User->>UI: Enter email + password
    UI->>API: POST /api/v1/auth/login
    API->>Auth: authenticate(email, password)
    Auth->>DB: SELECT user WHERE email = ?
    DB-->>Auth: User record
    Auth->>Auth: bcrypt.verify(password, hash)
    alt Valid credentials
        Auth->>Auth: Generate JWT access + refresh tokens
        Auth->>DB: UPDATE user SET last_login = now()
        Auth-->>API: TokenPair(access, refresh)
        API-->>UI: 200 { access_token, refresh_token, user }
        UI->>UI: Store tokens, redirect to /dashboard
    else Invalid credentials
        Auth-->>API: AuthenticationError
        API-->>UI: 401 { error: "Invalid credentials" }
        UI->>UI: Show error message
    end
```

---

## 3. Sequence Diagram — Manual Robot Command

```mermaid
sequenceDiagram
    actor Operator
    participant UI as Dashboard
    participant API as FastAPI
    participant Auth as Auth Service
    participant RobotSvc as Robot Service
    participant Safety as Safety Check
    participant MQTT as MQTT Broker
    participant Robot as Robot/Simulator

    Operator->>UI: Click "Move Forward"
    UI->>API: POST /api/v1/robots/{id}/command<br/>{ command: "MOVE_FORWARD", speed: 60 }
    API->>Auth: Verify JWT token
    Auth-->>API: User (role: OPERATOR)
    API->>RobotSvc: send_command(robot_id, command)
    RobotSvc->>RobotSvc: Check robot status (ONLINE?)
    RobotSvc->>Safety: validate_command(robot, command)
    Safety->>Safety: Check emergency_stop = false
    Safety->>Safety: Check battery > critical
    Safety->>Safety: Check obstacle distance > min
    Safety-->>RobotSvc: APPROVED
    RobotSvc->>MQTT: Publish robot/{id}/command
    MQTT->>Robot: Deliver command
    Robot->>Robot: Execute MOVE_FORWARD
    Robot->>MQTT: Publish robot/{id}/status
    MQTT->>API: Status update
    API->>UI: WebSocket: robot_status
    RobotSvc->>DB: Log command in robot_commands
```

---

## 4. Sequence Diagram — Telemetry Flow

```mermaid
sequenceDiagram
    participant Robot as Robot/Simulator
    participant MQTT as MQTT Broker
    participant MQTTSvc as MQTT Service
    participant TelSvc as Telemetry Service
    participant AnomalySvc as Anomaly Detection
    participant AlertSvc as Alert Service
    participant DB as PostgreSQL
    participant WS as WebSocket Manager
    participant UI as Dashboard

    loop Every 1 second
        Robot->>MQTT: Publish robot/{id}/telemetry
    end
    MQTT->>MQTTSvc: on_message callback
    MQTTSvc->>MQTTSvc: Parse + validate (Pydantic)
    MQTTSvc->>TelSvc: process_telemetry(data)
    TelSvc->>DB: INSERT INTO telemetry
    TelSvc->>AnomalySvc: check_anomalies(data)
    alt Anomaly found
        AnomalySvc-->>AlertSvc: create_alert(type, severity)
        AlertSvc->>DB: INSERT INTO alerts
        AlertSvc->>WS: broadcast("alert_created", alert)
    end
    TelSvc->>WS: broadcast("telemetry_update", data)
    WS->>UI: Push real-time update
```

---

## 5. Sequence Diagram — Alert Generation

```mermaid
sequenceDiagram
    participant Robot
    participant MQTT
    participant Backend
    participant Anomaly as Anomaly Detection
    participant DB as PostgreSQL
    participant WS as WebSocket
    participant UI as Dashboard
    actor Operator

    Robot->>MQTT: Telemetry { gas_level: 65 }
    MQTT->>Backend: Deliver message
    Backend->>Anomaly: check(gas_level=65, threshold=50)
    Anomaly-->>Backend: CRITICAL: HIGH_GAS
    Backend->>DB: INSERT alert (CRITICAL, HIGH_GAS)
    Backend->>WS: Broadcast alert_created
    Backend->>MQTT: Publish EMERGENCY_STOP
    WS->>UI: Display critical alert
    UI->>Operator: Alert notification
    Operator->>UI: Click "Acknowledge"
    UI->>Backend: POST /alerts/{id}/acknowledge
    Backend->>DB: UPDATE alert SET status=ACKNOWLEDGED
    Backend->>WS: Broadcast alert_updated
```

---

## 6. Sequence Diagram — AI Object Detection

```mermaid
sequenceDiagram
    participant Camera as Camera Provider
    participant AI as YOLO Detector
    participant Robot as Robot Controller
    participant MQTT as MQTT Broker
    participant Backend as FastAPI
    participant DB as PostgreSQL
    participant WS as WebSocket
    participant UI as Dashboard

    loop Every frame
        Camera->>AI: Capture frame
        AI->>AI: Run YOLO inference
        alt Object detected
            AI->>AI: Extract: type, confidence, bbox
            AI->>Robot: Detection event
            Robot->>MQTT: Publish robot/{id}/detection
            MQTT->>Backend: Deliver detection
            Backend->>DB: INSERT INTO detections
            Backend->>WS: Broadcast object_detected
            WS->>UI: Show detection overlay
        end
    end
```

---

## 7. Sequence Diagram — Autonomous Patrol

```mermaid
sequenceDiagram
    actor Operator
    participant UI as Dashboard
    participant API as FastAPI
    participant MQTT as MQTT Broker
    participant Robot as Robot/Simulator
    participant Nav as Navigation
    participant Sensor as Sensors
    participant AI as AI Detection

    Operator->>UI: Click "Start Patrol"
    UI->>API: POST /robots/{id}/patrol/start
    API->>API: Create PatrolSession
    API->>MQTT: Publish START_PATROL
    MQTT->>Robot: Start patrol command

    loop For each patrol point
        Robot->>Nav: Navigate to next point
        Nav->>Sensor: Read distance sensors
        alt Obstacle detected
            Sensor-->>Nav: distance < safe_min
            Nav->>Nav: Calculate avoidance path
            Nav->>Robot: Adjust heading
        end
        Robot->>Robot: Move toward point
        Robot->>MQTT: Telemetry update
        Robot->>AI: Run detection on camera frame
        alt Detection
            AI-->>Robot: Object found
            Robot->>MQTT: Publish detection
        end
        Robot->>MQTT: Point reached
    end
    Robot->>MQTT: Patrol complete
    MQTT->>API: Patrol completed
    API->>API: Update PatrolSession
    API->>UI: WebSocket: patrol_completed
```

---

## 8. Sequence Diagram — Emergency Stop

```mermaid
sequenceDiagram
    actor Operator
    participant UI as Dashboard
    participant API as FastAPI
    participant Safety as Safety Service
    participant MQTT as MQTT Broker
    participant Robot as Robot/Simulator
    participant DB as PostgreSQL

    Operator->>UI: Click EMERGENCY STOP
    UI->>API: POST /robots/{id}/emergency-stop
    API->>Safety: Set emergency_stop = true
    Safety->>DB: Log emergency event
    Safety->>DB: Create CRITICAL alert
    API->>MQTT: Publish EMERGENCY_STOP (QoS 2)
    MQTT->>Robot: Emergency stop command
    Robot->>Robot: Stop all motors immediately
    Robot->>Robot: Disable movement commands
    Robot->>MQTT: Status: EMERGENCY mode
    MQTT->>API: Status update
    API->>UI: WebSocket: robot_status (EMERGENCY)
    API->>UI: WebSocket: alert_created (CRITICAL)
```

---

## 9. Sequence Diagram — Network Failure & Recovery

```mermaid
sequenceDiagram
    participant Robot as Robot/Simulator
    participant MQTT as MQTT Broker
    participant Backend as FastAPI
    participant DB as PostgreSQL
    participant WS as WebSocket
    participant UI as Dashboard

    Note over Robot,MQTT: Normal operation
    Robot->>MQTT: Heartbeat (every 5s)
    MQTT->>Backend: Heartbeat received

    Note over Robot,MQTT: Network failure occurs
    Robot--xMQTT: Connection lost

    Robot->>Robot: Detect MQTT disconnect
    Robot->>Robot: Enter safe mode
    Robot->>Robot: Stop movement
    Robot->>Robot: Buffer telemetry locally (SQLite)

    Backend->>Backend: Heartbeat timeout (15s)
    Backend->>DB: UPDATE robot SET status=OFFLINE
    Backend->>DB: CREATE alert (COMMUNICATION_LOST)
    Backend->>WS: Broadcast robot_offline
    WS->>UI: Show robot offline

    Note over Robot,MQTT: Network recovered
    Robot->>MQTT: Reconnect
    Robot->>MQTT: Publish buffered telemetry
    MQTT->>Backend: Receive buffered data
    Backend->>DB: Store buffered telemetry
    Backend->>DB: UPDATE robot SET status=ONLINE
    Backend->>WS: Broadcast robot_online
    WS->>UI: Show robot online
```

---

## 10. Sequence Diagram — AI Natural-Language Command

```mermaid
sequenceDiagram
    actor User
    participant UI as Dashboard
    participant API as FastAPI
    participant Auth as Auth Service
    participant NLP as NL Interpreter
    participant Safety as Safety Check
    participant RobotSvc as Robot Service
    participant MQTT as MQTT Broker
    participant Robot as Robot

    User->>UI: Type "Start patrol in Lab B"
    UI->>API: POST /api/v1/ai/command<br/>{ text: "Start patrol in Lab B" }
    API->>Auth: Verify JWT + role
    Auth-->>API: User (role: OPERATOR)
    API->>NLP: interpret("Start patrol in Lab B")
    NLP->>NLP: Parse intent + entities
    NLP-->>API: { intent: "start_patrol", location: "Lab B", robot_id: "AURA-001" }
    API->>Safety: validate_command(start_patrol)
    Safety-->>API: APPROVED
    API->>RobotSvc: start_patrol(robot_id, route)
    RobotSvc->>MQTT: Publish START_PATROL
    MQTT->>Robot: Execute patrol
    API-->>UI: "Starting patrol in Lab B with AURA-001"
```

---

## 11. Sequence Diagram — Robot Reconnection

```mermaid
sequenceDiagram
    participant Robot as Robot
    participant LocalDB as Local SQLite
    participant MQTT as MQTT Broker
    participant Backend as FastAPI
    participant DB as PostgreSQL
    participant WS as WebSocket

    Note over Robot: Offline period ends
    Robot->>MQTT: MQTT Connect (clean_session=false)
    MQTT-->>Robot: CONNACK (success)
    Robot->>MQTT: Subscribe to robot/{id}/command
    Robot->>MQTT: Publish heartbeat
    MQTT->>Backend: Heartbeat received
    Backend->>DB: UPDATE robot status=ONLINE
    Backend->>WS: Broadcast robot_online

    Robot->>LocalDB: Read buffered telemetry
    loop For each buffered record
        Robot->>MQTT: Publish buffered telemetry
        MQTT->>Backend: Process telemetry
        Backend->>DB: Store telemetry
    end
    Robot->>LocalDB: Clear synced buffer
    Robot->>Robot: Resume normal operation
```

---

## 12. Component Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Dashboard<br/>Next.js + React]
    end

    subgraph "API Layer"
        GATEWAY[API Gateway<br/>FastAPI]
        WS_SVR[WebSocket Server]
    end

    subgraph "Service Layer"
        AUTH_SVC[Auth Service]
        ROBOT_SVC[Robot Service]
        TELEM_SVC[Telemetry Service]
        ALERT_SVC[Alert Service]
        NAV_SVC[Navigation Service]
        AI_SVC[AI Service]
        ANALYTICS_SVC[Analytics Service]
        MQTT_SVC[MQTT Client Service]
    end

    subgraph "AI Layer"
        YOLO[Object Detection<br/>YOLOv8]
        ANOMALY_DET[Anomaly Detection]
        NLP_INT[NL Interpreter]
    end

    subgraph "Data Layer"
        PG[(PostgreSQL)]
        MIGRATIONS[Alembic Migrations]
    end

    subgraph "IoT Layer"
        MOSQUITTO[Mosquitto<br/>MQTT Broker]
    end

    subgraph "Edge Layer"
        RPI[Raspberry Pi<br/>Controller]
        ESP[ESP32<br/>MCU]
        SIM[Robot Simulator]
    end

    WEB --> GATEWAY
    WEB --> WS_SVR

    GATEWAY --> AUTH_SVC
    GATEWAY --> ROBOT_SVC
    GATEWAY --> TELEM_SVC
    GATEWAY --> ALERT_SVC
    GATEWAY --> NAV_SVC
    GATEWAY --> AI_SVC
    GATEWAY --> ANALYTICS_SVC

    AI_SVC --> YOLO
    AI_SVC --> ANOMALY_DET
    AI_SVC --> NLP_INT

    AUTH_SVC --> PG
    ROBOT_SVC --> PG
    TELEM_SVC --> PG
    ALERT_SVC --> PG
    NAV_SVC --> PG
    ANALYTICS_SVC --> PG

    ROBOT_SVC --> MQTT_SVC
    TELEM_SVC --> MQTT_SVC
    MQTT_SVC --> MOSQUITTO

    MOSQUITTO --> RPI
    MOSQUITTO --> SIM
    RPI --> ESP

    MIGRATIONS --> PG
```

---

## 13. Deployment Diagram

```mermaid
graph TB
    subgraph "Development Machine / Cloud Server"
        subgraph "Docker Compose"
            subgraph "Frontend Container"
                NEXT[Next.js :3000]
            end
            subgraph "Backend Container"
                FASTAPI[FastAPI :8000<br/>+ MQTT Client<br/>+ WebSocket Server<br/>+ AI Services]
            end
            subgraph "Database Container"
                POSTGRES[(PostgreSQL :5432)]
            end
            subgraph "MQTT Container"
                MOSQ[Mosquitto<br/>:1883 TCP<br/>:9001 WebSocket]
            end
        end
    end

    subgraph "Edge Device (Optional)"
        subgraph "Raspberry Pi"
            RPI_APP[Python Controller<br/>+ Camera<br/>+ AI Inference]
        end
        subgraph "ESP32"
            ESP_FW[Firmware<br/>+ Sensors<br/>+ Motors]
        end
    end

    subgraph "Simulator (Alternative to Edge)"
        SIM_APP[Python Simulator<br/>Runs in Docker or locally]
    end

    BROWSER((Browser)) -->|HTTPS :3000| NEXT
    NEXT -->|HTTP :8000| FASTAPI
    BROWSER -->|WS :8000| FASTAPI
    FASTAPI -->|TCP :5432| POSTGRES
    FASTAPI -->|TCP :1883| MOSQ
    RPI_APP -->|MQTT :1883| MOSQ
    SIM_APP -->|MQTT :1883| MOSQ
    RPI_APP -->|Serial/I2C| ESP_FW
```
