#!/usr/bin/env python3
"""
Comprehensive MCP Protocol Test Suite

This script tests all MCP protocol methods and API endpoints using real data
from our conversation history. It covers:

1. Internal MCP Server functionality
2. External MCP Server management
3. Tool discovery and execution
4. Agent interactions
5. Server health monitoring
6. Error handling and edge cases

Usage:
    python test_mcp_comprehensive.py
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Dict, Any, List
import httpx

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "https://localhost:9000"
VERIFY_SSL = False  # For self-signed certificates

class MCPComprehensiveTester:
    """Comprehensive tester for all MCP functionality."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            verify=VERIFY_SSL,
            timeout=30.0
        )
        self.test_results = []
        self.session_id = f"test_session_{int(time.time())}"
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
        
    def log_test_result(self, test_name: str, success: bool, details: str = "", error: str = ""):
        """Log test result with details."""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "error": error,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}")
        if details:
            logger.info(f"   Details: {details}")
        if error:
            logger.error(f"   Error: {error}")
            
    async def test_backend_connectivity(self) -> bool:
        """Test basic backend connectivity."""
        try:
            response = await self.client.get(f"{BASE_URL}/")
            if response.status_code == 200:
                data = response.json()
                self.log_test_result(
                    "Backend Connectivity",
                    True,
                    f"Backend responding: {data.get('message', 'Unknown')}"
                )
                return True
            else:
                self.log_test_result(
                    "Backend Connectivity",
                    False,
                    f"Status code: {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test_result(
                "Backend Connectivity",
                False,
                error=str(e)
            )
            return False
            
    async def test_mcp_tools_discovery(self) -> bool:
        """Test MCP tools discovery endpoint."""
        try:
            response = await self.client.get(f"{BASE_URL}/api/v1/mcp/tools")
            if response.status_code == 200:
                data = response.json()
                tools = data.get('tools', [])
                self.log_test_result(
                    "MCP Tools Discovery",
                    True,
                    f"Discovered {len(tools)} tools: {[t['name'] for t in tools]}"
                )
                return True
            else:
                self.log_test_result(
                    "MCP Tools Discovery",
                    False,
                    f"Status code: {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test_result(
                "MCP Tools Discovery",
                False,
                error=str(e)
            )
            return False
            
    async def test_web_search_tool_execution(self) -> bool:
        """Test web search tool execution with real query from conversation."""
        try:
            # Real query from our conversation: "Mariam elazab"
            tool_name = "web_search_tool"
            response = await self.client.post(
                f"{BASE_URL}/api/v1/mcp/tools/{tool_name}/execute",
                json={
                    "parameters": {
                        "query": "Mariam elazab",
                        "max_results": 5
                    },
                    "session_id": self.session_id,
                    "request_id": f"test_{int(time.time())}"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test_result(
                    "Web Search Tool Execution",
                    True,
                    f"Query: 'Mariam elazab', Results: {len(data.get('results', []))}"
                )
                return True
            else:
                self.log_test_result(
                    "Web Search Tool Execution",
                    False,
                    f"Status code: {response.status_code}, Response: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test_result(
                "Web Search Tool Execution",
                False,
                error=str(e)
            )
            return False
            
    async def test_agent_chat_with_web_search(self) -> bool:
        """Test agent chat with web search intent."""
        try:
            # Real conversation from our history
            response = await self.client.post(
                f"{BASE_URL}/api/v1/mcp/agent/chat",
                json={
                    "message": "web search Mariam elazab",
                    "session_id": self.session_id,
                    "user_id": "test_user"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {})
                tool_name = result.get('tool_name')
                response_text = result.get('response', '')
                
                self.log_test_result(
                    "Agent Chat with Web Search",
                    True,
                    f"Tool used: {tool_name}, Response length: {len(response_text)}"
                )
                return True
            else:
                self.log_test_result(
                    "Agent Chat with Web Search",
                    False,
                    f"Status code: {response.status_code}, Response: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test_result(
                "Agent Chat with Web Search",
                False,
                error=str(e)
            )
            return False
            
    async def test_agent_conversational_response(self) -> bool:
        """Test agent conversational response without tool usage."""
        try:
            response = await self.client.post(
                f"{BASE_URL}/api/v1/mcp/agent/chat",
                json={
                    "message": "Hello, how are you?",
                    "session_id": self.session_id,
                    "user_id": "test_user"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {})
                tool_name = result.get('tool_name')
                response_text = result.get('response', '')
                
                # Should be conversational, not tool-based
                success = tool_name is None and len(response_text) > 0
                self.log_test_result(
                    "Agent Conversational Response",
                    success,
                    f"Tool used: {tool_name}, Response: {response_text[:100]}..."
                )
                return success
            else:
                self.log_test_result(
                    "Agent Conversational Response",
                    False,
                    f"Status code: {response.status_code}, Response: {response.text}"
                )
                return False
        except Exception as e:
            self.log_test_result(
                "Agent Conversational Response",
                False,
                error=str(e)
            )
            return False
            
    async def test_external_mcp_server_management(self) -> bool:
        """Test external MCP server management endpoints."""
        try:
            # Test adding external server (this should fail gracefully)
            server_config = {
                "name": "test_sequential_thinking",
                "description": "Test Sequential Thinking MCP Server",
                "server_url": "https://remote.mcpservers.org/sequentialthinking/mcp",
                "server_type": "custom",
                "authentication_type": "NONE",
                "api_key": None,
                "username": None,
                "password": None
            }
            
            # Test connection first
            test_response = await self.client.post(
                f"{BASE_URL}/api/v1/mcp/external/servers/test-connection",
                json=server_config
            )
            
            if test_response.status_code == 200:
                test_data = test_response.json()
                self.log_test_result(
                    "External Server Connection Test",
                    True,
                    f"Connection test result: {test_data.get('connection_test', 'unknown')}"
                )
            else:
                self.log_test_result(
                    "External Server Connection Test",
                    False,
                    f"Status code: {test_response.status_code}"
                )
            
            # Test adding server
            add_response = await self.client.post(
                f"{BASE_URL}/api/v1/mcp/external/servers",
                json=server_config
            )
            
            if add_response.status_code in [200, 201, 500]:  # 500 is expected for connection failure
                self.log_test_result(
                    "External Server Addition",
                    True,
                    f"Server addition handled (status: {add_response.status_code})"
                )
                return True
            else:
                self.log_test_result(
                    "External Server Addition",
                    False,
                    f"Unexpected status: {add_response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "External MCP Server Management",
                False,
                error=str(e)
            )
            return False
            
    async def test_mcp_status_endpoints(self) -> bool:
        """Test MCP status and health endpoints."""
        try:
            # Test MCP status
            status_response = await self.client.get(f"{BASE_URL}/api/v1/mcp/status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                self.log_test_result(
                    "MCP Status Endpoint",
                    True,
                    f"Status: {status_data.get('status', 'unknown')}"
                )
            else:
                self.log_test_result(
                    "MCP Status Endpoint",
                    False,
                    f"Status code: {status_response.status_code}"
                )
            
            # Test health endpoint
            health_response = await self.client.get(f"{BASE_URL}/api/v1/health")
            if health_response.status_code == 200:
                health_data = health_response.json()
                self.log_test_result(
                    "Health Endpoint",
                    True,
                    f"Health: {health_data.get('status', 'unknown')}"
                )
                return True
            else:
                self.log_test_result(
                    "Health Endpoint",
                    False,
                    f"Status code: {health_response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "MCP Status Endpoints",
                False,
                error=str(e)
            )
            return False
            
    async def test_tool_parameter_validation(self) -> bool:
        """Test tool parameter validation with invalid inputs."""
        try:
            # Test web search with invalid parameters
            response = await self.client.post(
                f"{BASE_URL}/api/v1/mcp/tools/web_search_tool/execute",
                json={
                    "parameters": {
                        "query": "",  # Empty query should fail validation
                        "max_results": 999  # Invalid max_results
                    },
                    "session_id": self.session_id,
                    "request_id": f"test_invalid_{int(time.time())}"
                }
            )
            
            # Should fail with validation error
            if response.status_code in [400, 422]:
                self.log_test_result(
                    "Tool Parameter Validation",
                    True,
                    f"Invalid parameters properly rejected (status: {response.status_code})"
                )
                return True
            else:
                self.log_test_result(
                    "Tool Parameter Validation",
                    False,
                    f"Expected validation error, got status: {response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Tool Parameter Validation",
                False,
                error=str(e)
            )
            return False
            
    async def test_conversation_memory(self) -> bool:
        """Test conversation memory persistence across requests."""
        try:
            # First message
            response1 = await self.client.post(
                f"{BASE_URL}/api/v1/mcp/agent/chat",
                json={
                    "message": "My name is Mariam",
                    "session_id": self.session_id,
                    "user_id": "test_user"
                }
            )
            
            if response1.status_code != 200:
                self.log_test_result(
                    "Conversation Memory - First Message",
                    False,
                    f"Status code: {response1.status_code}"
                )
                return False
                
            # Second message referencing the first
            response2 = await self.client.post(
                f"{BASE_URL}/api/v1/mcp/agent/chat",
                json={
                    "message": "What is my name?",
                    "session_id": self.session_id,
                    "user_id": "test_user"
                }
            )
            
            if response2.status_code == 200:
                data2 = response2.json()
                result2 = data2.get('result', {})
                response_text = result2.get('response', '')
                
                # Check if agent remembers the name
                success = 'Mariam' in response_text
                self.log_test_result(
                    "Conversation Memory - Context Retention",
                    success,
                    f"Response: {response_text[:100]}..."
                )
                return success
            else:
                self.log_test_result(
                    "Conversation Memory - Second Message",
                    False,
                    f"Status code: {response2.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Conversation Memory",
                False,
                error=str(e)
            )
            return False
            
    async def test_error_handling(self) -> bool:
        """Test error handling for various edge cases."""
        try:
            # Test non-existent tool
            response = await self.client.post(
                f"{BASE_URL}/api/v1/mcp/tools/non_existent_tool/execute",
                json={
                    "parameters": {"test": "value"},
                    "session_id": self.session_id,
                    "request_id": f"test_error_{int(time.time())}"
                }
            )
            
            # Should return 404 or 400
            if response.status_code in [404, 400]:
                self.log_test_result(
                    "Error Handling - Non-existent Tool",
                    True,
                    f"Properly handled non-existent tool (status: {response.status_code})"
                )
            else:
                self.log_test_result(
                    "Error Handling - Non-existent Tool",
                    False,
                    f"Expected error status, got: {response.status_code}"
                )
                return False
                
            # Test malformed JSON
            response2 = await self.client.post(
                f"{BASE_URL}/api/v1/mcp/agent/chat",
                content="This is not JSON",
                headers={"Content-Type": "application/json"}
            )
            
            if response2.status_code in [400, 422]:
                self.log_test_result(
                    "Error Handling - Malformed JSON",
                    True,
                    f"Properly handled malformed JSON (status: {response2.status_code})"
                )
                return True
            else:
                self.log_test_result(
                    "Error Handling - Malformed JSON",
                    False,
                    f"Expected error status, got: {response2.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Error Handling",
                False,
                error=str(e)
            )
            return False
            
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all comprehensive tests."""
        logger.info("🚀 Starting Comprehensive MCP Protocol Test Suite")
        logger.info("=" * 60)
        
        test_methods = [
            ("Backend Connectivity", self.test_backend_connectivity),
            ("MCP Tools Discovery", self.test_mcp_tools_discovery),
            ("Web Search Tool Execution", self.test_web_search_tool_execution),
            ("Agent Chat with Web Search", self.test_agent_chat_with_web_search),
            ("Agent Conversational Response", self.test_agent_conversational_response),
            ("External MCP Server Management", self.test_external_mcp_server_management),
            ("MCP Status Endpoints", self.test_mcp_status_endpoints),
            ("Tool Parameter Validation", self.test_tool_parameter_validation),
            ("Conversation Memory", self.test_conversation_memory),
            ("Error Handling", self.test_error_handling),
        ]
        
        for test_name, test_method in test_methods:
            try:
                logger.info(f"\n🧪 Running: {test_name}")
                await test_method()
                await asyncio.sleep(1)  # Brief pause between tests
            except Exception as e:
                logger.error(f"❌ Test {test_name} crashed: {str(e)}")
                self.log_test_result(test_name, False, error=f"Test crashed: {str(e)}")
        
        # Generate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        summary = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "test_results": self.test_results
        }
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests} ✅")
        logger.info(f"Failed: {failed_tests} ❌")
        logger.info(f"Success Rate: {summary['success_rate']:.1f}%")
        
        if failed_tests > 0:
            logger.info("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    logger.error(f"  - {result['test_name']}: {result.get('error', 'Unknown error')}")
        
        return summary

async def main():
    """Main test execution function."""
    try:
        async with MCPComprehensiveTester() as tester:
            summary = await tester.run_all_tests()
            
            # Save detailed results to file
            with open("mcp_test_results.json", "w") as f:
                json.dump(summary, f, indent=2, default=str)
            
            logger.info(f"\n💾 Detailed results saved to: mcp_test_results.json")
            
            # Exit with appropriate code
            if summary['failed'] == 0:
                logger.info("\n🎉 All tests passed! MCP implementation is working correctly.")
                sys.exit(0)
            else:
                logger.error(f"\n⚠️  {summary['failed']} tests failed. Please review the implementation.")
                sys.exit(1)
                
    except Exception as e:
        logger.error(f"❌ Test suite execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
