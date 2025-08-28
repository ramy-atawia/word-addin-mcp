"""
End-to-End MCP Client-Server Interaction Tests

This test suite covers complete MCP protocol flows including:
- Client initialization and connection establishment
- Tool discovery and capability negotiation
- Tool execution with various input types
- Error handling and recovery scenarios
- Performance and reliability testing
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status

from backend.app.main import app
from backend.app.core.mcp_client import MCPClient, MCPConnectionConfig
from backend.app.core.mcp_server import MCPServer
from backend.app.services.mcp_service import MCPService


class TestMCPE2EInteractions:
    """End-to-end MCP client-server interaction tests."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mcp_server(self):
        """Create MCP server instance."""
        return MCPServer()
    
    @pytest.fixture
    def mcp_client_config(self):
        """Create MCP client configuration."""
        return MCPConnectionConfig(
            server_url="http://localhost:8000",
            timeout=10,
            max_retries=3,
            retry_delay=0.1
        )
    
    @pytest.fixture
    def mcp_service(self):
        """Create MCP service instance."""
        return MCPService()


class TestMCPInitializationFlow:
    """Test MCP protocol initialization sequence."""
    
    def test_mcp_initialization_handshake(self, test_client):
        """Test complete MCP initialization handshake."""
        # Step 1: Client sends initialization request
        init_request = {
            "jsonrpc": "2.0",
            "id": "init_001",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "word-addin-mcp-client",
                    "version": "1.0.0"
                }
            }
        }
        
        response = test_client.post("/api/v1/mcp/initialize", json=init_request)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "init_001"
        assert "result" in data
        
        result = data["result"]
        assert result["protocolVersion"] == "2024-11-05"
        assert "capabilities" in result
        assert "serverInfo" in result
        
        # Verify server capabilities
        capabilities = result["capabilities"]
        assert "tools" in capabilities
        assert capabilities["tools"]["listChanged"] is True
        
        # Verify server info
        server_info = result["serverInfo"]
        assert server_info["name"] == "word-addin-mcp-server"
        assert server_info["version"] == "1.0.0"
    
    def test_mcp_capability_negotiation(self, test_client):
        """Test MCP capability negotiation."""
        # Test with minimal capabilities
        init_request = {
            "jsonrpc": "2.0",
            "id": "cap_test_001",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "minimal-client",
                    "version": "0.1.0"
                }
            }
        }
        
        response = test_client.post("/api/v1/mcp/initialize", json=init_request)
        assert response.status_code == status.HTTP_200_OK
        
        # Test with extended capabilities
        init_request["params"]["capabilities"] = {
            "tools": {"listChanged": True},
            "chat": {"completions": True},
            "files": {"list": True}
        }
        
        response = test_client.post("/api/v1/mcp/initialize", json=init_request)
        assert response.status_code == status.HTTP_200_OK


class TestMCPToolDiscoveryFlow:
    """Test MCP tool discovery and listing."""
    
    def test_mcp_tools_list_discovery(self, test_client):
        """Test complete tool discovery flow."""
        # Step 1: Initialize connection
        init_request = {
            "jsonrpc": "2.0",
            "id": "discovery_001",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "discovery-client", "version": "1.0.0"}
            }
        }
        
        init_response = test_client.post("/api/v1/mcp/initialize", json=init_request)
        assert init_response.status_code == status.HTTP_200_OK
        
        # Step 2: Request tools list
        tools_request = {
            "jsonrpc": "2.0",
            "id": "tools_list_001",
            "method": "tools/list",
            "params": {}
        }
        
        tools_response = test_client.post("/api/v1/mcp/tools/list", json=tools_request)
        assert tools_response.status_code == status.HTTP_200_OK
        
        data = tools_response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "tools_list_001"
        assert "result" in data
        
        result = data["result"]
        assert "tools" in result
        tools = result["tools"]
        
        # Verify expected tools are present
        tool_names = [tool["name"] for tool in tools]
        expected_tools = ["file_reader", "text_processor", "document_analyzer", 
                         "web_content_fetcher", "data_formatter"]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
        
        # Verify tool schema structure
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert tool["inputSchema"]["type"] == "object"
            assert "properties" in tool["inputSchema"]
            assert "required" in tool["inputSchema"]
    
    def test_mcp_tool_info_retrieval(self, test_client):
        """Test individual tool information retrieval."""
        # Test file_reader tool
        tool_info = test_client.get("/api/v1/mcp/tools/file_reader")
        assert tool_info.status_code == status.HTTP_200_OK
        
        data = tool_info.json()
        assert data["name"] == "file_reader"
        assert "inputSchema" in data
        
        schema = data["inputSchema"]
        assert schema["type"] == "object"
        assert "path" in schema["properties"]
        assert "path" in schema["required"]
        
        # Test text_processor tool
        tool_info = test_client.get("/api/v1/mcp/tools/text_processor")
        assert tool_info.status_code == status.HTTP_200_OK
        
        data = tool_info.json()
        assert data["name"] == "text_processor"
        assert "operation" in data["inputSchema"]["properties"]
        assert "summarize" in data["inputSchema"]["properties"]["operation"]["enum"]


class TestMCPToolExecutionFlow:
    """Test MCP tool execution with various input scenarios."""
    
    def test_file_reader_tool_execution(self, test_client):
        """Test file reader tool execution with different inputs."""
        # Test with valid file path
        execution_request = {
            "jsonrpc": "2.0",
            "id": "file_read_001",
            "method": "tools/call",
            "params": {
                "name": "file_reader",
                "arguments": {
                    "path": "/tmp/test.txt",
                    "encoding": "utf-8",
                    "max_size": 1024
                }
            }
        }
        
        response = test_client.post("/api/v1/mcp/tools/call", json=execution_request)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "file_read_001"
        assert "result" in data
        
        # Test with missing required parameter
        execution_request["params"]["arguments"] = {"encoding": "utf-8"}
        response = test_client.post("/api/v1/mcp/tools/call", json=execution_request)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32602  # Invalid params
        
        # Test with invalid parameter values
        execution_request["params"]["arguments"] = {
            "path": "",
            "max_size": -1
        }
        response = test_client.post("/api/v1/mcp/tools/call", json=execution_request)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "error" in data
    
    def test_text_processor_tool_execution(self, test_client):
        """Test text processor tool with various operations."""
        test_cases = [
            {
                "operation": "summarize",
                "text": "This is a long text that needs to be summarized. It contains multiple sentences and should be processed by the text processor tool.",
                "expected_success": True
            },
            {
                "operation": "translate",
                "text": "Hello world",
                "expected_success": True
            },
            {
                "operation": "extract_keywords",
                "text": "Machine learning artificial intelligence data science",
                "expected_success": True
            },
            {
                "operation": "invalid_operation",
                "text": "Test text",
                "expected_success": False
            }
        ]
        
        for test_case in test_cases:
            execution_request = {
                "jsonrpc": "2.0",
                "id": f"text_proc_{test_case['operation']}",
                "method": "tools/call",
                "params": {
                    "name": "text_processor",
                    "arguments": {
                        "text": test_case["text"],
                        "operation": test_case["operation"]
                    }
                }
            }
            
            response = test_client.post("/api/v1/mcp/tools/call", json=execution_request)
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            if test_case["expected_success"]:
                assert "result" in data
                assert "content" in data["result"]
            else:
                assert "error" in data
    
    def test_document_analyzer_tool_execution(self, test_client):
        """Test document analyzer tool with different content types."""
        test_documents = [
            {
                "content": "This is a simple document for analysis.",
                "analysis_type": "readability",
                "description": "Simple text document"
            },
            {
                "content": "Complex document with multiple paragraphs. This should test the analyzer's ability to handle longer content and provide meaningful insights.",
                "analysis_type": "structure",
                "description": "Multi-paragraph document"
            },
            {
                "content": "Technical document containing: algorithms, data structures, and implementation details.",
                "analysis_type": "keyword_extraction",
                "description": "Technical document"
            }
        ]
        
        for doc in test_documents:
            execution_request = {
                "jsonrpc": "2.0",
                "id": f"doc_analysis_{doc['analysis_type']}",
                "method": "tools/call",
                "params": {
                    "name": "document_analyzer",
                    "arguments": {
                        "content": doc["content"],
                        "analysis_type": doc["analysis_type"]
                    }
                }
            }
            
            response = test_client.post("/api/v1/mcp/tools/call", json=execution_request)
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert "result" in data
            assert "content" in data["result"]


class TestMCPErrorHandling:
    """Test MCP error handling and recovery scenarios."""
    
    def test_mcp_method_not_found(self, test_client):
        """Test handling of unknown MCP methods."""
        unknown_method_request = {
            "jsonrpc": "2.0",
            "id": "unknown_method_001",
            "method": "unknown/method",
            "params": {}
        }
        
        response = test_client.post("/api/v1/mcp/tools/call", json=unknown_method_request)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32601  # Method not found
    
    def test_mcp_invalid_json(self, test_client):
        """Test handling of invalid JSON requests."""
        # Send malformed JSON
        response = test_client.post(
            "/api/v1/mcp/tools/call",
            data="invalid json content",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_mcp_missing_required_fields(self, test_client):
        """Test handling of requests with missing required fields."""
        incomplete_request = {
            "jsonrpc": "2.0",
            "id": "incomplete_001"
            # Missing method and params
        }
        
        response = test_client.post("/api/v1/mcp/tools/call", json=incomplete_request)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "error" in data
    
    def test_mcp_tool_execution_timeout(self, test_client):
        """Test tool execution timeout handling."""
        # This would require a tool that takes a long time to execute
        # For now, test the timeout parameter handling
        execution_request = {
            "jsonrpc": "2.0",
            "id": "timeout_test_001",
            "method": "tools/call",
            "params": {
                "name": "file_reader",
                "arguments": {
                    "path": "/very/large/file.txt",
                    "max_size": 1000000000  # 1GB
                }
            }
        }
        
        response = test_client.post("/api/v1/mcp/tools/call", json=execution_request)
        assert response.status_code == status.HTTP_200_OK


class TestMCPPerformanceAndReliability:
    """Test MCP performance and reliability under various conditions."""
    
    def test_mcp_concurrent_requests(self, test_client):
        """Test handling of concurrent MCP requests."""
        import threading
        import queue
        
        results = queue.Queue()
        num_requests = 10
        
        def make_request(request_id):
            execution_request = {
                "jsonrpc": "2.0",
                "id": f"concurrent_{request_id}",
                "method": "tools/call",
                "params": {
                    "name": "text_processor",
                    "arguments": {
                        "text": f"Test text for request {request_id}",
                        "operation": "summarize"
                    }
                }
            }
            
            response = test_client.post("/api/v1/mcp/tools/call", json=execution_request)
            results.put((request_id, response.status_code))
        
        # Start concurrent requests
        threads = []
        for i in range(num_requests):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded
        successful_requests = 0
        while not results.empty():
            request_id, status_code = results.get()
            if status_code == status.HTTP_200_OK:
                successful_requests += 1
        
        assert successful_requests == num_requests
    
    def test_mcp_request_id_uniqueness(self, test_client):
        """Test that MCP request IDs are unique and properly handled."""
        request_ids = set()
        num_requests = 20
        
        for i in range(num_requests):
            execution_request = {
                "jsonrpc": "2.0",
                "id": f"unique_id_test_{i}_{int(time.time() * 1000)}",
                "method": "tools/call",
                "params": {
                    "name": "text_processor",
                    "arguments": {
                        "text": f"Test text {i}",
                        "operation": "summarize"
                    }
                }
            }
            
            response = test_client.post("/api/v1/mcp/tools/call", json=execution_request)
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            request_id = data["id"]
            assert request_id not in request_ids
            request_ids.add(request_id)
    
    def test_mcp_response_time_consistency(self, test_client):
        """Test that MCP response times are consistent."""
        response_times = []
        num_requests = 5
        
        for i in range(num_requests):
            start_time = time.time()
            
            execution_request = {
                "jsonrpc": "2.0",
                "id": f"perf_test_{i}",
                "method": "tools/call",
                "params": {
                    "name": "text_processor",
                    "arguments": {
                        "text": "Performance test text",
                        "operation": "summarize"
                    }
                }
            }
            
            response = test_client.post("/api/v1/mcp/tools/call", json=execution_request)
            end_time = time.time()
            
            assert response.status_code == status.HTTP_200_OK
            response_times.append(end_time - start_time)
        
        # Verify response times are reasonable (under 1 second for simple operations)
        for response_time in response_times:
            assert response_time < 1.0


class TestMCPIntegrationScenarios:
    """Test complete MCP integration scenarios."""
    
    def test_mcp_complete_workflow(self, test_client):
        """Test complete MCP workflow from initialization to tool execution."""
        # Step 1: Initialize MCP connection
        init_request = {
            "jsonrpc": "2.0",
            "id": "workflow_001",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "workflow-client", "version": "1.0.0"}
            }
        }
        
        init_response = test_client.post("/api/v1/mcp/initialize", json=init_request)
        assert init_response.status_code == status.HTTP_200_OK
        
        # Step 2: Discover available tools
        tools_request = {
            "jsonrpc": "2.0",
            "id": "workflow_002",
            "method": "tools/list",
            "params": {}
        }
        
        tools_response = test_client.post("/api/v1/mcp/tools/list", json=tools_request)
        assert tools_response.status_code == status.HTTP_200_OK
        
        # Step 3: Execute a tool
        execution_request = {
            "jsonrpc": "2.0",
            "id": "workflow_003",
            "method": "tools/call",
            "params": {
                "name": "text_processor",
                "arguments": {
                    "text": "This is a test document for the complete workflow.",
                    "operation": "summarize"
                }
            }
        }
        
        execution_response = test_client.post("/api/v1/mcp/tools/call", json=execution_request)
        assert execution_response.status_code == status.HTTP_200_OK
        
        # Step 4: Verify the complete flow
        init_data = init_response.json()
        tools_data = tools_response.json()
        execution_data = execution_response.json()
        
        # Verify initialization
        assert init_data["result"]["protocolVersion"] == "2024-11-05"
        
        # Verify tool discovery
        assert len(tools_data["result"]["tools"]) >= 5
        
        # Verify tool execution
        assert "result" in execution_data
        assert "content" in execution_data["result"]
    
    def test_mcp_multiple_tool_execution(self, test_client):
        """Test execution of multiple tools in sequence."""
        tools_to_test = [
            ("text_processor", {"text": "First test text", "operation": "summarize"}),
            ("document_analyzer", {"content": "Second test content", "analysis_type": "readability"}),
            ("data_formatter", {"data": "Third test data", "format": "summary"})
        ]
        
        for i, (tool_name, arguments) in enumerate(tools_to_test):
            execution_request = {
                "jsonrpc": "2.0",
                "id": f"multi_tool_{i}",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            response = test_client.post("/api/v1/mcp/tools/call", json=execution_request)
            assert response.status_code == status.HTTP_200_OK
            
            data = response.json()
            assert "result" in data
            assert "content" in data["result"]
    
    def test_mcp_error_recovery(self, test_client):
        """Test MCP error recovery and continued operation."""
        # Step 1: Make a valid request
        valid_request = {
            "jsonrpc": "2.0",
            "id": "recovery_001",
            "method": "tools/call",
            "params": {
                "name": "text_processor",
                "arguments": {
                    "text": "Valid text",
                    "operation": "summarize"
                }
            }
        }
        
        response = test_client.post("/api/v1/mcp/tools/call", json=valid_request)
        assert response.status_code == status.HTTP_200_OK
        
        # Step 2: Make an invalid request
        invalid_request = {
            "jsonrpc": "2.0",
            "id": "recovery_002",
            "method": "tools/call",
            "params": {
                "name": "nonexistent_tool",
                "arguments": {}
            }
        }
        
        response = test_client.post("/api/v1/mcp/tools/call", json=invalid_request)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "error" in data
        
        # Step 3: Make another valid request to ensure recovery
        response = test_client.post("/api/v1/mcp/tools/call", json=valid_request)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "result" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
