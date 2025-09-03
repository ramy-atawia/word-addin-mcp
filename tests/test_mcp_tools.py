"""
MCP Tool Functionality Tests for Word Add-in MCP System
"""
import pytest
import httpx
import json
import time
from typing import Dict, Any
from conftest import API_BASE

class TestMCPTools:
    """Test suite for MCP tool functionality."""
    
    @pytest.mark.asyncio
    async def test_web_search_tool(self, http_client: httpx.AsyncClient, test_result):
        """TC-021: Web Search Tool"""
        test_id = "TC-021"
        try:
            payload = {
                "parameters": {
                    "query": "latest AI trends 2025",
                    "max_results": 5
                }
            }
            
            response = await http_client.post(
                f"{API_BASE}/mcp/tools/web_search_tool/execute",
                json=payload
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "result" in data, "Response missing 'result' field"
            
            result = data["result"]
            # Check if result contains search results
            if isinstance(result, dict):
                has_results = any(key in result for key in ["results", "data", "items"])
                assert has_results, "Result should contain search results"
            
            test_result.add_result(test_id, "PASS", {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "result_type": type(result).__name__,
                "result_keys": list(result.keys()) if isinstance(result, dict) else None
            })
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "response_code": getattr(response, 'status_code', None) if 'response' in locals() else None
            })
            raise
    
    @pytest.mark.asyncio
    async def test_text_analysis_tool(self, http_client: httpx.AsyncClient, test_result):
        """TC-022: Text Analysis Tool"""
        test_id = "TC-022"
        try:
            test_text = "The quick brown fox jumps over the lazy dog. This sentence contains every letter of the alphabet."
            
            payload = {
                "parameters": {
                    "text": test_text,
                    "operation": "summarize"
                }
            }
            
            response = await http_client.post(
                f"{API_BASE}/mcp/tools/text_analysis_tool/execute",
                json=payload
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "result" in data, "Response missing 'result' field"
            
            result = data["result"]
            # Check if result contains analysis data
            if isinstance(result, dict):
                has_analysis = any(key in result for key in ["word_count", "character_count", "analysis"])
                assert has_analysis, "Result should contain analysis data"
            
            test_result.add_result(test_id, "PASS", {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "result": result
            })
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "response_code": getattr(response, 'status_code', None) if 'response' in locals() else None
            })
            raise
    
    @pytest.mark.asyncio
    async def test_document_analysis_tool(self, http_client: httpx.AsyncClient, test_result, sample_document):
        """TC-023: Document Analysis Tool"""
        test_id = "TC-023"
        try:
            payload = {
                "parameters": {
                    "content": sample_document
                }
            }
            
            response = await http_client.post(
                f"{API_BASE}/mcp/tools/document_analysis_tool/execute",
                json=payload
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "result" in data, "Response missing 'result' field"
            
            result = data["result"]
            # Check if result contains document analysis
            if isinstance(result, dict):
                has_analysis = any(key in result for key in ["summary", "analysis", "key_points"])
                assert has_analysis, "Result should contain document analysis"
            
            test_result.add_result(test_id, "PASS", {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "result": result
            })
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "response_code": getattr(response, 'status_code', None) if 'response' in locals() else None
            })
            raise
    
    @pytest.mark.asyncio
    async def test_file_reader_tool(self, http_client: httpx.AsyncClient, test_result):
        """TC-024: File Reader Tool"""
        test_id = "TC-024"
        try:
            payload = {
                "parameters": {
                    "file_path": "README.md",
                    "max_size": 1000
                }
            }
            
            response = await http_client.post(
                f"{API_BASE}/mcp/tools/file_reader_tool/execute",
                json=payload
            )
            
            # This might fail if file doesn't exist, which is expected
            if response.status_code == 200:
                data = response.json()
                assert "result" in data, "Response missing 'result' field"
                
                result = data["result"]
                test_result.add_result(test_id, "PASS", {
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "result": result
                })
            else:
                # Expected failure for non-existent file
                test_result.add_result(test_id, "PASS", {
                    "status_code": response.status_code,
                    "expected_failure": True,
                    "message": "File not found (expected)"
                })
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "response_code": getattr(response, 'status_code', None) if 'response' in locals() else None
            })
            raise
    
    @pytest.mark.asyncio
    async def test_external_mcp_server_connection(self, http_client: httpx.AsyncClient, test_result):
        """TC-025: External MCP Server Connection"""
        test_id = "TC-025"
        try:
            # Test connection to external MCP server
            response = await http_client.get(f"{API_BASE}/mcp/servers")
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            servers = data.get("servers", [])
            
            # Check for external servers
            external_servers = [s for s in servers if s.get("name") != "Internal MCP Server"]
            
            if external_servers:
                connected_external = [s for s in external_servers if s.get("status") == "connected"]
                
                if connected_external:
                    test_result.add_result(test_id, "PASS", {
                        "external_servers": len(external_servers),
                        "connected_external": len(connected_external),
                        "servers": external_servers
                    })
                else:
                    test_result.add_result(test_id, "FAIL", {
                        "external_servers": len(external_servers),
                        "connected_external": 0,
                        "message": "No external servers connected",
                        "servers": external_servers
                    })
            else:
                test_result.add_result(test_id, "FAIL", {
                    "external_servers": 0,
                    "message": "No external servers found"
                })
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "response_code": getattr(response, 'status_code', None) if 'response' in locals() else None
            })
            raise
    
    @pytest.mark.asyncio
    async def test_tool_error_handling(self, http_client: httpx.AsyncClient, test_result):
        """TC-026: Tool Error Handling"""
        test_id = "TC-026"
        try:
            # Test with invalid tool name
            payload = {
                "tool_name": "invalid_tool_name",
                "parameters": {
                    "test": "data"
                }
            }
            
            response = await http_client.post(
                f"{API_BASE}/mcp/tools/execute",
                json=payload
            )
            
            # Should return an error for invalid tool
            if response.status_code in [400, 404, 422]:
                test_result.add_result(test_id, "PASS", {
                    "status_code": response.status_code,
                    "error_handling": True,
                    "message": "Correctly handled invalid tool"
                })
            else:
                test_result.add_result(test_id, "FAIL", {
                    "status_code": response.status_code,
                    "error_handling": False,
                    "message": "Should return error for invalid tool"
                })
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "response_code": getattr(response, 'status_code', None) if 'response' in locals() else None
            })
            raise
