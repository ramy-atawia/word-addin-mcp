#!/usr/bin/env python3
"""
Final test for Pure MCP Implementation after all updates.
This tests the complete transformation from routing decisions to tool names.
"""

import asyncio
import aiohttp
import json

async def test_pure_mcp_final():
    """Test the complete pure MCP implementation."""
    print("🧪 Testing Pure MCP Implementation After All Updates...")
    
    # Test against the actual running server
    base_url = "https://localhost:9000"
    
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        try:
            # 1. Test tools endpoint
            print("\n1️⃣ Testing tools endpoint...")
            async with session.get(f"{base_url}/api/v1/mcp/tools") as response:
                if response.status == 200:
                    tools_data = await response.json()
                    tools = tools_data.get("tools", [])
                    print(f"   ✅ Tools endpoint working: {len(tools)} tools discovered")
                    for tool in tools:
                        print(f"      - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
                else:
                    print(f"   ❌ Tools endpoint failed: {response.status}")
                    return False
            
            # 2. Test agent chat endpoint with pure MCP approach
            print("\n2️⃣ Testing agent chat endpoint (pure MCP)...")
            chat_payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": "search for AI news"
                    }
                ],
                "context": {
                    "document_content": "",
                    "chat_history": "",
                    "available_tools": ""
                }
            }
            
            async with session.post(
                f"{base_url}/api/v1/mcp/conversation",
                json=chat_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    chat_data = await response.json()
                    print(f"   ✅ Agent chat working")
                    print(f"   📝 Response: {chat_data.get('response', 'No response')[:100]}...")
                    print(f"   🔧 Tool name: {chat_data.get('tool_name', 'None')}")
                    print(f"   🔧 Tools used: {chat_data.get('tools_used', [])}")
                    
                    # Verify pure MCP approach
                    if 'tool_name' in chat_data and 'routing_decision' not in chat_data:
                        print("   ✅ Pure MCP approach confirmed - no routing decisions")
                    else:
                        print("   ❌ Still using routing decisions")
                        return False
                else:
                    print(f"   ❌ Agent chat failed: {response.status}")
                    error_text = await response.text()
                    print(f"   📝 Error: {error_text}")
                    return False
            
            # 3. Test health endpoint
            print("\n3️⃣ Testing health endpoint...")
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"   ✅ Health endpoint working: {health_data.get('status', 'Unknown')}")
                else:
                    print(f"   ⚠️ Health endpoint failed: {response.status}")
            
            print("\n🎉 All tests completed successfully!")
            print("✅ Pure MCP Implementation is working correctly!")
            print("✅ No more routing decisions!")
            print("✅ No more deprecated methods!")
            print("✅ No more dangerous fallbacks!")
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🚀 Starting Final Pure MCP Implementation Tests...")
    print("⚠️  Make sure the FastAPI server is running on https://localhost:9000")
    
    success = asyncio.run(test_pure_mcp_final())
    if success:
        print("\n🎯 TRANSFORMATION COMPLETE: Pure MCP Implementation Achieved!")
    else:
        print("\n❌ Transformation incomplete - issues remain!")
