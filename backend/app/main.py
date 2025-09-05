"""
Main FastAPI application for Word Add-in MCP Project.

This module provides the main FastAPI application with all API routes
and middleware configured for MCP compliance.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
import time
from contextlib import asynccontextmanager

from .core.config import settings
from .core.logging import setup_logging
from .api.v1 import mcp, external_mcp, document, session, auth, health, legal_tools

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Word Add-in MCP Backend")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Initialize MCP Orchestrator
    try:
        from .services.mcp.orchestrator import get_mcp_orchestrator
        mcp_orchestrator = get_mcp_orchestrator()
        await mcp_orchestrator.initialize()
        logger.info("MCP Orchestrator initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MCP Orchestrator: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Word Add-in MCP Backend")
    
    # Cleanup MCP Orchestrator
    try:
        # Get external servers and disconnect them
        from .services.mcp.orchestrator import get_mcp_orchestrator
        mcp_orchestrator = get_mcp_orchestrator()
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
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add process time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


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
    document.router,
    prefix="/api/v1",
    tags=["document"]
)

app.include_router(
    session.router,
    prefix="/api/v1",
    tags=["session"]
)

app.include_router(
    auth.router,
    prefix="/api/v1",
    tags=["auth"]
)

app.include_router(
    health.router,
    prefix="/api/v1",
    tags=["health"]
)

app.include_router(
    legal_tools.router,
    prefix="/api/v1",
    tags=["legal-tools"]
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
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
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
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
