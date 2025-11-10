"""
Demo API - A portable Python FastAPI application for testing across platforms.

This application demonstrates best practices for cloud-native applications:
- Health checks and readiness probes
- Metrics and observability
- 12-factor app configuration
- Structured logging
- Graceful shutdown
"""

import os
import platform
import socket
import time
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

# Application metadata
APP_NAME = "demo-api"
APP_VERSION = "1.0.0"
START_TIME = time.time()

# Configuration from environment
PORT = int(os.getenv("PORT", "8000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Initialize FastAPI app
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="A portable demo API for testing across different platforms",
)

# Request counter for basic metrics
request_count = 0


@app.middleware("http")
async def add_metrics(request: Request, call_next):
    """Middleware to track request metrics."""
    global request_count
    request_count += 1

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with basic API information."""
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "running",
        "message": "Welcome to the Demo API!",
        "docs": "/docs",
        "health": "/health",
        "environment": ENVIRONMENT,
    }


@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint for liveness probes."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/ready")
async def ready() -> Dict[str, Any]:
    """Readiness check endpoint for readiness probes."""
    uptime_seconds = time.time() - START_TIME
    return {
        "status": "ready",
        "uptime_seconds": round(uptime_seconds, 2),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/metrics")
async def metrics() -> Dict[str, Any]:
    """Basic metrics endpoint."""
    uptime_seconds = time.time() - START_TIME
    return {
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "requests_total": request_count,
        "uptime_seconds": round(uptime_seconds, 2),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/info")
async def info() -> Dict[str, Any]:
    """
    System and environment information endpoint.

    Useful for verifying the app is running correctly on different platforms
    and for debugging environment-specific issues.
    """
    return {
        "application": {
            "name": APP_NAME,
            "version": APP_VERSION,
            "environment": ENVIRONMENT,
        },
        "system": {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        },
        "runtime": {
            "uptime_seconds": round(time.time() - START_TIME, 2),
            "start_time": datetime.fromtimestamp(START_TIME).isoformat(),
            "current_time": datetime.utcnow().isoformat(),
        },
        "environment_variables": {
            "PORT": PORT,
            "LOG_LEVEL": LOG_LEVEL,
            "ENVIRONMENT": ENVIRONMENT,
            # Add any custom env vars you want to expose (be careful with secrets!)
            "KUBERNETES_SERVICE_HOST": os.getenv("KUBERNETES_SERVICE_HOST", "not set"),
            "POD_NAME": os.getenv("POD_NAME", "not set"),
            "POD_NAMESPACE": os.getenv("POD_NAMESPACE", "not set"),
            "NODE_NAME": os.getenv("NODE_NAME", "not set"),
        },
    }


@app.get("/echo")
async def echo(request: Request) -> Dict[str, Any]:
    """
    Echo endpoint that returns information about the request.

    Useful for debugging reverse proxies, ingress controllers, and load balancers.
    """
    return {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "client": {
            "host": request.client.host if request.client else None,
            "port": request.client.port if request.client else None,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/version")
async def version() -> Dict[str, str]:
    """Version information endpoint."""
    return {
        "version": APP_VERSION,
        "app_name": APP_NAME,
    }


if __name__ == "__main__":
    print(f"Starting {APP_NAME} v{APP_VERSION}")
    print(f"Environment: {ENVIRONMENT}")
    print(f"Port: {PORT}")
    print(f"Log level: {LOG_LEVEL}")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        log_level=LOG_LEVEL,
        access_log=True,
    )
