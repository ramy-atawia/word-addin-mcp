#!/usr/bin/env python3
"""
Debug the full context pipeline to see where it's failing
"""

import requests
import json
import time

# Configuration
BASE_URL = "https://novitai-word-mcp-backend-dev.azurewebsites.net"
AUTH0_DOMAIN = "dev-bktskx5kbc655wcl.us.auth0.com"
CLIENT_ID = "INws849yDXaC6MZVXnLhMJi6CZC4nx6U"
CLIENT_SECRET = "6zJAq0NxHolRkOsIWvGj9J4ZCORcv67llEug1ZC_5K28O3S1pLrMPfCVudYDoV7o"
AUDIENCE = "INws849yDXaC6MZVXnLhMJi6CZC4nx6U"

def get_auth_token():
    """Get Auth0 token for API access."""
    try:
        response = requests.post(
            f"https://{AUTH0_DOMAIN}/oauth/token",
            headers={"Content-Type": "application/json"},
            json={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "audience": AUDIENCE,
                "grant_type": "client_credentials"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print(f"❌ Auth0 token request failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Auth0 token request error: {e}")
        return None

def test_query_with_history(message, token, chat_history=None, session_id="debug-pipeline"):
    """Test a query with conversation history."""
    try:
        request_data = {
            "message": message,
            "session_id": session_id,
            "context": {
                "document_content": "",
                "chat_history": json.dumps(chat_history) if chat_history else "",
                "available_tools": ""
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/mcp/agent/chat",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            },
            json=request_data,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"❌ Query failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Query error: {e}")
        return None

def main():
    print("🔍 Debug Full Context Pipeline")
    print("=" * 50)
    
    # Get token
    token = get_auth_token()
    if not token:
        print("❌ Failed to get token")
        return
    
    print("✅ Token obtained")
    
    # Step 1: Get web search result
    print(f"\n📝 Step 1: 'web search ramy atawia'")
    result1 = test_query_with_history("web search ramy atawia", token)
    
    if not result1 or not result1.get("success"):
        print("❌ Web search failed")
        return
    
    web_search_response = result1.get('response', '')
    print(f"✅ Web search successful")
    print(f"   Response length: {len(web_search_response)}")
    print(f"   Contains 'Ramy': {'ramy' in web_search_response.lower()}")
    print(f"   Contains 'Atawia': {'atawia' in web_search_response.lower()}")
    
    # Step 2: Test with conversation history
    chat_history = [
        {
            "role": "user",
            "content": "web search ramy atawia"
        },
        {
            "role": "assistant", 
            "content": web_search_response
        }
    ]
    
    print(f"\n📝 Step 2: 'draft 1 system claim' (with history)")
    print(f"   Chat history: {len(chat_history)} messages")
    print(f"   Assistant message length: {len(chat_history[1]['content'])}")
    
    result2 = test_query_with_history("draft 1 system claim", token, chat_history)
    
    if result2 and result2.get("success"):
        print("✅ Draft claim successful")
        print(f"   Intent: {result2.get('intent_type')}")
        print(f"   Tool: {result2.get('tool_name')}")
        print(f"   Response length: {len(result2.get('response', ''))}")
        
        # Check for context
        response_text = result2.get('response', '')
        print(f"\n🔍 Context Analysis:")
        print(f"   Contains 'Ramy': {'ramy' in response_text.lower()}")
        print(f"   Contains 'Atawia': {'atawia' in response_text.lower()}")
        print(f"   Contains 'research': {'research' in response_text.lower()}")
        print(f"   Contains 'analysis': {'analysis' in response_text.lower()}")
        
        if 'ramy' in response_text.lower() or 'atawia' in response_text.lower():
            print("   ✅ SUCCESS: Context found in response!")
        else:
            print("   ❌ FAILED: No context found in response")
            print(f"\n📄 Full response:")
            print(f"   {response_text}")
    else:
        print("❌ Draft claim failed")
        if result2:
            print(f"   Error: {result2.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()

