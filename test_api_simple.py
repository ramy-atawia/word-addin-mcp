#!/usr/bin/env python3
"""
Simple API test for prior art search with "prior art search 5G ai"
"""

import requests
import json
import time

def test_prior_art_api():
    """Test the prior art search API directly."""
    print("🔍 Testing Prior Art Search API: 'prior art search 5G ai'")
    print("=" * 60)
    
    # API endpoint
    url = "https://novitai-word-mcp-backend-dev.azurewebsites.net/api/v1/mcp/agent/chat"
    
    # Request payload
    payload = {
        "message": "prior art search 5G ai",
        "session_id": "test-simple"
    }
    
    # Headers
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print("🔍 Sending request to API...")
        print(f"📡 URL: {url}")
        print(f"📝 Payload: {json.dumps(payload, indent=2)}")
        
        # Make the request
        start_time = time.time()
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        end_time = time.time()
        
        print(f"✅ Request completed!")
        print(f"📊 Status Code: {response.status_code}")
        print(f"⏱️  Response Time: {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"📊 Response type: {type(result)}")
                
                if isinstance(result, dict):
                    print(f"📊 Response keys: {list(result.keys())}")
                    
                    if 'response' in result:
                        response_text = result['response']
                        print(f"📏 Response length: {len(response_text) if isinstance(response_text, str) else 'N/A'}")
                        
                        if isinstance(response_text, str) and response_text:
                            print(f"\n📄 Response preview (first 500 chars):")
                            print("-" * 50)
                            print(response_text[:500])
                            if len(response_text) > 500:
                                print("... [truncated]")
                            print("-" * 50)
                            
                            # Check if it looks like a comprehensive report
                            if any(keyword in response_text.lower() for keyword in 
                                   ['executive summary', 'patent', 'analysis', 'findings', 'recommendations', 'comprehensive']):
                                print("✅ Response appears to be a comprehensive report!")
                            else:
                                print("❌ Response appears to be basic/generic")
                        else:
                            print("❌ Empty or invalid response")
                    else:
                        print(f"❌ No 'response' key in result")
                        print(f"📄 Full result: {json.dumps(result, indent=2)}")
                else:
                    print(f"❌ Unexpected result type: {type(result)}")
                    print(f"📄 Result: {result}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"📄 Raw response: {response.text[:500]}...")
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"📄 Error response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 120 seconds")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_prior_art_api()
