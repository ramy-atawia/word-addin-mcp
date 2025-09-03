"""
Integration Tests for Word Add-in MCP System
"""
import pytest
import httpx
import json
import time
from typing import Dict, Any
from conftest import API_BASE

class TestIntegration:
    """Test suite for integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_document_analysis(self, http_client: httpx.AsyncClient, test_result, sample_document):
        """TC-051: End-to-End Document Analysis"""
        test_id = "TC-051"
        try:
            # Step 1: Send document for analysis
            payload = {
                "message": "Please analyze this document and provide a summary of the key points.",
                "context": {
                    "document_content": sample_document,
                    "chat_history": "[]",
                    "available_tools": "document_analysis_tool,text_analysis_tool"
                }
            }
            
            response = await http_client.post(
                f"{API_BASE}/mcp/chat",
                json=payload
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "response" in data, "Response missing 'response' field"
            
            # Check if response contains analysis
            response_text = data["response"].lower()
            has_analysis = any(keyword in response_text for keyword in ["summary", "analysis", "key", "point"])
            
            test_result.add_result(test_id, "PASS", {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "has_analysis": has_analysis,
                "response_length": len(data["response"]),
                "response_preview": data["response"][:200] + "..." if len(data["response"]) > 200 else data["response"]
            })
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "response_code": getattr(response, 'status_code', None) if 'response' in locals() else None
            })
            raise
    
    @pytest.mark.asyncio
    async def test_conversation_flow(self, http_client: httpx.AsyncClient, test_result, sample_conversation):
        """TC-052: Conversation Flow"""
        test_id = "TC-052"
        try:
            # Test conversation with history
            payload = {
                "message": "What did I ask you about earlier?",
                "context": {
                    "document_content": "",
                    "chat_history": json.dumps(sample_conversation),
                    "available_tools": "text_analysis_tool"
                }
            }
            
            response = await http_client.post(
                f"{API_BASE}/mcp/chat",
                json=payload
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "response" in data, "Response missing 'response' field"
            
            # Check if response references conversation history
            response_text = data["response"].lower()
            has_context = any(keyword in response_text for keyword in ["business", "report", "analyze", "document"])
            
            test_result.add_result(test_id, "PASS", {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "has_context": has_context,
                "response_length": len(data["response"])
            })
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "response_code": getattr(response, 'status_code', None) if 'response' in locals() else None
            })
            raise
    
    @pytest.mark.asyncio
    async def test_tool_selection_integration(self, http_client: httpx.AsyncClient, test_result):
        """TC-053: Tool Selection Integration"""
        test_id = "TC-053"
        try:
            # Test that LLM selects appropriate tool
            payload = {
                "message": "Search for information about machine learning algorithms",
                "context": {
                    "document_content": "",
                    "chat_history": "[]",
                    "available_tools": "web_search_tool,text_analysis_tool,document_analysis_tool"
                }
            }
            
            response = await http_client.post(
                f"{API_BASE}/mcp/chat",
                json=payload
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            data = response.json()
            assert "response" in data, "Response missing 'response' field"
            
            # Check if tools were used (if available in response)
            tools_used = data.get("tools_used", [])
            
            test_result.add_result(test_id, "PASS", {
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "tools_used": tools_used,
                "response_length": len(data["response"])
            })
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "response_code": getattr(response, 'status_code', None) if 'response' in locals() else None
            })
            raise
    
    @pytest.mark.asyncio
    async def test_document_content_limits(self, http_client: httpx.AsyncClient, test_result):
        """TC-055: Document Content Limits"""
        test_id = "TC-055"
        try:
            # Create a very long document
            long_document = "This is a test document. " * 1000  # ~25,000 characters
            
            payload = {
                "message": "Analyze this document",
                "context": {
                    "document_content": long_document,
                    "chat_history": "[]",
                    "available_tools": "document_analysis_tool"
                }
            }
            
            response = await http_client.post(
                f"{API_BASE}/mcp/chat",
                json=payload
            )
            
            # Should handle large documents gracefully
            if response.status_code == 200:
                data = response.json()
                assert "response" in data, "Response missing 'response' field"
                
                test_result.add_result(test_id, "PASS", {
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "document_size": len(long_document),
                    "handled_large_document": True
                })
            else:
                test_result.add_result(test_id, "FAIL", {
                    "status_code": response.status_code,
                    "document_size": len(long_document),
                    "handled_large_document": False,
                    "message": "Failed to handle large document"
                })
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "response_code": getattr(response, 'status_code', None) if 'response' in locals() else None
            })
            raise
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, http_client: httpx.AsyncClient, test_result):
        """TC-056: Concurrent Requests"""
        test_id = "TC-056"
        try:
            import asyncio
            
            # Send multiple concurrent requests
            async def send_request():
                payload = {
                    "message": "Hello, this is a test message.",
                    "context": {
                        "document_content": "",
                        "chat_history": "[]",
                        "available_tools": "text_analysis_tool"
                    }
                }
                return await http_client.post(f"{API_BASE}/mcp/chat", json=payload)
            
            # Send 5 concurrent requests
            tasks = [send_request() for _ in range(5)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check results
            successful_responses = [r for r in responses if not isinstance(r, Exception) and r.status_code == 200]
            failed_responses = [r for r in responses if isinstance(r, Exception) or r.status_code != 200]
            
            success_rate = len(successful_responses) / len(responses) * 100
            
            if success_rate >= 80:  # At least 80% success rate
                test_result.add_result(test_id, "PASS", {
                    "total_requests": len(responses),
                    "successful_requests": len(successful_responses),
                    "failed_requests": len(failed_responses),
                    "success_rate": success_rate
                })
            else:
                test_result.add_result(test_id, "FAIL", {
                    "total_requests": len(responses),
                    "successful_requests": len(successful_responses),
                    "failed_requests": len(failed_responses),
                    "success_rate": success_rate,
                    "message": "Success rate too low"
                })
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e)
            })
            raise
