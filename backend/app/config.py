"""
AURA Backend — Application Configuration
==========================================
Centralized configuration using Pydantic Settings.
All config loaded from environment variables / .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "AURA"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Backend Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    BACKEND_WORKERS: int = 1

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # Database
    POSTGRES_USER: str = "aura"
    POSTGRES_PASSWORD: str = "changeme_db_password"
    POSTGRES_DB: str = "aura_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql+asyncpg://aura:changeme_db_password@localhost:5432/aura_db"

    @property
    def database_url_sync(self) -> str:
        """Synchronous database URL for Alembic migrations."""
        return self.DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2")

    # JWT Authentication
    JWT_SECRET: str = "changeme_jwt_secret_min_32_chars_long"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # MQTT
    MQTT_HOST: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_WS_PORT: int = 9001
    MQTT_USERNAME: str = "aura_mqtt"
    MQTT_PASSWORD: str = "changeme_mqtt_password"
    MQTT_CLIENT_ID: str = "aura-backend"

    # AI
    AI_MODEL_PATH: str = "./ai/models"
    AI_CONFIDENCE_THRESHOLD: float = 0.5
    AI_API_KEY: str = ""

    # Camera
    CAMERA_URL: str = ""
    CAMERA_MOCK: bool = True

    # Robot Defaults
    ROBOT_HEARTBEAT_INTERVAL: int = 5
    ROBOT_HEARTBEAT_TIMEOUT: int = 15
    ROBOT_MIN_SAFE_DISTANCE: int = 20
    ROBOT_CRITICAL_BATTERY: int = 10
    ROBOT_LOW_BATTERY: int = 20
    ROBOT_CRITICAL_GAS_LEVEL: int = 50
    ROBOT_CRITICAL_TEMPERATURE: int = 60

    # Simulator
    SIMULATOR_ENABLED: bool = True
    SIMULATOR_ROBOT_ID: str = "AURA-001"
    SIMULATOR_MODE: str = "NORMAL"
    SIMULATOR_TICK_RATE: float = 1.0

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance — loaded once at startup."""
    return Settings()
