#!/usr/bin/env python3
"""
Simple streaming API test for prior art search with "prior art search 5G ai"
"""

import requests
import json
import time

def test_prior_art_streaming():
    """Test the prior art search streaming API directly."""
    print("🔍 Testing Prior Art Search Streaming API: 'prior art search 5G ai'")
    print("=" * 60)
    
    # API endpoint
    url = "https://novitai-word-mcp-backend-dev.azurewebsites.net/api/v1/mcp/agent/chat/stream"
    
    # Request payload
    payload = {
        "message": "prior art search 5G ai",
        "session_id": "test-simple"
    }
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    try:
        print("🔍 Sending streaming request to API...")
        print(f"📡 URL: {url}")
        print(f"📝 Payload: {json.dumps(payload, indent=2)}")
        
        # Make the streaming request
        start_time = time.time()
        response = requests.post(url, json=payload, headers=headers, timeout=120, stream=True)
        end_time = time.time()
        
        print(f"✅ Request completed!")
        print(f"📊 Status Code: {response.status_code}")
        print(f"⏱️  Response Time: {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            print("📡 Streaming response received:")
            print("-" * 50)
            
            full_response = ""
            event_count = 0
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    print(f"📨 Event: {line_str}")
                    
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])  # Remove 'data: ' prefix
                            event_count += 1
                            
                            if 'eventType' in data:
                                event_type = data['eventType']
                                print(f"  📊 Event Type: {event_type}")
                                
                                if event_type in ['llm_response', 'workflow_complete']:
                                    if 'content' in data:
                                        content = data['content']
                                        full_response += content
                                        print(f"  📄 Content: {content[:100]}...")
                                        
                        except json.JSONDecodeError:
                            print(f"  ❌ Invalid JSON: {line_str}")
            
            print("-" * 50)
            print(f"📊 Total events received: {event_count}")
            print(f"📏 Full response length: {len(full_response)}")
            
            if full_response:
                print(f"\n📄 Full Response Preview (first 500 chars):")
                print("-" * 50)
                print(full_response[:500])
                if len(full_response) > 500:
                    print("... [truncated]")
                print("-" * 50)
                
                # Check if it looks like a comprehensive report
                if any(keyword in full_response.lower() for keyword in 
                       ['executive summary', 'patent', 'analysis', 'findings', 'recommendations', 'comprehensive']):
                    print("✅ Response appears to be a comprehensive report!")
                else:
                    print("❌ Response appears to be basic/generic")
            else:
                print("❌ No content received in streaming response")
                
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
    test_prior_art_streaming()
