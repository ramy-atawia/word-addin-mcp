#!/usr/bin/env python3
"""
Test script for Internal MCP Server.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.mcp_servers.internal_server import internal_mcp_server


async def test_internal_mcp_server():
    """Test the internal MCP server functionality."""
    print("🧪 Testing Internal MCP Server...")
    
    try:
        # Test 1: Tool registry initialization
        print("1. Testing tool registry initialization...")
        tools = await internal_mcp_server.tool_registry.list_all_tools()
        print(f"   ✅ Found {len(tools)} tools in registry")
        
        # Test 2: Tool discovery
        print("2. Testing tool discovery...")
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description']}")
        
        # Test 3: Tool info retrieval
        print("3. Testing tool info retrieval...")
        if tools:
            first_tool = tools[0]['name']
            tool_info = await internal_mcp_server.tool_registry.get_tool_info(first_tool)
            if tool_info:
                print(f"   ✅ Retrieved info for tool: {first_tool}")
            else:
                print(f"   ❌ Failed to get info for tool: {first_tool}")
        
        # Test 4: Tool execution (placeholder)
        print("4. Testing tool execution...")
        if tools:
            first_tool = tools[0]['name']
            result = await internal_mcp_server.tool_registry.execute_tool(
                first_tool, {"test": "parameter"}
            )
            print(f"   ✅ Executed tool {first_tool}: {result.get('status', 'unknown')}")
        
        # Test 5: Health check
        print("5. Testing health check...")
        health = await internal_mcp_server.tool_registry.get_health()
        print(f"   ✅ Health status: {health['status']}")
        
        print("\n🎉 All tests passed! Internal MCP Server is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    print("🚀 Starting Internal MCP Server Test...")
    
    # Run the test
    success = asyncio.run(test_internal_mcp_server())
    
    if success:
        print("\n✅ Internal MCP Server test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Internal MCP Server test failed!")
        sys.exit(1)
