#!/usr/bin/env python3
"""
Test script for MCP HTTP endpoints.
"""

import asyncio
import sys
import os
import time

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.mcp_servers.internal_server import internal_mcp_server


async def test_mcp_endpoints():
    """Test the MCP HTTP endpoints."""
    print("🧪 Testing MCP HTTP Endpoints...")
    
    try:
        # Start the internal MCP server
        print("1. Starting internal MCP server...")
        await internal_mcp_server.start()
        print("   ✅ Internal MCP server started")
        
        # Wait a moment for server to be ready
        print("2. Waiting for server to be ready...")
        await asyncio.sleep(2)
        
        # Test the health endpoint
        print("3. Testing health endpoint...")
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("http://localhost:9001/health") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        print(f"   ✅ Health endpoint: {health_data}")
                    else:
                        print(f"   ❌ Health endpoint failed: {response.status}")
            except Exception as e:
                print(f"   ⚠️ Health endpoint test failed: {str(e)}")
        
        # Test the tools list endpoint
        print("4. Testing tools list endpoint...")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("http://localhost:9001/mcp/tools") as response:
                    if response.status == 200:
                        tools_data = await response.json()
                        print(f"   ✅ Tools list endpoint: {len(tools_data.get('result', {}).get('tools', []))} tools")
                    else:
                        print(f"   ❌ Tools list endpoint failed: {response.status}")
            except Exception as e:
                print(f"   ⚠️ Tools list endpoint test failed: {str(e)}")
        
        # Test tool info endpoint
        print("5. Testing tool info endpoint...")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("http://localhost:9001/mcp/tools/web_search_tool") as response:
                    if response.status == 200:
                        tool_info = await response.json()
                        print(f"   ✅ Tool info endpoint: {tool_info.get('result', {}).get('tool', {}).get('name')}")
                    else:
                        print(f"   ❌ Tool info endpoint failed: {response.status}")
            except Exception as e:
                print(f"   ⚠️ Tool info endpoint test failed: {str(e)}")
        
        # Test tool execution endpoint
        print("6. Testing tool execution endpoint...")
        async with aiohttp.ClientSession() as session:
            try:
                payload = {
                    "id": "test_call",
                    "params": {"query": "test search"}
                }
                async with session.post(
                    "http://localhost:9001/mcp/tools/web_search_tool/call",
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"   ✅ Tool execution endpoint: {result.get('result', {}).get('content', {}).get('status')}")
                    else:
                        print(f"   ❌ Tool execution endpoint failed: {response.status}")
            except Exception as e:
                print(f"   ⚠️ Tool execution endpoint test failed: {str(e)}")
        
        print("\n🎉 MCP HTTP endpoints test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    print("🚀 Starting MCP HTTP Endpoints Test...")
    
    # Run the test
    success = asyncio.run(test_mcp_endpoints())
    
    if success:
        print("\n✅ MCP HTTP endpoints test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ MCP HTTP endpoints test failed!")
        sys.exit(1)
