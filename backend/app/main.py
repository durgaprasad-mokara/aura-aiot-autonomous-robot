"""
AURA Backend — Main Application
==================================
FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import engine, close_db
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import (
    AuraBaseException, aura_exception_handler,
    validation_exception_handler, generic_exception_handler
)
from fastapi.exceptions import RequestValidationError

# API Routers
from app.api.auth import router as auth_router
from app.api.robots import router as robots_router
from app.api.commands import router as commands_router
from app.api.alerts import router as alerts_router
from app.api.websocket import router as ws_router

# Setup structured logging before anything else
setup_logging()
logger = get_logger("aura_main")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events (startup/shutdown)."""
    logger.info("aura_backend_starting", env=settings.APP_ENV, debug=settings.DEBUG)
    
    # Initialize MQTT client
    from app.services.mqtt_service import mqtt_client
    mqtt_client.start()
    
    yield
    
    logger.info("aura_backend_shutting_down")
    mqtt_client.stop()
    await close_db()


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AIoT Autonomous Robotics Platform API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(AuraBaseException, aura_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# ========================
# Include Routers
# ========================
api_prefix = "/api/v1"
app.include_router(auth_router, prefix=api_prefix)
app.include_router(robots_router, prefix=api_prefix)
# Commands router is nested under /robots in the router definition
app.include_router(commands_router, prefix=api_prefix)
app.include_router(alerts_router, prefix=api_prefix)
app.include_router(ws_router)


# ========================
# Health Checks
# ========================
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic service health check."""
    return {"status": "ok", "service": settings.APP_NAME}


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Deep health check (DB connection, MQTT connection)."""
    # Simply check DB connection for now
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        db_status = "ok"
    except Exception as e:
        logger.error("db_health_check_failed", error=str(e))
        db_status = "error"

    status_code = 200 if db_status == "ok" else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if db_status == "ok" else "not_ready",
            "database": db_status
        }
    )
