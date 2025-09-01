#!/usr/bin/env python3
"""
Simple test script for MCPOrchestrator.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.mcp.orchestrator import mcp_orchestrator


async def test_mcp_orchestrator():
    """Test the MCP orchestrator functionality."""
    print("🧪 Testing MCP Orchestrator...")
    
    try:
        # Test initialization
        print("1. Testing initialization...")
        await mcp_orchestrator.initialize()
        print("   ✅ Initialization successful")
        
        # Test health check
        print("2. Testing health check...")
        health = await mcp_orchestrator.get_server_health()
        print(f"   ✅ Health status: {health['status']}")
        
        # Test tool listing
        print("3. Testing tool listing...")
        tools = await mcp_orchestrator.list_all_tools()
        print(f"   ✅ Found {tools['total_count']} tools")
        print(f"   ✅ Built-in tools: {tools['built_in_count']}")
        print(f"   ✅ External tools: {tools['external_count']}")
        
        print("\n🎉 All tests passed! MCP Orchestrator is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    print("🚀 Starting MCP Orchestrator Test...")
    
    # Run the test
    success = asyncio.run(test_mcp_orchestrator())
    
    if success:
        print("\n✅ MCP Orchestrator test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ MCP Orchestrator test failed!")
        sys.exit(1)
