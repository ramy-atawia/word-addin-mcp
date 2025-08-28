"""
Rate limiting middleware for Word Add-in MCP Project.
"""

import time
import asyncio
from typing import Dict, Optional, Tuple
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class RateLimitMiddleware:
    """Rate limiting middleware implementation."""
    
    def __init__(self):
        """Initialize rate limiting middleware."""
        self.requests_per_minute: Dict[str, list] = {}
        self.requests_per_hour: Dict[str, list] = {}
        self.lock = asyncio.Lock()
    
    async def __call__(self, request: Request, call_next):
        """Process request with rate limiting."""
        start_time = time.time()
        
        # Get client identifier (IP address or session ID)
        client_id = self._get_client_id(request)
        
        # Check rate limits
        if not await self._check_rate_limits(client_id):
            return await self._rate_limit_exceeded_response(client_id)
        
        # Process request
        response = await call_next(request)
        
        # Record request for rate limiting
        await self._record_request(client_id)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(settings.RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Limit-Hour"] = str(settings.RATE_LIMIT_PER_HOUR)
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            await self._get_remaining_requests(client_id, "minute")
        )
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            await self._get_remaining_requests(client_id, "hour")
        )
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Client identifier string
        """
        # Try to get session ID from headers
        session_id = request.headers.get("X-Session-ID")
        if session_id:
            return f"session:{session_id}"
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    async def _check_rate_limits(self, client_id: str) -> bool:
        """Check if client has exceeded rate limits.
        
        Args:
            client_id: Client identifier
            
        Returns:
            True if within limits, False if exceeded
        """
        async with self.lock:
            current_time = time.time()
            
            # Clean old entries
            await self._cleanup_old_requests(client_id, current_time)
            
            # Check minute limit
            minute_requests = self.requests_per_minute.get(client_id, [])
            if len(minute_requests) >= settings.RATE_LIMIT_PER_MINUTE:
                logger.warning(
                    "Rate limit exceeded (per minute)",
                    client_id=client_id,
                    limit=settings.RATE_LIMIT_PER_MINUTE
                )
                return False
            
            # Check hour limit
            hour_requests = self.requests_per_hour.get(client_id, [])
            if len(hour_requests) >= settings.RATE_LIMIT_PER_HOUR:
                logger.warning(
                    "Rate limit exceeded (per hour)",
                    client_id=client_id,
                    limit=settings.RATE_LIMIT_PER_HOUR
                )
                return False
            
            return True
    
    async def _record_request(self, client_id: str) -> None:
        """Record a request for rate limiting.
        
        Args:
            client_id: Client identifier
        """
        async with self.lock:
            current_time = time.time()
            
            # Record for minute tracking
            if client_id not in self.requests_per_minute:
                self.requests_per_minute[client_id] = []
            self.requests_per_minute[client_id].append(current_time)
            
            # Record for hour tracking
            if client_id not in self.requests_per_hour:
                self.requests_per_hour[client_id] = []
            self.requests_per_hour[client_id].append(current_time)
    
    async def _cleanup_old_requests(self, client_id: str, current_time: float) -> None:
        """Clean up old request timestamps.
        
        Args:
            client_id: Client identifier
            current_time: Current timestamp
        """
        # Clean minute requests (older than 60 seconds)
        if client_id in self.requests_per_minute:
            self.requests_per_minute[client_id] = [
                ts for ts in self.requests_per_minute[client_id]
                if current_time - ts < 60
            ]
        
        # Clean hour requests (older than 3600 seconds)
        if client_id in self.requests_per_hour:
            self.requests_per_hour[client_id] = [
                ts for ts in self.requests_per_hour[client_id]
                if current_time - ts < 3600
            ]
    
    async def _get_remaining_requests(self, client_id: str, period: str) -> int:
        """Get remaining requests for a client in a given period.
        
        Args:
            client_id: Client identifier
            period: Time period ("minute" or "hour")
            
        Returns:
            Number of remaining requests
        """
        if period == "minute":
            limit = settings.RATE_LIMIT_PER_MINUTE
            requests = self.requests_per_minute.get(client_id, [])
        elif period == "hour":
            limit = settings.RATE_LIMIT_PER_HOUR
            requests = self.requests_per_hour.get(client_id, [])
        else:
            return 0
        
        return max(0, limit - len(requests))
    
    async def _rate_limit_exceeded_response(self, client_id: str) -> JSONResponse:
        """Generate rate limit exceeded response.
        
        Args:
            client_id: Client identifier
            
        Returns:
            JSON response indicating rate limit exceeded
        """
        logger.warning(
            "Rate limit exceeded response sent",
            client_id=client_id
        )
        
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after": 60,  # Retry after 1 minute
                "limits": {
                    "per_minute": settings.RATE_LIMIT_PER_MINUTE,
                    "per_hour": settings.RATE_LIMIT_PER_HOUR
                }
            },
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit-Minute": str(settings.RATE_LIMIT_PER_MINUTE),
                "X-RateLimit-Limit-Hour": str(settings.RATE_LIMIT_PER_HOUR),
                "X-RateLimit-Remaining-Minute": "0",
                "X-RateLimit-Remaining-Hour": str(
                    await self._get_remaining_requests(client_id, "hour")
                )
            }
        )


class AdaptiveRateLimitMiddleware(RateLimitMiddleware):
    """Adaptive rate limiting middleware that adjusts limits based on client behavior."""
    
    def __init__(self):
        """Initialize adaptive rate limiting middleware."""
        super().__init__()
        self.client_behavior: Dict[str, Dict[str, any]] = {}
        self.trusted_clients: set = set()
    
    async def _check_rate_limits(self, client_id: str) -> bool:
        """Check rate limits with adaptive adjustments.
        
        Args:
            client_id: Client identifier
            
        Returns:
            True if within limits, False if exceeded
        """
        # Check if client is trusted
        if client_id in self.trusted_clients:
            return True
        
        # Get adaptive limits for this client
        adaptive_limits = await self._get_adaptive_limits(client_id)
        
        async with self.lock:
            current_time = time.time()
            
            # Clean old entries
            await self._cleanup_old_requests(client_id, current_time)
            
            # Check adaptive minute limit
            minute_requests = self.requests_per_minute.get(client_id, [])
            if len(minute_requests) >= adaptive_limits["per_minute"]:
                logger.warning(
                    "Adaptive rate limit exceeded (per minute)",
                    client_id=client_id,
                    limit=adaptive_limits["per_minute"],
                    base_limit=settings.RATE_LIMIT_PER_MINUTE
                )
                return False
            
            # Check adaptive hour limit
            hour_requests = self.requests_per_hour.get(client_id, [])
            if len(hour_requests) >= adaptive_limits["per_hour"]:
                logger.warning(
                    "Adaptive rate limit exceeded (per hour)",
                    client_id=client_id,
                    limit=adaptive_limits["per_hour"],
                    base_limit=settings.RATE_LIMIT_PER_HOUR
                )
                return False
            
            return True
    
    async def _get_adaptive_limits(self, client_id: str) -> Dict[str, int]:
        """Get adaptive rate limits for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dictionary with adaptive limits
        """
        if client_id not in self.client_behavior:
            self.client_behavior[client_id] = {
                "good_behavior_count": 0,
                "bad_behavior_count": 0,
                "last_violation": None
            }
        
        behavior = self.client_behavior[client_id]
        
        # Calculate adaptive limits based on behavior
        behavior_score = behavior["good_behavior_count"] - behavior["bad_behavior_count"]
        
        if behavior_score >= 10:  # Very good behavior
            multiplier = 2.0
        elif behavior_score >= 5:  # Good behavior
            multiplier = 1.5
        elif behavior_score >= 0:  # Neutral behavior
            multiplier = 1.0
        elif behavior_score >= -5:  # Bad behavior
            multiplier = 0.5
        else:  # Very bad behavior
            multiplier = 0.25
        
        return {
            "per_minute": int(settings.RATE_LIMIT_PER_MINUTE * multiplier),
            "per_hour": int(settings.RATE_LIMIT_PER_HOUR * multiplier)
        }
    
    async def _record_request(self, client_id: str) -> None:
        """Record a request and update behavior score.
        
        Args:
            client_id: Client identifier
        """
        await super()._record_request(client_id)
        
        # Update behavior score (successful request)
        if client_id in self.client_behavior:
            self.client_behavior[client_id]["good_behavior_count"] += 1
    
    async def _rate_limit_exceeded_response(self, client_id: str) -> JSONResponse:
        """Generate rate limit exceeded response and update behavior score.
        
        Args:
            client_id: Client identifier
            
        Returns:
            JSON response indicating rate limit exceeded
        """
        # Update behavior score (rate limit violation)
        if client_id in self.client_behavior:
            self.client_behavior[client_id]["bad_behavior_count"] += 1
            self.client_behavior[client_id]["last_violation"] = time.time()
        
        return await super()._rate_limit_exceeded_response(client_id)
