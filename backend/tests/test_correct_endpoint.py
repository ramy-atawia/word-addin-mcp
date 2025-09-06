#!/usr/bin/env python3
"""
Test script for the correct endpoint that was actually updated.
"""

import asyncio
import aiohttp
import json

async def test_correct_endpoint():
    """Test the correct agent/chat endpoint."""
    print("🧪 Testing Correct Endpoint: /api/v1/mcp/agent/chat")
    
    base_url = "https://localhost:9000"
    
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        try:
            # Test the correct endpoint
            chat_payload = {
                "message": "search for AI news",
                "context": {
                    "document_content": "",
                    "chat_history": "",
                    "available_tools": ""
                }
            }
            
            print("📤 Sending request to /api/v1/mcp/agent/chat...")
            async with session.post(
                f"{base_url}/api/v1/mcp/agent/chat",
                json=chat_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    chat_data = await response.json()
                    print(f"📥 Response received:")
                    print(f"   Status: {response.status}")
                    print(f"   Response keys: {list(chat_data.keys())}")
                    print(f"   Tool name: {chat_data.get('tool_name')}")
                    print(f"   Tools used: {chat_data.get('tools_used')}")
                    print(f"   Intent type: {chat_data.get('intent_type')}")
                    print(f"   Reasoning: {chat_data.get('reasoning')}")
                    print(f"   Full response: {json.dumps(chat_data, indent=2)}")
                    
                    # Check if routing_decision still exists
                    if 'routing_decision' in chat_data:
                        print("❌ routing_decision still exists in response!")
                        return False
                    else:
                        print("✅ routing_decision removed from response")
                    
                    # Check if tool_name is properly set
                    if chat_data.get('tool_name'):
                        print("✅ tool_name is properly set")
                        return True
                    else:
                        print("❌ tool_name is None or empty")
                        return False
                        
                else:
                    print(f"❌ Request failed: {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🚀 Starting Correct Endpoint Test...")
    print("⚠️  Make sure the FastAPI server is running on https://localhost:9000")
    
    success = asyncio.run(test_correct_endpoint())
    if success:
        print("\n🎯 SUCCESS: Pure MCP Implementation Working!")
    else:
        print("\n❌ FAILURE: Issues remain!")
