"""
Logging middleware for Word Add-in MCP Project.
"""

import time
import uuid
from typing import Optional
from fastapi import Request, Response
from fastapi.responses import StreamingResponse
import structlog

from backend.app.core.logging import log_request_info

logger = structlog.get_logger()


class LoggingMiddleware:
    """Logging middleware for request/response tracking."""
    
    def __init__(self):
        """Initialize logging middleware."""
        pass
    
    async def __call__(self, request: Request, call_next):
        """Process request with comprehensive logging."""
        start_time = time.time()
        
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.headers["X-Request-ID"] = request_id
        
        # Get client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log request start
        logger.info(
            "HTTP request started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
            client_ip=client_ip,
            user_agent=user_agent,
            headers=dict(request.headers)
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Log request completion
            log_request_info(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                execution_time=execution_time,
                user_agent=user_agent,
                ip_address=client_ip
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(execution_time)
            
            return response
            
        except Exception as e:
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Log error
            logger.error(
                "HTTP request failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error=str(e),
                execution_time=execution_time,
                client_ip=client_ip,
                user_agent=user_agent
            )
            
            # Re-raise the exception
            raise


class DetailedLoggingMiddleware(LoggingMiddleware):
    """Enhanced logging middleware with detailed request/response information."""
    
    def __init__(self, log_request_body: bool = False, log_response_body: bool = False):
        """Initialize detailed logging middleware.
        
        Args:
            log_request_body: Whether to log request body content
            log_response_body: Whether to log response body content
        """
        super().__init__()
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
    
    async def __call__(self, request: Request, call_next):
        """Process request with detailed logging."""
        start_time = time.time()
        
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.headers["X-Request-ID"] = request_id
        
        # Get client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log detailed request information
        request_info = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "headers": dict(request.headers),
            "cookies": dict(request.cookies)
        }
        
        # Log request body if enabled and content type is appropriate
        if self.log_request_body and self._should_log_body(request):
            try:
                body = await request.body()
                if body:
                    request_info["body"] = body.decode('utf-8', errors='replace')
            except Exception as e:
                request_info["body_error"] = str(e)
        
        logger.info("HTTP request started", **request_info)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Log detailed response information
            response_info = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "execution_time": execution_time,
                "response_headers": dict(response.headers),
                "client_ip": client_ip,
                "user_agent": user_agent
            }
            
            # Log response body if enabled and content type is appropriate
            if self.log_response_body and self._should_log_response_body(response):
                try:
                    if hasattr(response, 'body'):
                        response_info["response_body"] = response.body.decode('utf-8', errors='replace')
                    elif isinstance(response, StreamingResponse):
                        response_info["response_body"] = "[Streaming Response]"
                except Exception as e:
                    response_info["response_body_error"] = str(e)
            
            # Log request completion
            log_request_info(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                execution_time=execution_time,
                user_agent=user_agent,
                ip_address=client_ip
            )
            
            # Log detailed response
            logger.info("HTTP request completed", **response_info)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(execution_time)
            
            return response
            
        except Exception as e:
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Log detailed error information
            error_info = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "execution_time": execution_time,
                "client_ip": client_ip,
                "user_agent": user_agent
            }
            
            logger.error("HTTP request failed", **error_info, exc_info=True)
            
            # Re-raise the exception
            raise
    
    def _should_log_body(self, request: Request) -> bool:
        """Determine if request body should be logged.
        
        Args:
            request: FastAPI request object
            
        Returns:
            True if body should be logged
        """
        content_type = request.headers.get("content-type", "").lower()
        
        # Log text-based content types
        loggable_types = [
            "application/json",
            "application/xml",
            "text/plain",
            "text/html",
            "application/x-www-form-urlencoded"
        ]
        
        return any(ct in content_type for ct in loggable_types)
    
    def _should_log_response_body(self, response: Response) -> bool:
        """Determine if response body should be logged.
        
        Args:
            response: FastAPI response object
            
        Returns:
            True if body should be logged
        """
        content_type = response.headers.get("content-type", "").lower()
        
        # Log text-based content types
        loggable_types = [
            "application/json",
            "application/xml",
            "text/plain",
            "text/html"
        ]
        
        return any(ct in content_type for ct in loggable_types)


class PerformanceLoggingMiddleware(LoggingMiddleware):
    """Performance-focused logging middleware."""
    
    def __init__(self, slow_request_threshold: float = 1.0):
        """Initialize performance logging middleware.
        
        Args:
            slow_request_threshold: Threshold in seconds for slow request logging
        """
        super().__init__()
        self.slow_request_threshold = slow_request_threshold
    
    async def __call__(self, request: Request, call_next):
        """Process request with performance logging."""
        start_time = time.time()
        
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.headers["X-Request-ID"] = request_id
        
        # Get client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log request start
        logger.info(
            "HTTP request started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Log performance metrics
            if execution_time > self.slow_request_threshold:
                logger.warning(
                    "Slow request detected",
                    request_id=request_id,
                    method=request.method,
                    path=request.url.path,
                    execution_time=execution_time,
                    threshold=self.slow_request_threshold,
                    client_ip=client_ip,
                    user_agent=user_agent
                )
            
            # Log request completion
            log_request_info(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                execution_time=execution_time,
                user_agent=user_agent,
                ip_address=client_ip
            )
            
            # Add performance headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(execution_time)
            response.headers["X-Performance-Grade"] = self._get_performance_grade(execution_time)
            
            return response
            
        except Exception as e:
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Log error with performance context
            logger.error(
                "HTTP request failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error=str(e),
                execution_time=execution_time,
                client_ip=client_ip,
                user_agent=user_agent
            )
            
            # Re-raise the exception
            raise
    
    def _get_performance_grade(self, execution_time: float) -> str:
        """Get performance grade based on execution time.
        
        Args:
            execution_time: Request execution time in seconds
            
        Returns:
            Performance grade string
        """
        if execution_time < 0.1:
            return "A+"
        elif execution_time < 0.5:
            return "A"
        elif execution_time < 1.0:
            return "B"
        elif execution_time < 2.0:
            return "C"
        elif execution_time < 5.0:
            return "D"
        else:
            return "F"
