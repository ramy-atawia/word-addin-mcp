"""
Simple Auth0 JWT Middleware for testing
"""

import logging
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class SimpleAuthMiddleware(BaseHTTPMiddleware):
    """Simple middleware for testing."""
    
    def __init__(self, app, domain: str, audience: str, excluded_paths: list = None):
        super().__init__(app)
        self.domain = domain
        self.audience = audience
        self.excluded_paths = excluded_paths or []
        logger.info(f"Simple Auth Middleware initialized for domain: {domain}")
    
    async def dispatch(self, request: Request, call_next):
        """Simple middleware logic."""
        logger.info(f"Processing request: {request.method} {request.url.path}")
        
        # Check if path should be excluded
        if request.url.path in self.excluded_paths:
            logger.info(f"Excluded path: {request.url.path}")
            return await call_next(request)
        
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.warning(f"Missing Authorization header for: {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Authorization header required"}
            )
        
        if not auth_header.startswith("Bearer "):
            logger.warning(f"Invalid Authorization header format for: {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Bearer token required"}
            )
        
        token = auth_header[7:]
        logger.info(f"Token found: {token[:20]}...")
        
        # For now, just accept any token
        logger.info(f"Token accepted for: {request.url.path}")
        
        # Process the request
        response = await call_next(request)
        return response
