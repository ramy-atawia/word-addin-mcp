"""
Unit tests for security middleware components.
"""

import pytest
import time
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.middleware.security import (
    SecurityMiddleware, InputValidationMiddleware, 
    RateLimitMiddleware, CORSMiddleware,
    sanitize_headers, validate_content_type, log_security_event
)
from app.core.config import settings


class TestSecurityMiddleware:
    """Test cases for SecurityMiddleware class."""
    
    @pytest.fixture
    def security_middleware(self):
        """Create a SecurityMiddleware instance for testing."""
        app = Mock()
        return SecurityMiddleware(app)
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request for testing."""
        request = Mock(spec=Request)
        request.url.scheme = "http"
        request.url.path = "/api/v1/auth/login"
        request.client.host = "192.168.1.1"
        request.headers = {"user-agent": "test-agent"}
        request.method = "POST"
        return request
    
    @pytest.fixture
    def mock_response(self):
        """Create a mock response for testing."""
        response = Mock(spec=Response)
        response.status_code = 200
        response.headers = {}
        return response
    
    async def test_security_headers_added(self, security_middleware, mock_request, mock_response):
        """Test that security headers are added to responses."""
        # Mock call_next to return our response
        async def mock_call_next(request):
            return mock_response
        
        # Process request through middleware
        result = await security_middleware.dispatch(mock_request, mock_call_next)
        
        # Check security headers
        assert result.headers["X-Content-Type-Options"] == "nosniff"
        assert result.headers["X-Frame-Options"] == "DENY"
        assert result.headers["X-XSS-Protection"] == "1; mode=block"
        assert result.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert result.headers["Permissions-Policy"] == "geolocation=(), microphone=(), camera=()"
        assert "Content-Security-Policy" in result.headers
        assert "X-Process-Time" in result.headers
    
    async def test_csp_policy_content(self, security_middleware, mock_request, mock_response):
        """Test Content Security Policy content."""
        async def mock_call_next(request):
            return mock_response
        
        result = await security_middleware.dispatch(mock_request, mock_call_next)
        
        csp = result.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "style-src 'self'" in csp
        assert "object-src 'none'" in csp
        assert "base-uri 'self'" in csp
    
    async def test_hsts_header_https(self, security_middleware, mock_request, mock_response):
        """Test HSTS header is added for HTTPS requests."""
        mock_request.url.scheme = "https"
        
        async def mock_call_next(request):
            return mock_response
        
        result = await security_middleware.dispatch(mock_request, mock_call_next)
        
        assert "Strict-Transport-Security" in result.headers
        assert "max-age=31536000" in result.headers["Strict-Transport-Security"]
    
    async def test_hsts_header_http(self, security_middleware, mock_request, mock_response):
        """Test HSTS header is not added for HTTP requests."""
        mock_request.url.scheme = "http"
        
        async def mock_call_next(request):
            return mock_response
        
        result = await security_middleware.dispatch(mock_request, mock_call_next)
        
        assert "Strict-Transport-Security" not in result.headers
    
    async def test_audit_logging_sensitive_paths(self, security_middleware, mock_request, mock_response):
        """Test audit logging for sensitive paths."""
        with patch.object(security_middleware, 'audit_log') as mock_audit:
            async def mock_call_next(request):
                return mock_response
            
            await security_middleware.dispatch(mock_request, mock_call_next)
            
            mock_audit.assert_called_once()
    
    async def test_audit_logging_non_sensitive_paths(self, security_middleware, mock_request, mock_response):
        """Test audit logging is not called for non-sensitive paths."""
        mock_request.url.path = "/api/v1/health"
        
        with patch.object(security_middleware, 'audit_log') as mock_audit:
            async def mock_call_next(request):
                return mock_response
            
            await security_middleware.dispatch(mock_request, mock_call_next)
            
            mock_audit.assert_not_called()
    
    async def test_audit_log_content(self, security_middleware, mock_request, mock_response):
        """Test audit log content."""
        with patch('app.middleware.security.logger') as mock_logger:
            async def mock_call_next(request):
                return mock_response
            
            await security_middleware.dispatch(mock_request, mock_call_next)
            
            # Check that logger.info was called with security audit log
            mock_logger.info.assert_called()
            call_args = mock_logger.info.call_args[1]
            assert call_args["client_ip"] == "192.168.1.1"
            assert call_args["user_agent"] == "test-agent"
            assert call_args["method"] == "POST"
            assert call_args["path"] == "/api/v1/auth/login"
            assert call_args["status_code"] == 200


class TestInputValidationMiddleware:
    """Test cases for InputValidationMiddleware class."""
    
    @pytest.fixture
    def input_validation_middleware(self):
        """Create an InputValidationMiddleware instance for testing."""
        app = Mock()
        return InputValidationMiddleware(app)
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request for testing."""
        request = Mock(spec=Request)
        request.method = "POST"
        request.headers = {"content-length": "100"}
        request.client.host = "192.168.1.1"
        request.url.path = "/api/v1/test"
        return request
    
    async def test_request_size_limit_exceeded(self, input_validation_middleware, mock_request):
        """Test that large requests are rejected."""
        mock_request.headers["content-length"] = str(11 * 1024 * 1024)  # 11MB
        
        async def mock_call_next(request):
            return Mock(spec=Response)
        
        result = await input_validation_middleware.dispatch(mock_request, mock_call_next)
        
        assert result.status_code == 413
        assert "Request too large" in result.body.decode()
    
    async def test_malicious_content_blocked(self, input_validation_middleware, mock_request):
        """Test that malicious content is blocked."""
        malicious_body = b"<script>alert('xss')</script>"
        mock_request._body = malicious_body
        
        async def mock_call_next(request):
            return Mock(spec=Response)
        
        result = await input_validation_middleware.dispatch(mock_request, mock_call_next)
        
        assert result.status_code == 400
        assert "Invalid request content" in result.body.decode()
    
    async def test_safe_content_allowed(self, input_validation_middleware, mock_request):
        """Test that safe content is allowed through."""
        safe_body = b"Hello, World!"
        mock_request._body = safe_body
        
        mock_response = Mock(spec=Response)
        async def mock_call_next(request):
            return mock_response
        
        result = await input_validation_middleware.dispatch(mock_request, mock_call_next)
        
        assert result == mock_response
    
    async def test_get_request_bypassed(self, input_validation_middleware, mock_request):
        """Test that GET requests bypass validation."""
        mock_request.method = "GET"
        
        mock_response = Mock(spec=Response)
        async def mock_call_next(request):
            return mock_response
        
        result = await input_validation_middleware.dispatch(mock_request, mock_call_next)
        
        assert result == mock_response
    
    async def test_multiple_malicious_patterns(self, input_validation_middleware, mock_request):
        """Test multiple malicious patterns are blocked."""
        malicious_patterns = [
            b"<script>alert('xss')</script>",
            b"javascript:alert('xss')",
            b"onload=alert('xss')",
            b"<iframe src='malicious.com'></iframe>",
            b"<object data='malicious.com'></object>"
        ]
        
        for pattern in malicious_patterns:
            mock_request._body = pattern
            
            async def mock_call_next(request):
                return Mock(spec=Response)
            
            result = await input_validation_middleware.dispatch(mock_request, mock_call_next)
            
            assert result.status_code == 400
            assert "Invalid request content" in result.body.decode()


class TestRateLimitMiddleware:
    """Test cases for RateLimitMiddleware class."""
    
    @pytest.fixture
    def rate_limit_middleware(self):
        """Create a RateLimitMiddleware instance for testing."""
        app = Mock()
        return RateLimitMiddleware(app)
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request for testing."""
        request = Mock(spec=Request)
        request.client.host = "192.168.1.1"
        request.url.path = "/api/v1/test"
        return request
    
    def test_rate_limit_checking(self, rate_limit_middleware, mock_request):
        """Test rate limit checking functionality."""
        client_ip = "192.168.1.1"
        category = "api"
        
        # First 100 requests should be allowed
        for i in range(100):
            assert rate_limit_middleware.check_rate_limit(client_ip, category)
        
        # 101st request should be blocked
        assert not rate_limit_middleware.check_rate_limit(client_ip, category)
    
    def test_rate_limit_categories(self, rate_limit_middleware, mock_request):
        """Test different rate limit categories."""
        client_ip = "192.168.1.1"
        
        # Auth category: 10 requests per 5 minutes
        for i in range(10):
            assert rate_limit_middleware.check_rate_limit(client_ip, "auth")
        
        assert not rate_limit_middleware.check_rate_limit(client_ip, "auth")
        
        # Default category: 50 requests per minute
        for i in range(50):
            assert rate_limit_middleware.check_rate_limit(client_ip, "default")
        
        assert not rate_limit_middleware.check_rate_limit(client_ip, "default")
    
    def test_rate_limit_cleanup(self, rate_limit_middleware, mock_request):
        """Test rate limit cleanup of old requests."""
        client_ip = "192.168.1.1"
        category = "api"
        
        # Add some old requests
        rate_limit_middleware.rate_limits[client_ip] = {
            category: {
                "requests": [time.time() - 120],  # 2 minutes old
                "window_start": time.time() - 120
            }
        }
        
        # Check rate limit (should clean up old requests)
        assert rate_limit_middleware.check_rate_limit(client_ip, category)
        assert len(rate_limit_middleware.rate_limits[client_ip][category]["requests"]) == 1
    
    async def test_rate_limit_middleware_dispatch(self, rate_limit_middleware, mock_request):
        """Test rate limit middleware dispatch."""
        # Set up rate limit exceeded
        client_ip = "192.168.1.1"
        category = "api"
        
        # Exceed rate limit
        for i in range(100):
            rate_limit_middleware.check_rate_limit(client_ip, category)
        
        async def mock_call_next(request):
            return Mock(spec=Response)
        
        result = await rate_limit_middleware.dispatch(mock_request, mock_call_next)
        
        assert result.status_code == 429
        assert "Rate limit exceeded" in result.body.decode()
    
    def test_retry_after_calculation(self, rate_limit_middleware, mock_request):
        """Test retry after time calculation."""
        client_ip = "192.168.1.1"
        category = "api"
        
        # Exceed rate limit
        for i in range(100):
            rate_limit_middleware.check_rate_limit(client_ip, category)
        
        retry_after = rate_limit_middleware.get_retry_after(client_ip, category)
        assert retry_after > 0
        assert retry_after <= 60  # Should be within the window


class TestCORSMiddleware:
    """Test cases for CORSMiddleware class."""
    
    @pytest.fixture
    def cors_middleware(self):
        """Create a CORSMiddleware instance for testing."""
        app = Mock()
        return CORSMiddleware(app)
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request for testing."""
        request = Mock(spec=Request)
        request.method = "GET"
        request.headers = {"origin": "http://localhost:3001"}
        return request
    
    async def test_preflight_request_handling(self, cors_middleware, mock_request):
        """Test OPTIONS preflight request handling."""
        mock_request.method = "OPTIONS"
        mock_request.headers["origin"] = "http://localhost:3001"
        
        mock_response = Mock(spec=Response)
        mock_response.headers = {}
        
        async def mock_call_next(request):
            return mock_response
        
        result = await cors_middleware.dispatch(mock_request, mock_call_next)
        
        assert result.headers["Access-Control-Allow-Origin"] == "http://localhost:3001"
        assert "Access-Control-Allow-Methods" in result.headers
        assert "Access-Control-Allow-Headers" in result.headers
        assert result.headers["Access-Control-Allow-Credentials"] == "true"
        assert result.headers["Access-Control-Max-Age"] == "86400"
    
    async def test_actual_request_handling(self, cors_middleware, mock_request):
        """Test actual request handling."""
        mock_response = Mock(spec=Response)
        mock_response.headers = {}
        
        async def mock_call_next(request):
            return mock_response
        
        result = await cors_middleware.dispatch(mock_request, mock_call_next)
        
        assert result.headers["Access-Control-Allow-Origin"] == "http://localhost:3001"
        assert result.headers["Access-Control-Allow-Credentials"] == "true"
    
    async def test_unauthorized_origin_blocked(self, cors_middleware, mock_request):
        """Test that unauthorized origins are blocked."""
        mock_request.headers["origin"] = "http://malicious.com"
        
        mock_response = Mock(spec=Response)
        mock_response.headers = {}
        
        async def mock_call_next(request):
            return mock_response
        
        result = await cors_middleware.dispatch(mock_request, mock_call_next)
        
        # Should not add CORS headers for unauthorized origin
        assert "Access-Control-Allow-Origin" not in result.headers


class TestSecurityUtilities:
    """Test cases for security utility functions."""
    
    def test_sanitize_headers(self):
        """Test header sanitization."""
        headers = {
            "user-agent": "Mozilla/5.0",
            "x-forwarded-for": "192.168.1.1",
            "x-real-ip": "10.0.0.1",
            "content-type": "application/json",
            "authorization": "Bearer <script>alert('xss')</script>"
        }
        
        sanitized = sanitize_headers(headers)
        
        # Blocked headers should be removed
        assert "x-forwarded-for" not in sanitized
        assert "x-real-ip" not in sanitized
        
        # Allowed headers should be sanitized
        assert sanitized["user-agent"] == "Mozilla/5.0"
        assert sanitized["content-type"] == "application/json"
        assert "&lt;script&gt;" in sanitized["authorization"]
    
    def test_validate_content_type(self):
        """Test content type validation."""
        # Valid content types
        assert validate_content_type("application/json")
        assert validate_content_type("application/x-www-form-urlencoded")
        assert validate_content_type("multipart/form-data")
        assert validate_content_type("text/plain")
        
        # Invalid content types
        assert not validate_content_type("application/octet-stream")
        assert not validate_content_type("text/html")
        assert not validate_content_type("image/jpeg")
    
    def test_log_security_event(self):
        """Test security event logging."""
        with patch('app.middleware.security.logger') as mock_logger:
            event_details = {
                "client_ip": "192.168.1.1",
                "event": "failed_login",
                "user_agent": "test-agent"
            }
            
            log_security_event("failed_login", event_details)
            
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args[1]
            assert call_args["event_type"] == "failed_login"
            assert call_args["details"] == event_details
            assert "timestamp" in call_args


class TestSecurityMiddlewareIntegration:
    """Integration tests for security middleware components."""
    
    @pytest.fixture
    def app_with_middleware(self):
        """Create a FastAPI app with security middleware for testing."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        app = FastAPI()
        
        # Add security middleware
        app.add_middleware(SecurityMiddleware)
        app.add_middleware(InputValidationMiddleware)
        app.add_middleware(RateLimitMiddleware)
        app.add_middleware(CORSMiddleware)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}
        
        @app.post("/test")
        async def test_post_endpoint():
            return {"message": "success"}
        
        return app, TestClient(app)
    
    def test_middleware_chain_security(self, app_with_middleware):
        """Test that all security middleware work together."""
        app, client = app_with_middleware
        
        # Test GET request (should add security headers)
        response = client.get("/test")
        
        assert response.status_code == 200
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "Content-Security-Policy" in response.headers
        assert "X-Process-Time" in response.headers
    
    def test_middleware_chain_rate_limiting(self, app_with_middleware):
        """Test rate limiting in middleware chain."""
        app, client = app_with_middleware
        
        # Make multiple requests to trigger rate limiting
        responses = []
        for i in range(101):  # Exceed default rate limit
            response = client.get("/test")
            responses.append(response)
        
        # Last request should be rate limited
        assert responses[-1].status_code == 429
        assert "Rate limit exceeded" in responses[-1].json()["error"]
    
    def test_middleware_chain_input_validation(self, app_with_middleware):
        """Test input validation in middleware chain."""
        app, client = app_with_middleware
        
        # Test malicious content
        malicious_data = "<script>alert('xss')</script>"
        response = client.post("/test", data=malicious_data)
        
        assert response.status_code == 400
        assert "Invalid request content" in response.json()["error"]


if __name__ == "__main__":
    pytest.main([__file__])
