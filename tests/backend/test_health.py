"""
Unit tests for health check API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock


class TestHealthEndpoints:
    """Test class for health check endpoints."""
    
    def test_health_check_basic(self, test_client: TestClient):
        """Test basic health check endpoint."""
        response = test_client.get("/health/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"
        assert data["environment"] == "development"
        assert data["service"] == "Word Add-in MCP API"
    
    def test_health_check_detailed(self, test_client: TestClient):
        """Test detailed health check endpoint."""
        response = test_client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"
        assert data["environment"] == "development"
        assert data["service"] == "Word Add-in MCP API"
        assert "dependencies" in data
        
        # Check dependencies
        dependencies = data["dependencies"]
        assert "database" in dependencies
        assert "redis" in dependencies
        assert "mcp_server" in dependencies
        assert "azure_openai" in dependencies
        
        # All dependencies should be healthy in test environment
        for dep_name, dep_info in dependencies.items():
            assert dep_info["status"] == "healthy"
            assert "response_time" in dep_info
            assert "details" in dep_info
    
    def test_health_check_ready(self, test_client: TestClient):
        """Test readiness check endpoint."""
        response = test_client.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "ready"
        assert "timestamp" in data
        assert "details" in data
        assert data["details"] == "All services are ready"
    
    def test_health_check_live(self, test_client: TestClient):
        """Test liveness check endpoint."""
        response = test_client.get("/health/live")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "alive"
        assert "timestamp" in data
        assert "pid" in data
        assert "uptime" in data
    
    def test_health_check_metrics(self, test_client: TestClient):
        """Test metrics endpoint."""
        response = test_client.get("/health/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "timestamp" in data
        assert data["version"] == "1.0.0"
        assert data["environment"] == "development"
        assert "metrics" in data
        
        metrics = data["metrics"]
        assert "requests_total" in metrics
        assert "requests_active" in metrics
        assert "errors_total" in metrics
        assert "response_time_avg" in metrics
        
        # Initial metrics should be 0
        assert metrics["requests_total"] == 0
        assert metrics["requests_active"] == 0
        assert metrics["errors_total"] == 0
        assert metrics["response_time_avg"] == 0.0
    
    def test_health_check_headers(self, test_client: TestClient):
        """Test that health check endpoints return proper headers."""
        response = test_client.get("/health/")
        
        assert response.status_code == 200
        assert "content-type" in response.headers
        assert response.headers["content-type"] == "application/json"
    
    def test_health_check_response_time(self, test_client: TestClient):
        """Test that health check endpoints include response time header."""
        response = test_client.get("/health/")
        
        assert response.status_code == 200
        assert "X-Process-Time" in response.headers
        
        # Response time should be a valid float
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0.0
    
    def test_health_check_request_id(self, test_client: TestClient):
        """Test that health check endpoints include request ID header."""
        response = test_client.get("/health/")
        
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        
        # Request ID should be a valid string
        request_id = response.headers["X-Request-ID"]
        assert isinstance(request_id, str)
        assert len(request_id) > 0
    
    @pytest.mark.parametrize("endpoint", [
        "/health/",
        "/health/detailed",
        "/health/ready",
        "/health/live",
        "/health/metrics"
    ])
    def test_health_endpoints_consistency(self, test_client: TestClient, endpoint: str):
        """Test that all health endpoints return consistent data structure."""
        response = test_client.get(endpoint)
        
        assert response.status_code == 200
        data = response.json()
        
        # All endpoints should return JSON
        assert isinstance(data, dict)
        
        # All endpoints should have timestamp
        assert "timestamp" in data
        
        # Timestamp should be a valid number
        timestamp = data["timestamp"]
        assert isinstance(timestamp, (int, float))
        assert timestamp > 0
    
    def test_health_check_error_handling(self, test_client: TestClient):
        """Test health check endpoints handle errors gracefully."""
        # This test would require mocking internal dependencies to fail
        # For now, we test that the endpoints don't crash on normal requests
        
        # Test with invalid HTTP method
        response = test_client.post("/health/")
        assert response.status_code == 405  # Method Not Allowed
        
        # Test with invalid endpoint
        response = test_client.get("/health/invalid")
        assert response.status_code == 404  # Not Found
    
    def test_health_check_cors_headers(self, test_client: TestClient):
        """Test that health check endpoints include CORS headers."""
        # Test that CORS headers are present in regular GET request
        response = test_client.get("/health/", headers={"Origin": "http://localhost:3001"})
        
        # Check CORS headers that should be present for all requests
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-credentials" in response.headers


class TestHealthEndpointPerformance:
    """Test class for health endpoint performance."""
    
    def test_health_check_response_time_under_threshold(self, test_client: TestClient):
        """Test that health check endpoints respond within acceptable time."""
        import time
        
        start_time = time.time()
        response = test_client.get("/health/")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Health check should respond within 100ms
        assert response_time < 0.1
        assert response.status_code == 200
    
    def test_health_check_concurrent_requests(self, test_client: TestClient):
        """Test that health check endpoints handle concurrent requests."""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request():
            try:
                start_time = time.time()
                response = test_client.get("/health/")
                end_time = time.time()
                
                results.append({
                    "status_code": response.status_code,
                    "response_time": end_time - start_time
                })
            except Exception as e:
                errors.append(str(e))
        
        # Create 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check that all requests succeeded
        assert len(results) == 10
        assert len(errors) == 0
        
        # All requests should have 200 status
        for result in results:
            assert result["status_code"] == 200
            assert result["response_time"] < 0.1  # Each request should be fast


class TestHealthEndpointEdgeCases:
    """Test class for health endpoint edge cases."""
    
    def test_health_check_with_query_parameters(self, test_client: TestClient):
        """Test health check endpoints with query parameters."""
        response = test_client.get("/health/?format=json&detailed=true")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_health_check_with_headers(self, test_client: TestClient):
        """Test health check endpoints with custom headers."""
        headers = {
            "User-Agent": "TestClient/1.0",
            "Accept": "application/json",
            "X-Custom-Header": "test-value"
        }
        
        response = test_client.get("/health/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_health_check_content_type_negotiation(self, test_client: TestClient):
        """Test health check endpoints with different content type preferences."""
        # Test with JSON preference
        headers = {"Accept": "application/json"}
        response = test_client.get("/health/", headers=headers)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        # Test with wildcard preference
        headers = {"Accept": "*/*"}
        response = test_client.get("/health/", headers=headers)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
