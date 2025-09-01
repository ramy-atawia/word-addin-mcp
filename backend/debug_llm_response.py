#!/usr/bin/env python3
"""
Debug script to test LLM response parsing and see what's happening.
"""

import asyncio
import aiohttp
import json

async def debug_llm_response():
    """Debug the LLM response to see what's happening."""
    print("🔍 Debugging LLM Response Parsing...")
    
    base_url = "https://localhost:9000"
    
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        try:
            # Test with a simple search request
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
            
            print("📤 Sending request to agent chat...")
            async with session.post(
                f"{base_url}/api/v1/mcp/conversation",
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
                    else:
                        print("✅ routing_decision removed from response")
                    
                    # Check if tool_name is properly set
                    if chat_data.get('tool_name'):
                        print("✅ tool_name is properly set")
                    else:
                        print("❌ tool_name is None or empty")
                        
                else:
                    print(f"❌ Request failed: {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text}")
                    
        except Exception as e:
            print(f"❌ Debug failed: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting LLM Response Debug...")
    print("⚠️  Make sure the FastAPI server is running on https://localhost:9000")
    
    asyncio.run(debug_llm_response())
