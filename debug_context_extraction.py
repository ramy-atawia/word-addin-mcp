#!/usr/bin/env python3
"""
Debug context extraction to see what keywords are found
"""

import requests
import json

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

def test_query_with_history(message, token, chat_history=None, session_id="debug-context"):
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
    print("🔍 Debug Context Extraction")
    print("=" * 40)
    
    # Get token
    token = get_auth_token()
    if not token:
        print("❌ Failed to get token")
        return
    
    print("✅ Token obtained")
    
    # Get web search result
    print(f"\n📝 Step 1: Get web search result")
    result1 = test_query_with_history("web search ramy atawia", token)
    
    if not result1 or not result1.get("success"):
        print("❌ Web search failed")
        return
    
    web_search_response = result1.get('response', '')
    print(f"✅ Web search successful")
    print(f"   Response length: {len(web_search_response)}")
    print(f"   Response preview: {web_search_response[:200]}...")
    
    # Check what keywords are present
    keywords = [
        'research', 'analysis', 'search results', 'findings', 'data', 'information',
        'comprehensive', 'executive summary', 'overview', 'report', 'results', 'patent'
    ]
    
    print(f"\n🔍 Checking for context extraction keywords:")
    found_keywords = []
    for keyword in keywords:
        if keyword in web_search_response.lower():
            found_keywords.append(keyword)
            print(f"   ✅ Found: '{keyword}'")
        else:
            print(f"   ❌ Missing: '{keyword}'")
    
    print(f"\n📊 Found {len(found_keywords)}/{len(keywords)} keywords: {found_keywords}")
    
    # Test context extraction manually
    print(f"\n🧪 Testing manual context extraction:")
    
    # Simulate the conversation history
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
    
    # Simulate the _extract_recent_tool_results function
    recent_tool_results = []
    for msg in chat_history[-5:]:  # Check last 5 messages
        if msg.get('role') == 'assistant':
            content = msg.get('content', '')
            if any(keyword in content.lower() for keyword in keywords):
                if len(content) > 1000:
                    content = content[:1000] + "... [truncated]"
                recent_tool_results.append(content)
                print(f"   ✅ Would extract: {len(content)} chars")
            else:
                print(f"   ❌ Would NOT extract: {len(content)} chars")
    
    print(f"\n📊 Context extraction result: {len(recent_tool_results)} tool results found")
    
    if recent_tool_results:
        print("   ✅ Context extraction should work")
    else:
        print("   ❌ Context extraction failed - no tool results found")

if __name__ == "__main__":
    main()

