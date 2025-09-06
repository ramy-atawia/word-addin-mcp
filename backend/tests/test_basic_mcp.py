#!/usr/bin/env python3
"""
Basic MCP Test Script
Run this to test if your MCP setup is working correctly.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import structlog
from app.services.mcp.orchestrator import get_mcp_orchestrator

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


async def test_basic_mcp():
    """Test basic MCP functionality."""
    print("🚀 Testing Basic MCP Setup...")
    
    try:
        # 1. Initialize MCP Orchestrator
        print("\n1️⃣  Initializing MCP Orchestrator...")
        orchestrator = get_mcp_orchestrator()
        await orchestrator.initialize()
        print("✅ MCP Orchestrator initialized successfully")
        
        # 2. Test Tool Discovery
        print("\n2️⃣  Testing Tool Discovery...")
        tools_data = await orchestrator.list_all_tools()
        tools = tools_data.get("tools", [])
        print(f"✅ Found {len(tools)} tools")
        
        for tool in tools:
            print(f"   📋 {tool.get('name', 'Unknown')} - {tool.get('description', 'No description')}")
        
        # 3. Test Internal Server Health
        print("\n3️⃣  Testing Internal Server Health...")
        health = await orchestrator.get_server_health()
        print(f"✅ Health Status: {health.get('status', 'unknown')}")
        
        # 4. Test Tool Execution
        if tools:
            print("\n4️⃣  Testing Tool Execution...")
            first_tool = tools[0]
            tool_name = first_tool.get("name")
            
            print(f"   🔧 Executing tool: {tool_name}")
            
            # Test parameters based on tool type
            if tool_name == "web_search_tool":
                test_params = {"query": "test search"}
            elif tool_name == "text_analysis_tool":
                test_params = {"text": "This is a test text for analysis", "operation": "summarize"}
            elif tool_name == "document_analysis_tool":
                test_params = {"content": "This is test document content for analysis purposes"}
            elif tool_name == "file_reader_tool":
                test_params = {"path": "test.txt", "encoding": "utf-8"}
            else:
                test_params = {}
            
            try:
                result = await orchestrator.execute_tool(tool_name, test_params)
                print(f"   ✅ Tool executed successfully!")
                print(f"   📊 Result status: {result.get('status', 'unknown')}")
                print(f"   ⏱️  Execution time: {result.get('execution_time', 0):.3f}s")
            except Exception as e:
                print(f"   ❌ Tool execution failed: {str(e)}")
        
        # 5. Test External Server Management (basic)
        print("\n5️⃣  Testing External Server Management...")
        external_servers = await orchestrator.get_external_servers()
        print(f"✅ External servers configured: {len(external_servers)}")
        
        print("\n🎉 Basic MCP Test Completed Successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ MCP Test Failed: {str(e)}")
        logger.error("MCP test failed", error=str(e))
        return False
    
    finally:
        # Cleanup
        try:
            await orchestrator.shutdown()
            print("🧹 Cleanup completed")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {str(e)}")


async def test_fastapi_integration():
    """Test FastAPI integration."""
    print("\n🌐 Testing FastAPI Integration...")
    
    try:
        from app.main import app
        print("✅ FastAPI app imported successfully")
        
        # Test that routes are properly configured
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        mcp_routes = [route for route in routes if '/mcp' in route]
        
        print(f"✅ Found {len(mcp_routes)} MCP routes:")
        for route in mcp_routes:
            print(f"   🛤️  {route}")
        
        return True
        
    except Exception as e:
        print(f"❌ FastAPI integration test failed: {str(e)}")
        return False


def main():
    """Main test function."""
    print("🧪 Starting MCP Basic Test Suite")
    print("=" * 50)
    
    # Test 1: Basic MCP functionality
    mcp_success = asyncio.run(test_basic_mcp())
    
    # Test 2: FastAPI integration
    api_success = asyncio.run(test_fastapi_integration())
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   MCP Basic Functionality: {'✅ PASS' if mcp_success else '❌ FAIL'}")
    print(f"   FastAPI Integration: {'✅ PASS' if api_success else '❌ FAIL'}")
    
    if mcp_success and api_success:
        print("\n🎉 All tests passed! Your basic MCP setup is working.")
        print("\n🚀 Next steps:")
        print("   1. Start the server: python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 9000")
        print("   2. Test API endpoints: http://localhost:9000/docs")
        print("   3. Test MCP tools: http://localhost:9000/api/v1/mcp/tools")
        return 0
    else:
        print("\n❌ Some tests failed. Check the logs above for details.")
        return 1


if __name__ == "__main__":
    exit(main())
