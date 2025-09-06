#!/usr/bin/env python3
"""
Test script for the Custom MCP Client implementation.

This script tests connection to the Sequential Thinking MCP server.
"""

import asyncio
import logging
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.fastmcp_client import FastMCPClientFactory

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_sequential_thinking_server():
    """Test connection to the Sequential Thinking MCP server."""
    server_url = "https://remote.mcpservers.org/sequentialthinking/mcp"
    
    print(f"🚀 Testing Custom MCP Client with {server_url}")
    print("=" * 60)
    
    try:
        # Create HTTP client
        client = FastMCPClientFactory.create_http_client(
            server_url=server_url,
            server_name="Sequential Thinking",
            timeout=30
        )
        
        print(f"✅ MCP Client created successfully")
        
        # Test connection
        print(f"🔗 Attempting to connect...")
        async with client:
            print(f"✅ Connected successfully!")
            
            # Get connection status
            status = client.get_stats()
            print(f"📊 Connection Status:")
            for key, value in status.items():
                print(f"   {key}: {value}")
            
            # Test health check
            print(f"\n🏥 Testing health check...")
            is_healthy = await client.health_check()
            print(f"✅ Health check: {'PASSED' if is_healthy else 'FAILED'}")
            
            # Discover tools
            print(f"\n🔍 Discovering tools...")
            tools = await client.list_tools()
            print(f"✅ Found {len(tools)} tool(s):")
            
            for i, tool in enumerate(tools, 1):
                print(f"   {i}. {tool.get('name', 'Unknown')} - {tool.get('description', 'No description')}")
                if 'inputSchema' in tool:
                    schema = tool['inputSchema']
                    if isinstance(schema, dict) and 'properties' in schema:
                        props = schema['properties']
                        print(f"      Parameters: {list(props.keys())}")
            
            # Test tool execution if tools are available
            if tools:
                tool_to_test = tools[0]
                tool_name = tool_to_test.get('name')
                
                if tool_name:
                    print(f"\n🔧 Testing tool execution: {tool_name}")
                    try:
                        # Try with minimal parameters
                        result = await client.execute_tool(tool_name, {
                            "thought": "Test thought from Custom MCP Client",
                            "nextThoughtNeeded": False,
                            "thoughtNumber": 1,
                            "totalThoughts": 1
                        })
                        print(f"✅ Tool execution successful!")
                        print(f"📄 Result: {result}")
                        
                    except Exception as tool_error:
                        print(f"⚠️ Tool execution failed: {tool_error}")
                        
                        # Try with no parameters
                        try:
                            print(f"🔧 Retrying with no parameters...")
                            result = await client.execute_tool(tool_name, {})
                            print(f"✅ Tool execution successful!")
                            print(f"📄 Result: {result}")
                        except Exception as retry_error:
                            print(f"❌ Tool execution failed again: {retry_error}")
            
            print(f"\n🎉 Test completed successfully!")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_basic_functionality():
    """Test basic functionality of the Custom MCP Client."""
    print(f"\n🧪 Testing Basic Functionality")
    print("=" * 40)
    
    try:
        # Test client creation
        client = FastMCPClientFactory.create_http_client(
            "https://httpbin.org/get",
            "Test Server"
        )
        print(f"✅ HTTP client creation successful")
        
        # Test connection status before connection
        status = client.get_stats()
        print(f"📊 Status before connection: {status['state']}")
        
        print(f"✅ Basic functionality test passed")
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Custom MCP Client Test Suite")
    print("=" * 60)
    
    asyncio.run(test_basic_functionality())
    asyncio.run(test_sequential_thinking_server())
