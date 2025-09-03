"""
Performance Tests for Word Add-in MCP System
"""
import pytest
import httpx
import json
import time
import asyncio
from typing import Dict, Any
from conftest import API_BASE

class TestPerformance:
    """Test suite for performance testing."""
    
    @pytest.mark.asyncio
    async def test_api_response_time(self, http_client: httpx.AsyncClient, test_result):
        """TC-069: API Response Time"""
        test_id = "TC-069"
        try:
            start_time = time.time()
            
            response = await http_client.get(f"{API_BASE}/health")
            
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert response_time < 2.0, f"Response time {response_time:.2f}s exceeds 2s limit"
            
            test_result.add_result(test_id, "PASS", {
                "status_code": response.status_code,
                "response_time": response_time,
                "within_limit": response_time < 2.0
            })
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "response_code": getattr(response, 'status_code', None) if 'response' in locals() else None,
                "response_time": getattr(locals(), 'response_time', None)
            })
            raise
    
    @pytest.mark.asyncio
    async def test_chat_response_time(self, http_client: httpx.AsyncClient, test_result):
        """TC-070: Chat Response Time"""
        test_id = "TC-070"
        try:
            payload = {
                "message": "Hello, this is a test message for performance testing.",
                "context": {
                    "document_content": "",
                    "chat_history": "[]",
                    "available_tools": "text_analysis_tool"
                }
            }
            
            start_time = time.time()
            
            response = await http_client.post(
                f"{API_BASE}/mcp/chat",
                json=payload
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert response_time < 5.0, f"Response time {response_time:.2f}s exceeds 5s limit"
            
            test_result.add_result(test_id, "PASS", {
                "status_code": response.status_code,
                "response_time": response_time,
                "within_limit": response_time < 5.0
            })
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "response_code": getattr(response, 'status_code', None) if 'response' in locals() else None,
                "response_time": getattr(locals(), 'response_time', None)
            })
            raise
    
    @pytest.mark.asyncio
    async def test_tool_execution_time(self, http_client: httpx.AsyncClient, test_result):
        """TC-071: Tool Execution Time"""
        test_id = "TC-071"
        try:
            payload = {
                "tool_name": "text_analysis_tool",
                "parameters": {
                    "text": "This is a test text for performance analysis. " * 10,
                    "analysis_type": "word_count"
                }
            }
            
            start_time = time.time()
            
            response = await http_client.post(
                f"{API_BASE}/mcp/tools/execute",
                json=payload
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert response_time < 3.0, f"Response time {response_time:.2f}s exceeds 3s limit"
            
            test_result.add_result(test_id, "PASS", {
                "status_code": response.status_code,
                "response_time": response_time,
                "within_limit": response_time < 3.0
            })
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "response_code": getattr(response, 'status_code', None) if 'response' in locals() else None,
                "response_time": getattr(locals(), 'response_time', None)
            })
            raise
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, http_client: httpx.AsyncClient, test_result):
        """TC-072: Memory Usage Under Load"""
        test_id = "TC-072"
        try:
            import psutil
            import os
            
            # Get initial memory usage
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Send multiple requests to simulate load
            async def send_request():
                payload = {
                    "message": "This is a load test message.",
                    "context": {
                        "document_content": "Test document content. " * 100,
                        "chat_history": "[]",
                        "available_tools": "text_analysis_tool"
                    }
                }
                return await http_client.post(f"{API_BASE}/mcp/chat", json=payload)
            
            # Send 10 concurrent requests
            tasks = [send_request() for _ in range(10)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Get memory usage after load
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Check if memory usage is reasonable
            memory_ok = memory_increase < 100  # Less than 100MB increase
            
            successful_responses = [r for r in responses if not isinstance(r, Exception) and r.status_code == 200]
            success_rate = len(successful_responses) / len(responses) * 100
            
            if memory_ok and success_rate >= 80:
                test_result.add_result(test_id, "PASS", {
                    "initial_memory_mb": initial_memory,
                    "final_memory_mb": final_memory,
                    "memory_increase_mb": memory_increase,
                    "success_rate": success_rate,
                    "memory_ok": memory_ok
                })
            else:
                test_result.add_result(test_id, "FAIL", {
                    "initial_memory_mb": initial_memory,
                    "final_memory_mb": final_memory,
                    "memory_increase_mb": memory_increase,
                    "success_rate": success_rate,
                    "memory_ok": memory_ok,
                    "message": "Memory usage too high or success rate too low"
                })
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e),
                "message": "Could not measure memory usage"
            })
            raise
    
    @pytest.mark.asyncio
    async def test_concurrent_user_simulation(self, http_client: httpx.AsyncClient, test_result):
        """TC-073: Concurrent User Simulation"""
        test_id = "TC-073"
        try:
            # Simulate multiple users
            async def user_session(user_id):
                responses = []
                for i in range(3):  # 3 requests per user
                    payload = {
                        "message": f"User {user_id} message {i}",
                        "context": {
                            "document_content": "",
                            "chat_history": "[]",
                            "available_tools": "text_analysis_tool"
                        }
                    }
                    response = await http_client.post(f"{API_BASE}/mcp/chat", json=payload)
                    responses.append(response)
                    await asyncio.sleep(0.1)  # Small delay between requests
                return responses
            
            # Simulate 5 concurrent users
            user_tasks = [user_session(i) for i in range(5)]
            user_responses = await asyncio.gather(*user_tasks, return_exceptions=True)
            
            # Analyze results
            total_requests = 0
            successful_requests = 0
            
            for user_response in user_responses:
                if not isinstance(user_response, Exception):
                    for response in user_response:
                        total_requests += 1
                        if response.status_code == 200:
                            successful_requests += 1
            
            success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
            
            if success_rate >= 90:
                test_result.add_result(test_id, "PASS", {
                    "total_requests": total_requests,
                    "successful_requests": successful_requests,
                    "success_rate": success_rate,
                    "concurrent_users": 5
                })
            else:
                test_result.add_result(test_id, "FAIL", {
                    "total_requests": total_requests,
                    "successful_requests": successful_requests,
                    "success_rate": success_rate,
                    "concurrent_users": 5,
                    "message": "Success rate too low for concurrent users"
                })
            
        except Exception as e:
            test_result.add_result(test_id, "FAIL", {
                "error": str(e)
            })
            raise
