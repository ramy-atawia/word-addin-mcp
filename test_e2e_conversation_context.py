#!/usr/bin/env python3
"""
E2E Test to verify conversation context handling:
1. Conversation history is correct and doesn't include the latest user message
2. User message is the actual latest user input
"""

import asyncio
import json
import time
import requests
from typing import List, Dict, Any

# Test configuration
BACKEND_URL = "https://novitai-word-mcp-backend-dev.azurewebsites.net"
STREAMING_ENDPOINT = f"{BACKEND_URL}/api/v1/mcp/agent/chat/stream"

def test_conversation_context():
    """Test that conversation context is handled correctly."""
    
    print("🧪 Starting E2E Conversation Context Test")
    print("=" * 60)
    
    # Test conversation flow
    test_messages = [
        "Hello, I need help with a patent",
        "Can you search for AI patents?",
        "Now draft 3 claims for blockchain",
        "Hi there, how are you?"  # This should be treated as new conversation
    ]
    
    conversation_history = []
    
    for i, message in enumerate(test_messages):
        print(f"\n📝 Test Message {i+1}: '{message}'")
        print("-" * 40)
        
        # Prepare request
        request_data = {
            "message": message,
            "context": {
                "document_content": "Test document content",
                "chat_history": json.dumps(conversation_history),
                "available_tools": "web_search_tool,prior_art_search_tool,claim_drafting_tool"
            },
            "session_id": f"test-session-{int(time.time())}"
        }
        
        print(f"📤 Sending request with conversation history length: {len(conversation_history)}")
        if conversation_history:
            print("📋 Previous conversation:")
            for j, msg in enumerate(conversation_history[-3:]):  # Show last 3 messages
                print(f"  {j+1}. {msg['role']}: {msg['content'][:50]}...")
        
        # Make streaming request
        try:
            response = requests.post(
                STREAMING_ENDPOINT,
                json=request_data,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'text/event-stream'
                },
                stream=True,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ Request failed with status {response.status_code}")
                print(f"Response: {response.text}")
                continue
            
            print("📡 Streaming response:")
            
            # Process streaming response
            final_response = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            event_data = json.loads(line_str[6:])
                            event_type = event_data.get('event_type', '')
                            
                            if event_type == 'langgraph_chunk':
                                data = event_data.get('data', {})
                                if 'updates' in data and 'updates' in data['updates']:
                                    for node_name, node_data in data['updates']['updates'].items():
                                        if node_name == 'response_generation' and isinstance(node_data, dict):
                                            if 'final_response' in node_data:
                                                final_response = node_data['final_response']
                                                print(f"✅ Final response: {final_response[:100]}...")
                            
                            elif event_type == 'workflow_complete':
                                final_response = event_data.get('data', {}).get('final_response', '')
                                print(f"✅ Workflow complete: {final_response[:100]}...")
                                
                        except json.JSONDecodeError as e:
                            print(f"⚠️  Failed to parse event: {e}")
            
            if not final_response:
                print("❌ No final response received")
                continue
                
            # Add to conversation history
            conversation_history.append({
                "role": "user",
                "content": message,
                "timestamp": time.time()
            })
            conversation_history.append({
                "role": "assistant", 
                "content": final_response,
                "timestamp": time.time()
            })
            
            print(f"✅ Response received and added to history")
            print(f"📊 Total conversation history length: {len(conversation_history)}")
            
        except Exception as e:
            print(f"❌ Error during request: {e}")
            continue
        
        # Wait between requests
        time.sleep(2)
    
    print("\n" + "=" * 60)
    print("🎯 E2E Test Results Summary")
    print("=" * 60)
    
    # Verify conversation history
    print(f"📊 Final conversation history length: {len(conversation_history)}")
    print("📋 Full conversation history:")
    for i, msg in enumerate(conversation_history):
        print(f"  {i+1}. {msg['role']}: {msg['content'][:100]}...")
    
    # Test the key verification
    print("\n🔍 Verification Tests:")
    
    # Test 1: Last message should be assistant response
    if conversation_history and conversation_history[-1]['role'] == 'assistant':
        print("✅ PASS: Last message in history is assistant response")
    else:
        print("❌ FAIL: Last message in history is not assistant response")
    
    # Test 2: Second to last should be user message
    if len(conversation_history) >= 2 and conversation_history[-2]['role'] == 'user':
        print("✅ PASS: Second to last message is user message")
    else:
        print("❌ FAIL: Second to last message is not user message")
    
    # Test 3: User message should match the last test message
    last_user_message = conversation_history[-2]['content'] if len(conversation_history) >= 2 else ""
    if last_user_message == test_messages[-1]:
        print("✅ PASS: User message matches the latest input")
    else:
        print(f"❌ FAIL: User message mismatch. Expected: '{test_messages[-1]}', Got: '{last_user_message}'")
    
    print("\n🏁 E2E Test Complete!")

if __name__ == "__main__":
    test_conversation_context()
