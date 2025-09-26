"""
Main FastAPI application for Word Add-in MCP Project.

This module provides the main FastAPI application with all API routes
and middleware configured for MCP compliance.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
from contextlib import asynccontextmanager

import os
import asyncio
from .core.config import settings
from .core.logging import setup_logging
from .middleware.auth0_jwt_middleware import Auth0JWTMiddleware
from .api.v1 import mcp, external_mcp, session, health, async_chat

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


async def _wait_for_internal_mcp_server():
    """Wait for internal MCP server to be ready."""
    import aiohttp
    import asyncio
    
    max_retries = 30
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8001/health") as response:
                    if response.status == 200:
                        logger.info("Internal MCP server is ready")
                        return
        except Exception as e:
            logger.debug(f"Waiting for internal MCP server... (attempt {attempt + 1}/{max_retries})")
            await asyncio.sleep(retry_delay)
    
    raise RuntimeError("Internal MCP server failed to start within timeout")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Word Add-in MCP Backend")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Wait for internal MCP server to be ready (can be skipped in APP_STARTER_MODE
    # or if INTERNAL_MCP_FAIL_OPEN is enabled to avoid aborting startup in prod)
    skip_wait = getattr(settings, "app_starter_mode", False) or os.getenv("INTERNAL_MCP_FAIL_OPEN", "false").lower() == "true"
    if skip_wait:
        logger.warning("Skipping internal MCP wait due to APP_STARTER_MODE or INTERNAL_MCP_FAIL_OPEN")
    else:
        try:
            await _wait_for_internal_mcp_server()
        except Exception as e:
            # Fail-open behavior: log a warning and continue so App Service can start.
            # This avoids container restart loops while still reporting degraded state.
            logger.warning(f"Internal MCP server did not become ready: {str(e)}. Continuing startup in degraded mode.")
    
    # Initialize MCP Orchestrator
    try:
        from .services.mcp.orchestrator import get_mcp_orchestrator
        mcp_orchestrator = get_mcp_orchestrator()
        await mcp_orchestrator.initialize()
        logger.info("MCP Orchestrator initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MCP Orchestrator: {str(e)}")
        raise
    
    # Initialize Job Queue
    try:
        from .services.job_queue import job_queue
        # Start job queue worker in background
        asyncio.create_task(job_queue.start_worker())
        logger.info("Job queue worker started")
    except Exception as e:
        logger.error(f"Failed to start job queue worker: {str(e)}")
        # Don't raise - job queue is optional for basic functionality
    
    yield
    
    # Shutdown
    logger.info("Shutting down Word Add-in MCP Backend")
    
    # Stop Job Queue Worker
    try:
        from .services.job_queue import job_queue
        await job_queue.stop_worker()
        logger.info("Job queue worker stopped")
    except Exception as e:
        logger.error(f"Failed to stop job queue worker: {str(e)}")
    
    # Cleanup MCP Orchestrator
    try:
        from .services.mcp.orchestrator import get_mcp_orchestrator
        mcp_orchestrator = get_mcp_orchestrator()
        
        # Stop internal MCP server
        if mcp_orchestrator.internal_mcp_server:
            await mcp_orchestrator.internal_mcp_server.stop()
            logger.info("Internal MCP server stopped")
        
        # Get external servers and disconnect them
        external_servers = await mcp_orchestrator.get_external_servers()
        for server in external_servers:
            # Note: Server cleanup is handled by the registry
            pass
        logger.info("MCP Orchestrator cleanup completed")
    except Exception as e:
        logger.error(f"Error during MCP Orchestrator cleanup: {str(e)}")


# Create FastAPI application
app = FastAPI(
    title="Word Add-in MCP Backend",
    description="Backend service for Word Add-in MCP integration",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# OpenAPI documentation available at /docs

# IMPORTANT: Middleware order matters! They execute in REVERSE order of addition.
# Last added = First to execute (outermost layer)

# Add request logging middleware (outermost - executes first)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = time.time()
    
    # Log request
    logger.info(
        f"Incoming request - Method: {request.method}, URL: {request.url}, "
        f"Client IP: {request.client.host if request.client else 'unknown'}, "
        f"User Agent: {request.headers.get('user-agent', 'unknown')}"
    )
    
    try:
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Request completed - Method: {request.method}, URL: {request.url}, "
            f"Status: {response.status_code}, Process Time: {process_time:.3f}s"
        )
        
        return response
        
    except Exception as e:
        # Log error
        process_time = time.time() - start_time
        logger.error(
            f"Request failed - Method: {request.method}, URL: {request.url}, "
            f"Error: {str(e)}, Process Time: {process_time:.3f}s"
        )
        raise


# Add process time header middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add process time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Use standard CORSMiddleware to handle preflight and CORS headers
# We'll add it after other middlewares so it runs as the outermost layer


# Add Auth0 JWT Middleware (this will execute AFTER the CORS middleware above)
if settings.auth0_enabled:
    logger.info(f"Enabling Auth0 JWT middleware for domain: {settings.auth0_domain}")
    logger.info(f"Auth0 excluded paths: {settings.auth0_excluded_paths}")
    
    app.add_middleware(
        Auth0JWTMiddleware, 
        domain=settings.auth0_domain,
        audience=settings.auth0_audience,
        excluded_paths=settings.auth0_excluded_paths,
        fallback_mode=True
    )
else:
    logger.warning("Auth0 JWT middleware is DISABLED - all endpoints are publicly accessible!")


# Add trusted host middleware (this will execute LAST, closest to the application)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts
)

# Add CORSMiddleware as the outermost middleware so preflight requests are handled
# before authentication middleware runs. Read allowed_origins from settings for flexibility.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins or ["https://novitai-word-mcp-frontend-dev.azurewebsites.net"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Authenticated-User-ID"]
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(
        f"Unhandled exception - Method: {request.method}, URL: {request.url}, "
        f"Error: {str(exc)}, Error Type: {type(exc).__name__}"
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "error_type": type(exc).__name__,
            "timestamp": time.time()
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP exception handler."""
    logger.warning(
        f"HTTP exception - Method: {request.method}, URL: {request.url}, "
        f"Status: {exc.status_code}, Detail: {exc.detail}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": time.time()
        }
    )


# Include API routers
app.include_router(
    mcp.router,
    prefix="/api/v1",
    tags=["mcp"]
)

app.include_router(
    external_mcp.router,
    prefix="/api/v1",
    tags=["external-mcp"]
)

app.include_router(
    session.router,
    prefix="/api/v1",
    tags=["session"]
)

app.include_router(
    health.router,
    prefix="/api/v1",
    tags=["health"]
)

app.include_router(
    async_chat.router,
    prefix="/api/v1/async/chat",
    tags=["async-chat"]
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Word Add-in MCP Backend",
        "version": "1.0.0",
        "status": "running",
        "mcp_compliance": "2025-06-18",
        "timestamp": time.time()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check MCP Orchestrator status
        from .services.mcp.orchestrator import mcp_orchestrator
        orchestrator_status = await mcp_orchestrator.get_server_health()
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "mcp_orchestrator": orchestrator_status,
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )


@app.get("/info")
async def info():
    """Application information endpoint."""
    return {
        "name": "Word Add-in MCP Backend",
        "version": "1.0.0",
        "description": "Backend service for Word Add-in MCP integration",
        "environment": settings.environment,
        "debug": settings.debug,
        "mcp_compliance": "2025-06-18",
        "features": [
            "MCP Protocol Compliance",
            "External MCP Server Integration",
            "Tool Discovery and Execution",
            "Document Analysis",
            "Chat Integration",
            "Session Management"
        ],
        "timestamp": time.time()
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        reload=settings.debug,
        log_level="info"
    )