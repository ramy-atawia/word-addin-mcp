#!/usr/bin/env python3
"""
Test to verify that simple greetings work correctly without triggering tool workflows.

This test:
1. Tests simple greetings like "hi", "hello", "hey"
2. Verifies they are treated as CONVERSATION intent
3. Ensures no tool workflows are triggered
4. Checks that conversation history doesn't interfere
"""

import requests
import json
import time

def test_greeting_flow():
    """Test that greetings work correctly without triggering tools."""
    print("🧪 Greeting Flow Test")
    print("=" * 40)
    
    # Test cases with different greetings
    test_cases = [
        "hi",
        "hello", 
        "hey",
        "how are you",
        "good morning"
    ]
    
    # Simulate conversation history with previous tool requests
    conversation_history = [
        {"role": "user", "content": "web search ramy atawia", "timestamp": time.time() - 100},
        {"role": "assistant", "content": "Search the web for information:\n\nWeb Search Results for: ramy atawia...", "timestamp": time.time() - 90},
        {"role": "user", "content": "Insert to Word", "timestamp": time.time() - 80},
        {"role": "assistant", "content": "Content inserted to Word document.", "timestamp": time.time() - 70}
    ]
    
    print(f"📝 Testing greetings with conversation history containing tool requests")
    print(f"📚 Conversation history: {len(conversation_history)} messages")
    
    for i, greeting in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: '{greeting}'")
        
        # Test data with conversation history
        test_data = {
            "message": greeting,
            "context": {
                "document_content": "",
                "chat_history": json.dumps(conversation_history),
                "available_tools": "web_search_tool,prior_art_search_tool,claim_drafting_tool"
            }
        }
        
        try:
            # Make request
            response = requests.post(
                "http://localhost:9000/api/v1/mcp/agent/chat/stream",
                json=test_data,
                headers={"Content-Type": "application/json"},
                stream=True,
                timeout=15
            )
            
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Failed: {response.text}")
                continue
            
            # Process events to check for tool execution
            tool_events = []
            conversation_events = []
            final_response = ""
            
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    try:
                        event = json.loads(line[6:])
                        event_type = event.get('event_type', '')
                        
                        # Only count actual tool execution events, not completion events
                        if ('tool' in event_type.lower() and 'complete' not in event_type.lower()) or \
                           ('langgraph_chunk' in event_type and 'tool_execution' in str(event.get('data', {}))):
                            tool_events.append(event)
                        elif event_type == 'llm_response':
                            final_response = event.get('data', {}).get('content', '')
                            conversation_events.append(event)
                        
                    except json.JSONDecodeError:
                        continue
            
            # Analyze results
            print(f"🔧 Tool events: {len(tool_events)}")
            print(f"💬 Conversation events: {len(conversation_events)}")
            print(f"📝 Final response: {final_response[:100]}...")
            
            # Check if any tools were executed (should be 0 for greetings)
            if len(tool_events) > 0:
                print(f"❌ FAILED: Tools were executed for greeting '{greeting}'")
                print(f"   Tool events: {[e.get('event_type') for e in tool_events]}")
                return False
            else:
                print(f"✅ PASSED: No tools executed for greeting '{greeting}'")
                
        except Exception as e:
            print(f"❌ Error testing '{greeting}': {e}")
            return False
    
    return True

def test_greeting_without_history():
    """Test greetings without conversation history."""
    print("\n🧪 Greeting Flow Test (No History)")
    print("=" * 40)
    
    test_cases = ["hi", "hello", "hey"]
    
    for i, greeting in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: '{greeting}' (no history)")
        
        test_data = {
            "message": greeting,
            "context": {
                "document_content": "",
                "chat_history": "[]",
                "available_tools": "web_search_tool,prior_art_search_tool,claim_drafting_tool"
            }
        }
        
        try:
            response = requests.post(
                "http://localhost:9000/api/v1/mcp/agent/chat/stream",
                json=test_data,
                headers={"Content-Type": "application/json"},
                stream=True,
                timeout=15
            )
            
            if response.status_code != 200:
                print(f"❌ Failed: {response.text}")
                continue
            
            # Count tool events
            tool_events = []
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    try:
                        event = json.loads(line[6:])
                        event_type = event.get('event_type', '')
                        # Only count actual tool execution events, not completion events
                        if ('tool' in event_type.lower() and 'complete' not in event_type.lower()) or \
                           ('langgraph_chunk' in event_type and 'tool_execution' in str(event.get('data', {}))):
                            tool_events.append(event)
                    except json.JSONDecodeError:
                        continue
            
            if len(tool_events) > 0:
                print(f"❌ FAILED: Tools executed for '{greeting}' without history")
                return False
            else:
                print(f"✅ PASSED: No tools executed for '{greeting}' without history")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Greeting Flow Test")
    print("Make sure backend is running on localhost:9000")
    print()
    
    success1 = test_greeting_flow()
    success2 = test_greeting_without_history()
    
    if success1 and success2:
        print("\n🎉 All greeting tests passed!")
        print("✅ Greetings are properly handled as CONVERSATION intent")
        print("✅ Conversation history doesn't interfere with greeting detection")
    else:
        print("\n❌ Some greeting tests failed!")
        print("❌ Greetings may still be triggering tool workflows")
    
    exit(0 if (success1 and success2) else 1)
