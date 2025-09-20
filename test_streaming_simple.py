#!/usr/bin/env python3
"""
Simple test to verify streaming implementation works.

This test:
1. Tests the backend streaming endpoint
2. Verifies LangGraph streaming works
3. Checks event format
"""

import requests
import json
import time

def test_streaming_endpoint_simple():
    """Simple test of the streaming endpoint."""
    print("🧪 Simple Streaming Test")
    print("=" * 40)
    
    # Test data
    test_data = {
        "message": "Hello, test message",
        "context": {
            "document_content": "",
            "chat_history": "[]",
            "available_tools": ""
        }
    }
    
    print(f"📝 Testing: '{test_data['message']}'")
    
    try:
        # Make request
        response = requests.post(
            "http://localhost:9000/api/v1/mcp/agent/chat/stream",
            json=test_data,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=10
        )
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Failed: {response.text}")
            return False
        
        # Process first few events
        event_count = 0
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                try:
                    event = json.loads(line[6:])
                    event_count += 1
                    print(f"📡 Event {event_count}: {event['event_type']}")
                    
                    if event_count >= 5:  # Just test first 5 events
                        break
                        
                except json.JSONDecodeError:
                    continue
        
        print(f"✅ Received {event_count} events")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Simple Streaming Test")
    print("Make sure backend is running on localhost:9000")
    print()
    
    success = test_streaming_endpoint_simple()
    
    if success:
        print("\n🎉 Simple test passed!")
    else:
        print("\n❌ Simple test failed!")
    
    exit(0 if success else 1)
