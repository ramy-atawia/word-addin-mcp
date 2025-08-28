"""
Main FastAPI application entry point for Word Add-in MCP Project.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import structlog

from backend.app.core.config import settings
from backend.app.core.logging import setup_logging
from backend.app.api.v1 import chat, mcp, document, session, health, auth
from backend.app.middleware.security import (
    SecurityMiddleware, 
    InputValidationMiddleware, 
    RateLimitMiddleware
)
from backend.app.middleware.logging import LoggingMiddleware

# Setup logging
setup_logging()
logger = structlog.get_logger()

# Create FastAPI application
app = FastAPI(
    title="Word Add-in MCP API",
    description="Enterprise-grade API for Word Add-in with MCP integration",
    version="1.0.0",
    docs_url="/docs" if settings.ENABLE_SWAGGER else None,
    redoc_url="/redoc" if settings.ENABLE_SWAGGER else None,
    openapi_url="/openapi.json" if settings.ENABLE_SWAGGER else None,
)

# Add middleware
# Temporarily comment out custom middleware to fix startup issues
# app.add_middleware(LoggingMiddleware)
# app.add_middleware(SecurityMiddleware)
# app.add_middleware(InputValidationMiddleware)
# app.add_middleware(RateLimitMiddleware)

# Use FastAPI's built-in CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=settings.allowed_methods,
    allow_headers=settings.allowed_headers,
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Include API routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(mcp.router, prefix="/api/v1/mcp", tags=["MCP Tools"])
app.include_router(document.router, prefix="/api/v1/document", tags=["Document"])
app.include_router(session.router, prefix="/api/v1/session", tags=["Session"])

@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Starting Word Add-in MCP API", version="1.0.0")
    
    # Initialize database connection
    # await init_database()
    
    # Initialize MCP client connections
    # await init_mcp_clients()
    
    logger.info("Word Add-in MCP API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Shutting down Word Add-in MCP API")
    
    # Close database connections
    # await close_database()
    
    # Close MCP client connections
    # await close_mcp_clients()
    
    logger.info("Word Add-in MCP API shutdown complete")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "request_id": request.headers.get("x-request-id", "unknown")
        }
    )

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add process time header to response."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.middleware("http")
async def add_request_id_header(request: Request, call_next):
    """Add request ID header to response."""
    request_id = request.headers.get("x-request-id", f"req_{int(time.time() * 1000)}")
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.app.main:app",
        host=settings.FASTAPI_HOST,
        port=settings.FASTAPI_PORT,
        reload=settings.FASTAPI_RELOAD,
        log_level=settings.FASTAPI_LOG_LEVEL.lower(),
        access_log=True,
    )
