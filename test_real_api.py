#!/usr/bin/env python3
"""
Test real API call to show actual patent search output
"""

import asyncio
import httpx
import json
import os

async def test_real_api():
    """Test real API call to show actual patent search output."""
    print("🔍 Testing real API call for patent search")
    print("=" * 60)
    
    # Use the dev backend URL
    backend_url = "https://novitai-word-mcp-backend-dev.azurewebsites.net"
    api_endpoint = f"{backend_url}/api/v1/mcp/agent/chat"
    
    # Test payload
    payload = {
        "message": "prior art search 5G AI",
        "session_id": "real-api-test"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"📡 Calling API: {api_endpoint}")
    print(f"📝 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(api_endpoint, headers=headers, json=payload)
            
            print(f"\n📊 Status Code: {response.status_code}")
            
            if response.is_success:
                response_json = response.json()
                response_text = response_json.get("response", "")
                
                print(f"📏 Response length: {len(response_text)} characters")
                print(f"\n📄 REAL API RESPONSE:")
                print("="*80)
                print(response_text)
                print("="*80)
                
                # Check if it's a comprehensive report
                if "Comprehensive Prior Art Search Report" in response_text:
                    print("\n✅ Generated comprehensive patent search report!")
                elif "patent" in response_text.lower():
                    print("\n✅ Generated patent-related response!")
                else:
                    print("\n❌ Response doesn't appear to be patent search related")
                    
            else:
                print(f"❌ API request failed with status {response.status_code}")
                print(f"📄 Error response: {response.text}")
                
    except httpx.RequestError as e:
        print(f"❌ HTTP Request Error: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON Decode Error: {e}")
        print(f"📄 Raw response: {response.text}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_real_api())
