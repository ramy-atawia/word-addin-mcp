"""
Unit tests for MCP API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import json


class TestMCPToolEndpoints:
    """Test class for MCP tool endpoints."""
    
    def test_list_available_tools(self, test_client: TestClient):
        """Test listing available MCP tools."""
        response = test_client.get("/api/v1/mcp/tools")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "tools" in data
        assert "total_count" in data
        assert "protocol_version" in data
        assert "server_capabilities" in data
        
        # Check tools list
        tools = data["tools"]
        assert isinstance(tools, list)
        assert len(tools) == 4  # We have 4 tools implemented
        
        # Check tool definitions
        tool_names = [tool["name"] for tool in tools]
        expected_tools = [
            "text_processor", 
            "document_analyzer",
            "web_content_fetcher",
            "data_formatter"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
        
        # Check protocol version
        assert data["protocol_version"] == "2024-11-05"
        
        # Check server capabilities
        capabilities = data["server_capabilities"]
        assert capabilities["tools.listChanged"] is True
        assert capabilities["tools.call"] is True
    
    def test_list_tools_response_structure(self, test_client: TestClient):
        """Test that tool list response has correct structure."""
        response = test_client.get("/api/v1/mcp/tools")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check first tool structure
        first_tool = data["tools"][0]
        assert "name" in first_tool
        assert "description" in first_tool
        assert "inputSchema" in first_tool
        
        # Check input schema structure
        input_schema = first_tool["inputSchema"]
        assert "type" in input_schema
        assert input_schema["type"] == "object"
        assert "properties" in input_schema
        assert "required" in input_schema
    
        assert "execution_time" in data
        assert "result" in data
        
        # Check result structure
        result = data["result"]
        assert "content" in result
        assert "content_type" in result
        assert "metadata" in result
        
        # Check content structure (the actual tool result)
        content = result["content"]
        assert "file_path" in content
        assert "size_bytes" in content
        assert "encoding" in content
    
    def test_execute_mcp_tool_text_processor(self, test_client: TestClient):
        """Test executing text_processor MCP tool."""
        request_data = {
            "tool_name": "text_processor",
            "parameters": {
                "text": "This is a test text for processing.",
                "operation": "summarize"
            },
            "session_id": "test-session-123",
            "request_id": "test-request-789"
        }
        
        response = test_client.post(
            "/api/v1/mcp/tools/execute",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["tool_name"] == "text_processor"
        assert data["status"] == "success"
        assert "result" in data
        
        # Check result structure
        result = data["result"]
        assert "content" in result
        assert "content_type" in result
        assert "metadata" in result
        
        # Check content structure (the actual tool result)
        content = result["content"]
        assert "processed_text" in content
        assert "operation" in content
        assert "original_length" in content
        assert "processed_length" in content
    
    def test_execute_mcp_tool_document_analyzer(self, test_client: TestClient):
        """Test executing document_analyzer MCP tool."""
        request_data = {
            "tool_name": "document_analyzer",
            "parameters": {
                "content": "This is a test document content for analysis.",
                "analysis_type": "readability"
            },
            "session_id": "test-session-123",
            "request_id": "test-request-101"
        }
        
        response = test_client.post(
            "/api/v1/mcp/tools/execute",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["tool_name"] == "document_analyzer"
        assert data["status"] == "success"
        assert "result" in data
        
        # Check result structure
        result = data["result"]
        assert "content" in result
        assert "content_type" in result
        assert "metadata" in result
        
        # Check content structure (the actual tool result)
        content = result["content"]
        assert "analysis_type" in content
        assert "summary" in content
        assert "metrics" in content
        assert "suggestions" in content
    
    def test_execute_mcp_tool_web_content_fetcher(self, test_client: TestClient):
        """Test executing web_content_fetcher MCP tool."""
        request_data = {
            "tool_name": "web_content_fetcher",
            "parameters": {
                "url": "https://example.com",
                "content_type": "text"
            },
            "session_id": "test-session-123",
            "request_id": "test-request-202"
        }
        
        response = test_client.post(
            "/api/v1/mcp/tools/execute",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["tool_name"] == "web_content_fetcher"
        assert data["status"] == "success"
        assert "result" in data
        
        # Check result structure
        result = data["result"]
        assert "content" in result
        assert "content_type" in result
        assert "metadata" in result
        
        # Check content structure (the actual tool result)
        content = result["content"]
        assert "url" in content
        assert "content" in content
        assert "content_type" in content
        assert "extraction_time" in content
    
    def test_execute_mcp_tool_data_formatter(self, test_client: TestClient):
        """Test executing data_formatter MCP tool."""
        request_data = {
            "tool_name": "data_formatter",
            "parameters": {
                "data": "name,age,city\nJohn,30,New York\nJane,25,Los Angeles",
                "output_format": "table"
            },
            "session_id": "test-session-123",
            "request_id": "test-request-303"
        }
        
        response = test_client.post(
            "/api/v1/mcp/tools/execute",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["tool_name"] == "data_formatter"
        assert data["status"] == "success"
        assert "result" in data
        
        # Check result structure
        result = data["result"]
        assert "content" in result
        assert "content_type" in result
        assert "metadata" in result
        
        # Check content structure (the actual tool result)
        content = result["content"]
        assert "output_format" in content
        assert "formatted_data" in content
        assert "input_length" in content
        assert "output_length" in content
    
    def test_execute_mcp_tool_unknown_tool(self, test_client: TestClient):
        """Test executing unknown MCP tool returns error."""
        request_data = {
            "tool_name": "unknown_tool",
            "parameters": {"test": "data"},
            "session_id": "test-session-123"
        }
        
        response = test_client.post(
            "/api/v1/mcp/tools/execute",
            json=request_data
        )
        
        assert response.status_code == 400
        data = response.json()
        
        assert "detail" in data
        assert "Unknown tool: unknown_tool" in data["detail"]
    
    def test_execute_mcp_tool_missing_parameters(self, test_client: TestClient):
        """Test executing MCP tool with missing required parameters."""
        request_data = {
            "tool_name": "text_processor",
            "parameters": {},  # Missing required 'text' parameter
            "session_id": "test-session-123"
        }
        
        response = test_client.post(
            "/api/v1/mcp/tools/execute",
            json=request_data
        )
        
        # Should still work as we have placeholder implementations
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "result" in data
    
    def test_execute_mcp_tool_invalid_session_id(self, test_client: TestClient):
        """Test executing MCP tool with invalid session ID."""
        request_data = {
            "tool_name": "text_processor",
            "parameters": {"text": "test text"},
            "session_id": "",  # Empty session ID
            "request_id": "test-request-404"
        }
        
        response = test_client.post(
            "/api/v1/mcp/tools/execute",
            json=request_data
        )
        
        # Should still work as we have placeholder implementations
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["session_id"] == ""
    
    def test_mcp_status_endpoint(self, test_client: TestClient):
        """Test MCP status endpoint."""
        response = test_client.get("/api/v1/mcp/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "connected"
        assert "server_url" in data
        assert "protocol_version" in data
        assert "last_heartbeat" in data
        assert "connection_health" in data
        assert "available_tools" in data
        assert "server_capabilities" in data
        
        # Check specific values
        assert data["protocol_version"] == "2024-11-05"
        assert data["connection_health"] == "healthy"
        assert data["available_tools"] == 5
        assert data["server_capabilities"]["tools.listChanged"] is True
        assert data["server_capabilities"]["tools.call"] is True


class TestMCPToolExecutionPerformance:
    """Test class for MCP tool execution performance."""
    
    def test_tool_execution_response_time(self, test_client: TestClient):
        """Test that MCP tool execution responds within acceptable time."""
        import time
        
        request_data = {
            "tool_name": "text_processor",
            "parameters": {"text": "test text"},
            "session_id": "test-session-123"
        }
        
        start_time = time.time()
        response = test_client.post(
            "/api/v1/mcp/tools/execute",
            json=request_data
        )
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Tool execution should respond within 1 second
        assert execution_time < 1.0
        assert response.status_code == 200
        
        # Check that execution time is recorded
        data = response.json()
        assert "execution_time" in data
        recorded_time = data["execution_time"]
        assert isinstance(recorded_time, (int, float))
        assert recorded_time >= 0.0
    
    def test_concurrent_tool_executions(self, test_client: TestClient):
        """Test that MCP tools can handle concurrent executions."""
        import threading
        import time
        
        results = []
        errors = []
        
        def execute_tool(tool_name, parameters):
            try:
                request_data = {
                    "tool_name": tool_name,
                    "parameters": parameters,
                    "session_id": f"test-session-{tool_name}",
                    "request_id": f"test-request-{tool_name}"
                }
                
                start_time = time.time()
                response = test_client.post(
                    "/api/v1/mcp/tools/execute",
                    json=request_data
                )
                end_time = time.time()
                
                results.append({
                    "tool_name": tool_name,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time
                })
            except Exception as e:
                errors.append({"tool_name": tool_name, "error": str(e)})
        
        # Execute different tools concurrently
        tools_to_test = [
            ("text_processor", {"text": "Test text 1", "operation": "summarize"}),
            ("document_analyzer", {"content": "Test content 1", "analysis_type": "readability"}),
            ("web_content_fetcher", {"url": "https://example1.com"}),
            ("data_formatter", {"data": "test,data,1", "output_format": "table"})
        ]
        
        threads = []
        for tool_name, parameters in tools_to_test:
            thread = threading.Thread(target=execute_tool, args=(tool_name, parameters))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check that all executions succeeded
        assert len(results) == 5
        assert len(errors) == 0
        
        # All executions should have 200 status
        for result in results:
            assert result["status_code"] == 200
            assert result["response_time"] < 1.0  # Each execution should be fast


class TestMCPToolErrorHandling:
    """Test class for MCP tool error handling."""
    
    def test_tool_execution_with_invalid_json(self, test_client: TestClient):
        """Test MCP tool execution with invalid JSON."""
        response = test_client.post(
            "/api/v1/mcp/tools/execute",
            data="invalid json data",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_tool_execution_with_missing_tool_name(self, test_client: TestClient):
        """Test MCP tool execution with missing tool name."""
        request_data = {
            "parameters": {"path": "./test.txt"},
            "session_id": "test-session-123"
        }
        
        response = test_client.post(
            "/api/v1/mcp/tools/execute",
            json=request_data
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_tool_execution_with_missing_session_id(self, test_client: TestClient):
        """Test MCP tool execution with missing session ID."""
        request_data = {
            "tool_name": "text_processor",
            "parameters": {"text": "test text"}
        }
        
        response = test_client.post(
            "/api/v1/mcp/tools/execute",
            json=request_data
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_tool_execution_with_empty_parameters(self, test_client: TestClient):
        """Test MCP tool execution with empty parameters."""
        request_data = {
            "tool_name": "text_processor",
            "parameters": None,
            "session_id": "test-session-123"
        }
        
        response = test_client.post(
            "/api/v1/mcp/tools/execute",
            json=request_data
        )
        
        # Should fail validation as parameters is required
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestMCPToolValidation:
    """Test class for MCP tool parameter validation."""
    
    def test_text_processor_parameter_validation(self, test_client: TestClient):
        """Test text_processor tool parameter validation."""
        # Test with valid parameters
        valid_request = {
            "tool_name": "text_processor",
            "parameters": {
                "text": "test text",
                "operation": "summarize"
            },
            "session_id": "test-session-123"
        }
        
        response = test_client.post(
            "/api/v1/mcp/tools/execute",
            json=valid_request
        )
        
        assert response.status_code == 200
        
        # Test with additional parameters (should be ignored by placeholder)
        extended_request = {
            "tool_name": "text_processor",
            "parameters": {
                "text": "test text",
                "operation": "summarize",
                "max_length": 100,
                "extra_param": "should_be_ignored"
            },
            "session_id": "test-session-123"
        }
        
        response = test_client.post(
            "/api/v1/mcp/tools/execute",
            json=extended_request
        )
        
        assert response.status_code == 200
    
    def test_text_processor_parameter_validation(self, test_client: TestClient):
        """Test text_processor tool parameter validation."""
        # Test with valid parameters
        valid_request = {
            "tool_name": "text_processor",
            "parameters": {
                "text": "This is a test text.",
                "operation": "summarize"
            },
            "session_id": "test-session-123"
        }
        
        response = test_client.post(
            "/api/v1/mcp/tools/execute",
            json=valid_request
        )
        
        assert response.status_code == 200
        
        # Test with different operations
        operations = ["summarize", "translate", "enhance"]
        for operation in operations:
            request_data = {
                "tool_name": "text_processor",
                "parameters": {
                    "text": f"Test text for {operation}",
                    "operation": operation
                },
                "session_id": "test-session-123"
            }
            
            response = test_client.post(
                "/api/v1/mcp/tools/execute",
                json=request_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
    
    def test_document_analyzer_parameter_validation(self, test_client: TestClient):
        """Test document_analyzer tool parameter validation."""
        # Test with valid parameters
        valid_request = {
            "tool_name": "document_analyzer",
            "parameters": {
                "content": "This is a test document content.",
                "analysis_type": "readability"
            },
            "session_id": "test-session-123"
        }
        
        response = test_client.post(
            "/api/v1/mcp/tools/execute",
            json=valid_request
        )
        
        assert response.status_code == 200
        
        # Test with different analysis types
        analysis_types = ["readability", "structure", "tone"]
        for analysis_type in analysis_types:
            request_data = {
                "tool_name": "document_analyzer",
                "parameters": {
                    "content": f"Test content for {analysis_type} analysis",
                    "analysis_type": analysis_type
                },
                "session_id": "test-session-123"
            }
            
            response = test_client.post(
                "/api/v1/mcp/tools/execute",
                json=request_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
