#!/usr/bin/env python3
"""
Quick test script to verify Google Search integration is working.
"""

import requests
import json
import time

def test_google_search():
    """Test the Google Search tool via API."""
    print("🧪 Testing Google Search Integration...")
    
    # Wait a moment for server to be ready
    time.sleep(2)
    
    url = "http://localhost:9000/api/v1/mcp/tools/web_search_tool/execute"
    headers = {"Content-Type": "application/json"}
    
    test_cases = [
        {"query": "latest AI developments 2024", "max_results": 3},
        {"query": "machine learning news", "max_results": 2}
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: Searching for '{test_case['query']}'")
        
        payload = {
            "tool_name": "web_search_tool",
            "parameters": test_case
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("status") == "success":
                    search_result = result.get("result", {})
                    results = search_result.get("results", [])
                    source = search_result.get("source", "Unknown")
                    
                    print(f"✅ Success! Found {len(results)} results from {source}")
                    
                    for j, item in enumerate(results[:2], 1):
                        title = item.get("title", "No title")[:80] + "..."
                        url = item.get("url", "No URL")
                        print(f"   {j}. {title}")
                        print(f"      🔗 {url}")
                        
                    if len(results) > 2:
                        print(f"   ... and {len(results)-2} more results")
                        
                else:
                    print(f"❌ Tool execution failed: {result}")
                    
            else:
                print(f"❌ HTTP Error {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection Error: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n🎉 Google Search test completed!")

if __name__ == "__main__":
    test_google_search()
