#!/usr/bin/env python3
"""
Manual test script for streaming endpoint.

Run this to test the streaming endpoint manually:
python test_streaming_manual.py
"""

import requests
import json
import time

def test_streaming_endpoint():
    """Test the streaming endpoint manually."""
    print("🧪 Manual Streaming Endpoint Test")
    print("=" * 50)
    
    # Test data
    test_data = {
        "message": "Hello, can you help me with patent research?",
        "context": {
            "document_content": "Test document content about AI patents",
            "chat_history": "[]",
            "available_tools": "web_search,prior_art_search,claim_drafting"
        }
    }
    
    print(f"📝 Testing with message: '{test_data['message']}'")
    print(f"📄 Document content: '{test_data['context']['document_content']}'")
    print(f"🔧 Available tools: {test_data['context']['available_tools']}")
    print()
    
    try:
        # Make streaming request
        print("🚀 Making streaming request to: http://localhost:9000/api/v1/mcp/agent/chat/stream")
        response = requests.post(
            "http://localhost:9000/api/v1/mcp/agent/chat/stream",
            json=test_data,
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            },
            stream=True,
            timeout=30
        )
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📊 Response headers: {dict(response.headers)}")
        print()
        
        if response.status_code != 200:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response content: {response.text}")
            return False
        
        print("📡 Streaming events:")
        print("-" * 50)
        
        # Process streaming response
        event_count = 0
        start_time = time.time()
        
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                try:
                    event_data = line[6:]  # Remove 'data: ' prefix
                    if event_data.strip():
                        event = json.loads(event_data)
                        event_count += 1
                        elapsed = time.time() - start_time
                        
                        print(f"[{elapsed:.2f}s] Event {event_count}: {event['event_type']}")
                        
                        # Show event data
                        data = event.get('data', {})
                        if 'message' in data:
                            print(f"    Message: {data['message']}")
                        if 'node' in data:
                            print(f"    Node: {data['node']}")
                        if 'content' in data:
                            print(f"    Content: {data['content'][:100]}...")
                        
                        print()
                        
                        # Stop after reasonable number of events or completion
                        if (event_count > 50 or 
                            event['event_type'] in ['workflow_complete', 'workflow_error', 'stream_error']):
                            break
                            
                except json.JSONDecodeError as e:
                    print(f"⚠️  Failed to parse event: {e}")
                    print(f"    Raw line: {line}")
                    continue
        
        elapsed_total = time.time() - start_time
        print("-" * 50)
        print(f"✅ Streaming test completed in {elapsed_total:.2f}s")
        print(f"📊 Total events received: {event_count}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Manual Streaming Test")
    print("Make sure the backend is running on http://localhost:9000")
    print()
    
    success = test_streaming_endpoint()
    
    if success:
        print("\n🎉 Manual test completed successfully!")
    else:
        print("\n❌ Manual test failed!")
    
    exit(0 if success else 1)
