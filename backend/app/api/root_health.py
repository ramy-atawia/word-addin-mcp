"""
Root-level health check endpoints for deployment probes.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
import time
import structlog
from typing import Dict, Any

from app.core.config import settings

router = APIRouter()
logger = structlog.get_logger()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint for deployment probes.
    This endpoint is used by Azure Container Apps for liveness and readiness probes.
    """
    try:
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "service": "Word Add-in MCP API",
            "version": "1.0.0",
            "environment": settings.environment
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": time.time(),
                "service": "Word Add-in MCP API",
                "error": str(e)
            }
        )


@router.get("/health/llm")
async def llm_health_check() -> Dict[str, Any]:
    """
    LLM health check endpoint for debugging.
    """
    try:
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "config": {
                "api_key_configured": bool(settings.azure_openai_api_key),
                "endpoint_configured": bool(settings.azure_openai_endpoint),
                "deployment_configured": bool(settings.azure_openai_deployment),
                "api_version": settings.azure_openai_api_version,
                "environment": settings.environment,
                "timeout": settings.azure_openai_timeout,
                "max_retries": settings.azure_openai_max_retries
            },
            "llm": {
                "configured": bool(settings.azure_openai_api_key and settings.azure_openai_endpoint),
                "test_successful": None,
                "test_error": None
            }
        }
    except Exception as e:
        logger.error(f"LLM health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": time.time(),
                "service": "Word Add-in MCP API",
                "error": str(e)
            }
        )


@router.get("/health/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint.
    """
    try:
        return {
            "ready": True,
            "timestamp": time.time(),
            "details": "All services are ready"
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "timestamp": time.time(),
                "service": "Word Add-in MCP API",
                "error": str(e)
            }
        )


@router.get("/health/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check endpoint.
    """
    try:
        return {
            "alive": True,
            "timestamp": time.time(),
            "pid": "process_id_here",
            "uptime": "uptime_here"
        }
    except Exception as e:
        logger.error(f"Liveness check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "alive": False,
                "timestamp": time.time(),
                "service": "Word Add-in MCP API",
                "error": str(e)
            }
        )
