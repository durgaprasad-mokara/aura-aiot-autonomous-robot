# AURA — AIoT Autonomous Robotics Platform

<div align="center">

**Autonomous Unified Robotic Assistant**

*A full-stack AIoT robotics platform combining autonomous mobile robotics, IoT telemetry, computer vision, AI agents, real-time communication, cloud-ready infrastructure, and a web-based control center.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docker.com)

</div>

---

## Overview

AURA is a production-oriented AIoT autonomous robotics platform that enables:

- **Autonomous Patrol** — Robot navigates predefined waypoints, avoiding obstacles
- **Real-Time Telemetry** — Temperature, humidity, gas, battery, distance, speed streamed live
- **Computer Vision** — YOLO-based person/vehicle/object detection with bounding boxes
- **Anomaly Detection** — Threshold and ML-based sensor anomaly alerting
- **Natural-Language Control** — AI agent interprets commands like "Start patrol" or "Return home"
- **Emergency Safety** — Local safety logic operates even without cloud connectivity
- **Fleet Management** — Multi-robot support with role-based access control
- **Robot Simulation** — Full software simulator for development without hardware

## Architecture

```
PERCEIVE → UNDERSTAND → REASON → DECIDE → ACT → OBSERVE → LEARN → REPEAT
```

```
┌──────────────────────────────────────────────────────────┐
│                   Next.js Dashboard                       │
│              (React + TypeScript + Tailwind)               │
└───────────────────────┬──────────────────────────────────┘
                        │ REST API + WebSocket
┌───────────────────────▼──────────────────────────────────┐
│                   FastAPI Backend                          │
│    Auth │ Robots │ Telemetry │ Alerts │ AI │ Navigation    │
└──┬──────────┬──────────┬─────────────────────────────────┘
   │          │          │
   ▼          ▼          ▼
PostgreSQL  Mosquitto   AI Engine
   │        (MQTT)     (YOLO/CV)
   │          │          │
   └──────────┼──────────┘
              ▼
     Robot / Simulator
  (Raspberry Pi + ESP32)
  Sensors + Motors + Camera
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14, React, TypeScript, Tailwind CSS, Recharts, WebSocket |
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy, Alembic, Pydantic v2 |
| **Database** | PostgreSQL 16 |
| **IoT** | MQTT (Mosquitto), ESP32, Raspberry Pi |
| **AI/CV** | OpenCV, YOLOv8, NumPy, Scikit-learn |
| **Auth** | JWT (PyJWT), bcrypt, RBAC |
| **DevOps** | Docker, Docker Compose, GitHub Actions |
| **Testing** | Pytest, Playwright, MQTT integration tests |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Git

### Run with Docker

```bash
# Clone the repository
git clone https://github.com/your-org/aura-aiot.git
cd aura-aiot

# Copy environment variables
cp .env.example .env

# Start all services
docker compose up --build

# Access the dashboard
open http://localhost:3000

# Access API docs
open http://localhost:8000/docs
```

### Default Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@aura.local | admin123 |
| Operator | operator@aura.local | operator123 |
| Viewer | viewer@aura.local | viewer123 |

> ⚠️ **Change default credentials in production!**

### Run the Simulator

```bash
# The simulator starts automatically with docker compose
# Or run standalone:
cd simulator
python -m aura_simulator --robot-id AURA-001 --mode NORMAL
```

## Project Structure

```
aura-aiot-autonomous-robot/
├── frontend/                # Next.js web dashboard
│   ├── src/
│   │   ├── app/             # App router pages
│   │   ├── components/      # React components
│   │   ├── lib/             # API client, utilities
│   │   ├── hooks/           # Custom React hooks
│   │   └── types/           # TypeScript types
│   ├── Dockerfile
│   └── package.json
│
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/             # Route handlers
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   ├── ai/              # AI/CV services
│   │   └── core/            # Config, security, logging
│   ├── alembic/             # Database migrations
│   ├── tests/               # Backend tests
│   ├── Dockerfile
│   └── requirements.txt
│
├── robot/                   # Hardware code
│   ├── esp32/               # ESP32 firmware (C/C++)
│   └── raspberry_pi/        # Raspberry Pi code (Python)
│
├── simulator/               # Software robot simulator
│   ├── aura_simulator/
│   └── requirements.txt
│
├── ai/                      # AI models & training
│   └── models/
│
├── docs/                    # Documentation
│   ├── architecture/        # Architecture docs & UML
│   ├── api/                 # API documentation
│   ├── testing/             # Test documentation
│   └── deployment/          # Deployment guides
│
├── infrastructure/          # Infrastructure configs
│   └── mosquitto/           # MQTT broker config
│
├── docker-compose.yml
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

## User Roles

| Role | View | Control | Manage |
|------|------|---------|--------|
| **Admin** | ✅ All data | ✅ All robots | ✅ Users, config, system |
| **Operator** | ✅ All data | ✅ Assigned robots | ❌ |
| **Viewer** | ✅ All data | ❌ | ❌ |

## Robot Modes

| Mode | Description |
|------|-------------|
| **MANUAL** | Operator controls movement directly |
| **AUTONOMOUS** | Robot follows patrol waypoints, avoids obstacles |
| **RETURN_HOME** | Robot navigates to configured home position |
| **EMERGENCY** | All movement stopped, critical alert raised |

## API Endpoints

Full API documentation available at `/docs` (Swagger) and `/redoc` (ReDoc).

| Category | Endpoints |
|----------|-----------|
| Auth | `POST /api/v1/auth/login`, `/register`, `/refresh`, `/me` |
| Robots | `GET/POST /api/v1/robots`, `GET/PUT/DELETE /api/v1/robots/{id}` |
| Commands | `POST /api/v1/robots/{id}/command`, `/stop`, `/emergency-stop` |
| Telemetry | `GET /api/v1/robots/{id}/telemetry`, `/telemetry/latest` |
| Alerts | `GET /api/v1/alerts`, `POST /api/v1/alerts/{id}/acknowledge` |
| Analytics | `GET /api/v1/analytics/overview`, `/telemetry`, `/alerts` |
| WebSocket | `WS /ws/robots/{id}`, `WS /ws/dashboard` |

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and design |
| [SRS.md](docs/SRS.md) | Software Requirements Specification |
| [API.md](docs/api/API.md) | REST API documentation |
| [DATABASE.md](docs/DATABASE.md) | Database schema and design |
| [MQTT.md](docs/MQTT.md) | MQTT topics and message formats |
| [AI.md](docs/AI.md) | AI/CV pipeline documentation |
| [SECURITY.md](docs/SECURITY.md) | Security design and practices |
| [ROBOT_SETUP.md](docs/ROBOT_SETUP.md) | Hardware setup guide |
| [DEPLOYMENT.md](docs/deployment/DEPLOYMENT.md) | Deployment instructions |
| [TESTING.md](docs/testing/TESTING.md) | Testing strategy and guides |
| [USER_GUIDE.md](docs/USER_GUIDE.md) | End-user guide |
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Common issues and solutions |

## Future Roadmap

- ROS 2 integration
- LiDAR + SLAM navigation
- Multi-robot fleet management
- Mobile application (React Native)
- Predictive maintenance
- Digital twin
- Voice interface
- Edge AI optimization
- OTA firmware updates

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE).
