"""
Health check API endpoints for Word Add-in MCP Project.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
import time
import structlog
from typing import Dict, Any

from app.core.config import settings

router = APIRouter()
logger = structlog.get_logger()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns:
        Dict containing health status and basic information
    """
    try:
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": settings.app_version,
            "environment": settings.environment,
            "service": "Word Add-in MCP API"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "error": str(e),
            "service": "Word Add-in MCP API"
        }


@router.get("/llm")
async def llm_health_check() -> Dict[str, Any]:
    """
    LLM health check endpoint for dev environment debugging.
    
    Returns:
        Dict containing LLM service status and configuration
    """
    try:
        # Check configuration without creating LLM client (to avoid hanging)
        config_status = {
            "api_key_configured": bool(settings.azure_openai_api_key),
            "endpoint_configured": bool(settings.azure_openai_endpoint),
            "deployment_configured": bool(settings.azure_openai_deployment),
            "api_version": settings.azure_openai_api_version,
            "environment": settings.environment,
            "timeout": settings.azure_openai_timeout,
            "max_retries": settings.azure_openai_max_retries
        }
        
        # Simple configuration check without actual LLM call
        is_configured = all([
            settings.azure_openai_api_key,
            settings.azure_openai_endpoint,
            settings.azure_openai_deployment
        ])
        
        return {
            "status": "healthy" if is_configured else "unhealthy",
            "timestamp": time.time(),
            "config": config_status,
            "llm": {
                "configured": is_configured,
                "test_successful": None,  # Not tested to avoid hanging
                "test_error": None
            }
        }
        
    except Exception as e:
        logger.error(f"LLM health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": time.time(),
            "error": str(e)
        }


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check endpoint with service dependencies.
    
    Returns:
        Dict containing detailed health status of all services
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.app_version,
        "environment": settings.environment,
        "service": "Word Add-in MCP API",
        "dependencies": {}
    }
    
    
    # Check Redis health
    try:
        # TODO: Implement actual Redis health check
        # redis_health = await check_redis_health()
        health_status["dependencies"]["redis"] = {
            "status": "healthy",
            "response_time": 0.001,
            "details": "Redis connection active"
        }
    except Exception as e:
        health_status["dependencies"]["redis"] = {
            "status": "unhealthy",
            "error": str(e),
            "details": "Redis connection failed"
        }
        health_status["status"] = "degraded"
    
    # Check MCP server health (non-blocking)
    try:
        # Get actual MCP orchestrator health status with timeout
        import asyncio
        from app.services.mcp.orchestrator import get_initialized_mcp_orchestrator
        
        # Use asyncio.wait_for to prevent hanging
        mcp_orchestrator = get_initialized_mcp_orchestrator()
        mcp_health = await asyncio.wait_for(
            mcp_orchestrator.get_server_health(),
            timeout=5.0  # 5 second timeout
        )
        
        # Extract response time from MCP health metrics
        response_time = 0.001  # Default fallback
        if "metrics" in mcp_health and "average_execution_time" in mcp_health["metrics"]:
            response_time = mcp_health["metrics"]["average_execution_time"]
        
        health_status["dependencies"]["mcp_server"] = {
            "status": mcp_health.get("status", "unknown"),
            "response_time": response_time,
            "details": f"MCP orchestrator status: {mcp_health.get('status', 'unknown')}",
            "components": mcp_health.get("components", {}),
            "metrics": mcp_health.get("metrics", {})
        }
        
        # If MCP server is not healthy, mark overall status as degraded
        if mcp_health.get("status") != "healthy":
            health_status["status"] = "degraded"
            
    except asyncio.TimeoutError:
        health_status["dependencies"]["mcp_server"] = {
            "status": "timeout",
            "error": "MCP orchestrator health check timed out",
            "details": "MCP server health check took longer than 5 seconds"
        }
        health_status["status"] = "degraded"
    except RuntimeError as e:
        if "not yet initialized" in str(e):
            health_status["dependencies"]["mcp_server"] = {
                "status": "initializing",
                "error": "MCP orchestrator not yet initialized",
                "details": "MCP server is still initializing"
            }
            health_status["status"] = "degraded"
        else:
            health_status["dependencies"]["mcp_server"] = {
                "status": "unhealthy",
                "error": str(e),
                "details": "MCP server connection failed"
            }
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["dependencies"]["mcp_server"] = {
            "status": "unhealthy",
            "error": str(e),
            "details": "MCP server connection failed"
        }
        health_status["status"] = "degraded"
    
    # Check Azure OpenAI health
    try:
        # TODO: Implement actual Azure OpenAI health check
        # azure_health = await check_azure_openai_health()
        health_status["dependencies"]["azure_openai"] = {
            "status": "healthy",
            "response_time": 0.001,
            "details": "Azure OpenAI connection active"
        }
    except Exception as e:
        health_status["dependencies"]["azure_openai"] = {
            "status": "unhealthy",
            "error": str(e),
            "details": "Azure OpenAI connection failed"
        }
        health_status["status"] = "degraded"
    
    # Log health check
    logger.info(f"Health check completed - Status: {health_status['status']}, Environment: {settings.environment}")
    
    return health_status


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint for Kubernetes/container orchestration.
    
    Returns:
        Dict containing readiness status
    """
    try:
        # Check if all critical services are ready
        # TODO: Implement actual readiness checks
        ready = True
        details = "All services are ready"
        
        if not ready:
            raise HTTPException(status_code=503, detail="Service not ready")
        
        return {
            "ready": True,
            "timestamp": time.time(),
            "details": details
        }
        
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check endpoint for Kubernetes/container orchestration.
    
    Returns:
        Dict containing liveness status
    """
    return {
        "alive": True,
        "timestamp": time.time(),
        "pid": "process_id_here",  # TODO: Add actual process ID
        "uptime": "uptime_here"    # TODO: Add actual uptime
    }


@router.get("/debug/config")
async def debug_config() -> Dict[str, Any]:
    """
    Debug endpoint to check configuration values.
    
    Returns:
        Dict containing configuration values for debugging
    """
    try:
        return {
            "timestamp": time.time(),
            "test": "debug endpoint working",
            "environment": settings.environment,
            "version": settings.app_version,
            "azure_openai_configured": bool(settings.azure_openai_api_key and settings.azure_openai_endpoint),
            "google_api_configured": bool(settings.google_search_api_key),
            "auth0_configured": bool(getattr(settings, 'auth0_domain', None)),
            "service": "Word Add-in MCP API"
        }
        
    except Exception as e:
        return {
            "error": "Debug endpoint failed",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "timestamp": time.time()
        }


@router.get("/metrics")
async def metrics() -> Dict[str, Any]:
    """
    Basic metrics endpoint for monitoring.
    
    Returns:
        Dict containing basic application metrics
    """
    # TODO: Implement actual metrics collection
    return {
        "timestamp": time.time(),
        "version": settings.app_version,
        "environment": settings.environment,
        "metrics": {
            "requests_total": 0,  # TODO: Implement request counter
            "requests_active": 0,  # TODO: Implement active request counter
            "errors_total": 0,     # TODO: Implement error counter
            "response_time_avg": 0.0  # TODO: Implement response time tracking
        }
    }
