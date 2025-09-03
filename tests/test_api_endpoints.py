"""
API Endpoint Tests for Word Add-in MCP System
"""
import pytest
import httpx
import json
import time
import asyncio
from typing import Dict, Any
from conftest import API_BASE, HEALTH_URL

class TestAPIEndpoints:
    """Test suite for API endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, http_client: httpx.AsyncClient, test_result):
        """TC-001: Health Check Endpoint"""
        test_id = "TC-001"
        try:
            response = await http_client.get(HEALTH_URL)
            
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                assert "status" in data, "Response missing 'status' field"
                assert data["status"] == "healthy", f"Expected 'healthy', got '{data['status']}'"
                assert "timestamp" in data, "Response missing 'timestamp' field"
                assert "version" in data, "Response missing 'version' field"
                
                test_result.add_result(test_id, "PASS", {
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "response_data": data
                })
            else:
                test_result.add_result(test_id, "FAIL", {
                    "status_code": response.status_code,
                    "response_content": response.text,
                    "error": f"Expected 200, got {response.status_code}"
                })
                assert False, f"Expected 200, got {response.status_code}: {response.text}"
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "response_code": getattr(response, 'status_code', None) if 'response' in locals() else None
            })
            raise
    
    @pytest.mark.asyncio
    async def test_mcp_servers_list(self, http_client: httpx.AsyncClient, test_result):
        """TC-002: MCP Server List Endpoint"""
        test_id = "TC-002"
        try:
            response = await http_client.get(f"{API_BASE}/mcp/external/servers")
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "servers" in data, "Response missing 'servers' field"
            assert isinstance(data["servers"], list), "Servers field should be a list"
            assert len(data["servers"]) > 0, "Should have at least one server"
            
            # Check server structure
            server = data["servers"][0]
            assert "server_id" in server, "Server missing 'server_id' field"
            assert "name" in server, "Server missing 'name' field"
            assert "connected" in server, "Server missing 'connected' field"
            
            test_result.add_result(test_id, "PASS", {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "server_count": len(data["servers"]),
                "servers": data["servers"]
            })
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "response_code": getattr(response, 'status_code', None) if 'response' in locals() else None
            })
            raise
    
    @pytest.mark.asyncio
    async def test_authentication_endpoint(self, http_client: httpx.AsyncClient, test_result):
        """TC-003: Authentication Endpoint (Expected to fail - not implemented)"""
        test_id = "TC-003"
        try:
            response = await http_client.post(
                f"{API_BASE}/auth/login",
                json={
                    "username": "testuser",
                    "password": "testpass123"
                }
            )
            
            # This should fail since auth is not implemented (404 or 401)
            if response.status_code in [401, 404]:
                test_result.add_result(test_id, "PASS", {
                    "status_code": response.status_code,
                    "expected_failure": True,
                    "message": "Authentication correctly not implemented"
                })
            else:
                test_result.add_result(test_id, "FAIL", {
                    "status_code": response.status_code,
                    "expected_failure": False,
                    "message": "Authentication endpoint should return 401 or 404"
                })
                assert False, f"Expected 401 or 404, got {response.status_code}"
                
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "response_code": getattr(response, 'status_code', None) if 'response' in locals() else None
            })
            raise
    
    @pytest.mark.asyncio
    async def test_agent_chat_endpoint(self, http_client: httpx.AsyncClient, test_result, sample_document):
        """TC-004: Agent Chat Endpoint"""
        test_id = "TC-004"
        try:
            payload = {
                "message": "Hello, can you help me analyze this document?",
                "context": {
                    "document_content": sample_document[:1000],  # Truncate for testing
                    "chat_history": "[]",
                    "available_tools": "web_search_tool,text_analysis_tool"
                }
            }
            
            response = await http_client.post(
                f"{API_BASE}/mcp/agent/chat",
                json=payload
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "response" in data, "Response missing 'response' field"
            assert isinstance(data["response"], str), "Response should be a string"
            assert len(data["response"]) > 0, "Response should not be empty"
            
            test_result.add_result(test_id, "PASS", {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "response_length": len(data["response"]),
                "response_preview": data["response"][:100] + "..." if len(data["response"]) > 100 else data["response"]
            })
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "response_code": getattr(response, 'status_code', None) if 'response' in locals() else None
            })
            raise
    
    @pytest.mark.asyncio
    async def test_tool_execution_endpoint(self, http_client: httpx.AsyncClient, test_result):
        """TC-005: Tool Execution Endpoint"""
        test_id = "TC-005"
        try:
            payload = {
                "parameters": {
                    "text": "The quick brown fox jumps over the lazy dog. This sentence contains every letter of the alphabet.",
                    "operation": "summarize"
                }
            }
            
            response = await http_client.post(
                f"{API_BASE}/mcp/tools/text_analysis_tool/execute",
                json=payload
            )
            
            print(f"Tool execution response status: {response.status_code}")
            print(f"Tool execution response content: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                assert "result" in data, "Response missing 'result' field"
                
                # Check if result contains analysis data
                result = data["result"]
                if isinstance(result, dict):
                    has_analysis = any(key in result for key in ["result", "analysis", "summary", "confidence"])
                    assert has_analysis, "Result should contain analysis data"
                
                test_result.add_result(test_id, "PASS", {
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "result": result
                })
            else:
                test_result.add_result(test_id, "FAIL", {
                    "status_code": response.status_code,
                    "response_content": response.text,
                    "error": f"Expected 200, got {response.status_code}"
                })
                assert False, f"Expected 200, got {response.status_code}: {response.text}"
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "response_code": getattr(response, 'status_code', None) if 'response' in locals() else None
            })
            raise
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, http_client: httpx.AsyncClient, test_result):
        """TC-015: Rate Limiting (Expected to fail - not implemented)"""
        test_id = "TC-015"
        try:
            # Send multiple rapid requests
            responses = []
            for i in range(10):
                response = await http_client.get(HEALTH_URL)
                responses.append(response.status_code)
                await asyncio.sleep(0.1)  # Small delay between requests
            
            # Check if any requests were rate limited
            rate_limited = any(status == 429 for status in responses)
            
            if rate_limited:
                test_result.add_result(test_id, "PASS", {
                    "rate_limiting_implemented": True,
                    "responses": responses
                })
            else:
                test_result.add_result(test_id, "FAIL", {
                    "rate_limiting_implemented": False,
                    "message": "Rate limiting not implemented",
                    "responses": responses
                })
                
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e)
            })
            raise
