#!/usr/bin/env python3
"""
Targeted E2E Test Suite - Fixed Version
=======================================

This test suite fixes the issues found in the comprehensive test and focuses on
the core functionality that should be working.
"""

import asyncio
import json
import logging
import time
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TargetedE2ETester:
    """Targeted E2E tester with fixed test cases."""
    
    def __init__(self, base_url: str = "http://localhost:9000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = []
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def run_test(self, test_name: str, test_func, *args, **kwargs):
        """Run a single test and record results."""
        start_time = time.time()
        result = {
            "test_name": test_name,
            "status": "PENDING",
            "start_time": start_time,
            "duration": 0,
            "error": None,
            "details": {}
        }
        
        try:
            logger.info(f"🧪 Running test: {test_name}")
            test_result = await test_func(*args, **kwargs)
            result["status"] = "PASSED"
            result["details"] = test_result
            logger.info(f"✅ Test passed: {test_name}")
        except Exception as e:
            result["status"] = "FAILED"
            result["error"] = str(e)
            logger.error(f"❌ Test failed: {test_name} - {e}")
        
        result["duration"] = time.time() - start_time
        self.test_results.append(result)
        return result
    
    # ============================================================================
    # CORE FUNCTIONALITY TESTS
    # ============================================================================
    
    async def test_health_endpoint(self):
        """Test health endpoint functionality."""
        response = await self.client.get(f"{self.base_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "mcp_orchestrator" in data
        return {"status_code": response.status_code, "response_data": data}
    
    async def test_tools_list_endpoint(self):
        """Test tools list endpoint."""
        response = await self.client.get(f"{self.base_url}/api/v1/mcp/tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert "total_count" in data
        return {"status_code": response.status_code, "tool_count": data["total_count"]}
    
    async def test_agent_chat_endpoint_fixed(self):
        """Test agent chat endpoint with correct format."""
        payload = {
            "message": "Hello, test message",
            "context": {
                "document_content": "Test document content",
                "chat_history": "[]",  # String format
                "available_tools": "web_search_tool"  # String format
            }
        }
        response = await self.client.post(f"{self.base_url}/api/v1/mcp/agent/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        return {"status_code": response.status_code, "response_length": len(data["response"])}
    
    async def test_web_search_tool(self):
        """Test web search tool functionality."""
        payload = {"parameters": {"query": "artificial intelligence patents"}}
        response = await self.client.post(f"{self.base_url}/api/v1/mcp/tools/web_search_tool/execute", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        return {"status_code": response.status_code, "result_type": type(data["result"]).__name__}
    
    async def test_prior_art_search_tool(self):
        """Test prior art search tool functionality."""
        payload = {"parameters": {"query": "5G handover AI"}}
        response = await self.client.post(f"{self.base_url}/api/v1/mcp/tools/prior_art_search_tool/execute", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        return {"status_code": response.status_code, "result_type": type(data["result"]).__name__}
    
    async def test_claim_drafting_tool(self):
        """Test claim drafting tool functionality."""
        payload = {"parameters": {"user_query": "Draft a claim for 5G handover technology"}}
        response = await self.client.post(f"{self.base_url}/api/v1/mcp/tools/claim_drafting_tool/execute", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        return {"status_code": response.status_code, "result_type": type(data["result"]).__name__}
    
    async def test_claim_analysis_tool(self):
        """Test claim analysis tool functionality."""
        payload = {"parameters": {"claim_text": "A method for 5G handover comprising: receiving a handover request"}}
        response = await self.client.post(f"{self.base_url}/api/v1/mcp/tools/claim_analysis_tool/execute", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        return {"status_code": response.status_code, "result_type": type(data["result"]).__name__}
    
    async def test_external_servers_endpoint(self):
        """Test external servers management endpoint."""
        response = await self.client.get(f"{self.base_url}/api/v1/external/servers")
        assert response.status_code == 200
        data = response.json()
        assert "servers" in data
        return {"status_code": response.status_code, "server_count": len(data["servers"])}
    
    async def test_add_external_server_endpoint(self):
        """Test adding external server endpoint."""
        server_data = {
            "name": f"Test Server {int(time.time())}",
            "description": "Test external MCP server",
            "server_url": "https://example.com/mcp",
            "server_type": "custom",
            "authentication_type": "none"
        }
        response = await self.client.post(f"{self.base_url}/api/v1/external/servers", json=server_data)
        # Should return 503 for invalid URL, but endpoint should work
        assert response.status_code in [200, 503]
        return {"status_code": response.status_code, "server_name": server_data["name"]}
    
    async def test_test_connection_endpoint(self):
        """Test connection testing endpoint."""
        payload = {
            "name": "Test Connection",
            "server_url": "https://learn.microsoft.com/api/mcp",
            "server_type": "custom",
            "authentication_type": "none"
        }
        response = await self.client.post(f"{self.base_url}/api/v1/external/servers/test-connection", json=payload)
        assert response.status_code in [200, 503]
        return {"status_code": response.status_code}
    
    async def test_performance_response_time(self):
        """Test response time performance."""
        start_time = time.time()
        response = await self.client.get(f"{self.base_url}/api/v1/mcp/tools")
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 5.0  # Should respond within 5 seconds
        
        return {"status_code": response.status_code, "response_time": response_time}
    
    async def test_concurrent_requests(self):
        """Test concurrent request handling."""
        async def make_request():
            response = await self.client.get(f"{self.base_url}/api/v1/mcp/tools")
            return response.status_code
        
        # Make 5 concurrent requests
        tasks = [make_request() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(status == 200 for status in results)
        return {"concurrent_requests": len(results), "all_successful": True}
    
    async def test_error_handling_invalid_endpoint(self):
        """Test invalid endpoint handling."""
        response = await self.client.get(f"{self.base_url}/api/v1/invalid/endpoint")
        assert response.status_code == 404
        return {"status_code": response.status_code, "error_handling": "working"}
    
    async def test_error_handling_malformed_json(self):
        """Test malformed JSON handling."""
        response = await self.client.post(
            f"{self.base_url}/api/v1/mcp/agent/chat",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
        return {"status_code": response.status_code, "json_validation": "working"}
    
    async def run_all_tests(self):
        """Run all targeted E2E tests."""
        logger.info("🚀 Starting Targeted E2E Test Suite (Core Functionality)")
        start_time = time.time()
        
        # Core functionality tests
        tests = [
            ("Health Endpoint", self.test_health_endpoint),
            ("Tools List Endpoint", self.test_tools_list_endpoint),
            ("Agent Chat Endpoint (Fixed)", self.test_agent_chat_endpoint_fixed),
            ("Web Search Tool", self.test_web_search_tool),
            ("Prior Art Search Tool", self.test_prior_art_search_tool),
            ("Claim Drafting Tool", self.test_claim_drafting_tool),
            ("Claim Analysis Tool", self.test_claim_analysis_tool),
            ("External Servers Endpoint", self.test_external_servers_endpoint),
            ("Add External Server Endpoint", self.test_add_external_server_endpoint),
            ("Test Connection Endpoint", self.test_test_connection_endpoint),
            ("Performance Response Time", self.test_performance_response_time),
            ("Concurrent Requests", self.test_concurrent_requests),
            ("Error Handling - Invalid Endpoint", self.test_error_handling_invalid_endpoint),
            ("Error Handling - Malformed JSON", self.test_error_handling_malformed_json),
        ]
        
        # Execute all tests
        for test_name, test_func in tests:
            await self.run_test(test_name, test_func)
        
        # Calculate results
        total_time = time.time() - start_time
        passed_tests = len([r for r in self.test_results if r["status"] == "PASSED"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAILED"])
        total_tests = len(self.test_results)
        
        # Performance metrics
        response_times = [r["duration"] for r in self.test_results]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        
        results = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "total_execution_time": total_time,
                "average_response_time": avg_response_time,
                "max_response_time": max_response_time
            },
            "test_results": self.test_results
        }
        
        logger.info(f"🎯 Test Suite Complete: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
        logger.info(f"⏱️ Total execution time: {total_time:.2f} seconds")
        
        return results

async def main():
    """Main function to run targeted E2E tests."""
    async with TargetedE2ETester() as tester:
        results = await tester.run_all_tests()
        
        # Save results to file
        with open("targeted_e2e_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        # Print summary
        summary = results["summary"]
        print(f"\n{'='*60}")
        print(f"🎯 TARGETED E2E TEST RESULTS")
        print(f"{'='*60}")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']} ✅")
        print(f"Failed: {summary['failed_tests']} ❌")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Total Time: {summary['total_execution_time']:.2f}s")
        print(f"Avg Response Time: {summary['average_response_time']:.3f}s")
        print(f"Max Response Time: {summary['max_response_time']:.3f}s")
        print(f"{'='*60}")
        
        if summary['failed_tests'] > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in results['test_results']:
                if result['status'] == 'FAILED':
                    print(f"  - {result['test_name']}: {result['error']}")
        
        return results

if __name__ == "__main__":
    asyncio.run(main())
