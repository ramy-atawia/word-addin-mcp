"""
Security Middleware for Word Add-in MCP Project.

This middleware provides additional security features including:
- Security headers
- CORS configuration
- Input validation and sanitization
- Request size limits
- Audit logging
"""

import time
import json
from typing import Callable, Dict, Any
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for enhanced application security."""
    
    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self.sensitive_paths = [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/change-password",
            "/api/v1/auth/reset-password"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security middleware."""
        start_time = time.time()
        
        # Add security headers
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://appsforoffice.microsoft.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.openai.com https://*.azure.com; "
            "frame-src 'self' https://appsforoffice.microsoft.com; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response.headers["Content-Security-Policy"] = csp_policy
        
        # HSTS header (only for HTTPS)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Process time
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Audit logging for sensitive operations
        if request.url.path in self.sensitive_paths:
            await self.audit_log(request, response, process_time)
        
        return response
    
    async def audit_log(self, request: Request, response: Response, process_time: float):
        """Log security-relevant events for audit purposes."""
        try:
            # Extract relevant information
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")
            method = request.method
            path = request.url.path
            status_code = response.status_code
            
            # Log security event
            logger.info(
                "Security audit log",
                client_ip=client_ip,
                user_agent=user_agent,
                method=method,
                path=path,
                status_code=status_code,
                process_time=process_time,
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for input validation and sanitization."""
    
    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self.max_request_size = 10 * 1024 * 1024  # 10MB
        self.blocked_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"onload=",
            r"onerror=",
            r"onclick=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through input validation middleware."""
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            return JSONResponse(
                status_code=413,
                content={"error": "Request too large", "max_size": self.max_request_size}
            )
        
        # Validate request body for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Read and validate request body
                body = await request.body()
                if body:
                    body_str = body.decode("utf-8")
                    
                    # Check for blocked patterns
                    for pattern in self.blocked_patterns:
                        import re
                        if re.search(pattern, body_str, re.IGNORECASE):
                            logger.warning(
                                "Blocked malicious request",
                                client_ip=request.client.host if request.client else "unknown",
                                pattern=pattern,
                                path=request.url.path
                            )
                            return JSONResponse(
                                status_code=400,
                                content={"error": "Invalid request content"}
                            )
                    
                    # Reconstruct request body for downstream processing
                    request._body = body
                    
            except Exception as e:
                logger.error(f"Input validation error: {e}")
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid request content"}
                )
        
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enhanced rate limiting middleware with IP-based tracking."""
    
    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        self.default_limits = {
            "auth": {"requests": 10, "window": 300},  # 10 requests per 5 minutes
            "api": {"requests": 100, "window": 60},   # 100 requests per minute
            "default": {"requests": 50, "window": 60}  # 50 requests per minute
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through rate limiting middleware."""
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        
        # Determine rate limit category
        if path.startswith("/api/v1/auth"):
            category = "auth"
        elif path.startswith("/api/v1/"):
            category = "api"
        else:
            category = "default"
        
        # Check rate limit
        if not self.check_rate_limit(client_ip, category):
            logger.warning(
                "Rate limit exceeded",
                client_ip=client_ip,
                category=category,
                path=path
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": self.get_retry_after(client_ip, category)
                }
            )
        
        return await call_next(request)
    
    def check_rate_limit(self, client_ip: str, category: str) -> bool:
        """Check if request is within rate limit."""
        import time
        
        now = time.time()
        limit_config = self.default_limits[category]
        
        if client_ip not in self.rate_limits:
            self.rate_limits[client_ip] = {}
        
        if category not in self.rate_limits[client_ip]:
            self.rate_limits[client_ip][category] = {
                "requests": [],
                "window_start": now
            }
        
        # Clean old requests outside window
        window_start = now - limit_config["window"]
        self.rate_limits[client_ip][category]["requests"] = [
            req_time for req_time in self.rate_limits[client_ip][category]["requests"]
            if req_time > window_start
        ]
        
        # Check if under limit
        if len(self.rate_limits[client_ip][category]["requests"]) < limit_config["requests"]:
            self.rate_limits[client_ip][category]["requests"].append(now)
            return True
        
        return False
    
    def get_retry_after(self, client_ip: str, category: str) -> int:
        """Get retry after time in seconds."""
        import time
        
        now = time.time()
        limit_config = self.default_limits[category]
        
        if client_ip in self.rate_limits and category in self.rate_limits[client_ip]:
            oldest_request = min(self.rate_limits[client_ip][category]["requests"])
            return int(limit_config["window"] - (now - oldest_request))
        
        return limit_config["window"]


class CORSMiddleware(BaseHTTPMiddleware):
    """Enhanced CORS middleware with security considerations."""
    
    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self.allowed_origins = settings.ALLOWED_ORIGINS
        self.allowed_methods = settings.ALLOWED_METHODS
        self.allowed_headers = settings.ALLOWED_HEADERS
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through CORS middleware."""
        response = await call_next(request)
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            origin = request.headers.get("origin")
            if origin in self.allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
                response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Max-Age"] = "86400"  # 24 hours
        
        # Handle actual requests
        else:
            origin = request.headers.get("origin")
            if origin in self.allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response


# Security utilities
def sanitize_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Sanitize HTTP headers for security."""
    sanitized = {}
    blocked_headers = [
        "x-forwarded-for",
        "x-real-ip",
        "x-forwarded-host",
        "x-forwarded-proto"
    ]
    
    for key, value in headers.items():
        if key.lower() not in blocked_headers:
            # Basic sanitization
            sanitized_value = value.replace("<", "&lt;").replace(">", "&gt;")
            sanitized[key] = sanitized_value
    
    return sanitized


def validate_content_type(content_type: str) -> bool:
    """Validate content type for security."""
    allowed_types = [
        "application/json",
        "application/x-www-form-urlencoded",
        "multipart/form-data",
        "text/plain"
    ]
    
    return any(allowed_type in content_type for allowed_type in allowed_types)


def log_security_event(event_type: str, details: Dict[str, Any]):
    """Log security events for monitoring."""
    logger.warning(
        f"Security event: {event_type}",
        event_type=event_type,
        details=details,
        timestamp=time.time()
    )
