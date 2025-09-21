#!/usr/bin/env python3
"""
Specific test for the "Hi" scenario with proper conversation history values.
This simulates the exact scenario where user says "Hi" after previous tool workflows.
"""

import requests
import json
import time

def test_hi_with_conversation_history():
    """Test 'Hi' with realistic conversation history containing tool workflows."""
    print("🧪 Testing 'Hi' with Proper Conversation History")
    print("=" * 50)
    
    # Simulate a realistic conversation history with tool workflows
    conversation_history = [
        {
            "role": "user", 
            "content": "web search ramy atawia", 
            "timestamp": time.time() - 300
        },
        {
            "role": "assistant", 
            "content": "Search the web for information:\n\nWeb Search Results for: ramy atawia\n1. Ramy Atawia - Thomson Reuters | LinkedIn\n2. Ramy Atawia - Google Scholar\n3. Ramy ATAWIA | Doctor of Philosophy | R&D | Research profile\n\nInsert to Word", 
            "timestamp": time.time() - 290
        },
        {
            "role": "user", 
            "content": "Insert to Word", 
            "timestamp": time.time() - 280
        },
        {
            "role": "assistant", 
            "content": "Content inserted to Word document successfully.", 
            "timestamp": time.time() - 270
        }
    ]
    
    print(f"📚 Conversation history contains {len(conversation_history)} messages")
    print("📝 Previous messages:")
    for i, msg in enumerate(conversation_history, 1):
        print(f"   {i}. {msg['role']}: {msg['content'][:50]}...")
    
    # Test data with the conversation history
    test_data = {
        "message": "Hi",
        "context": {
            "document_content": "This is a test document with some content about patent research and AI technology.",
            "chat_history": json.dumps(conversation_history),
            "available_tools": "web_search_tool,prior_art_search_tool,claim_drafting_tool,claim_analysis_tool"
        }
    }
    
    print(f"\n🔍 Testing: '{test_data['message']}'")
    print(f"📄 Document content: {len(test_data['context']['document_content'])} chars")
    print(f"🔧 Available tools: {test_data['context']['available_tools']}")
    
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
            return False
        
        # Process events
        tool_events = []
        conversation_events = []
        final_response = ""
        all_events = []
        
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                try:
                    event = json.loads(line[6:])
                    all_events.append(event)
                    event_type = event.get('event_type', '')
                    
                    # Count actual tool execution events
                    if ('tool' in event_type.lower() and 'complete' not in event_type.lower()) or \
                       ('langgraph_chunk' in event_type and 'tool_execution' in str(event.get('data', {}))):
                        tool_events.append(event)
                    elif event_type == 'llm_response':
                        final_response = event.get('data', {}).get('content', '')
                        conversation_events.append(event)
                    
                except json.JSONDecodeError:
                    continue
        
        # Analyze results
        print(f"\n📊 Analysis:")
        print(f"🔧 Tool events: {len(tool_events)}")
        print(f"💬 Conversation events: {len(conversation_events)}")
        print(f"📡 Total events: {len(all_events)}")
        print(f"📝 Final response: {final_response}")
        
        # Check for tool execution
        if len(tool_events) > 0:
            print(f"❌ FAILED: Tools were executed for 'Hi'")
            print(f"   Tool events: {[e.get('event_type') for e in tool_events]}")
            return False
        else:
            print(f"✅ PASSED: No tools executed for 'Hi'")
            
        # Check response quality
        if "hi" in final_response.lower() or "hello" in final_response.lower():
            print(f"✅ PASSED: Response contains appropriate greeting")
        else:
            print(f"⚠️  WARNING: Response doesn't contain greeting words")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_hi_without_history():
    """Test 'Hi' without any conversation history."""
    print("\n🧪 Testing 'Hi' without Conversation History")
    print("=" * 50)
    
    test_data = {
        "message": "Hi",
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
            return False
        
        # Count tool events
        tool_events = []
        final_response = ""
        
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                try:
                    event = json.loads(line[6:])
                    event_type = event.get('event_type', '')
                    if ('tool' in event_type.lower() and 'complete' not in event_type.lower()) or \
                       ('langgraph_chunk' in event_type and 'tool_execution' in str(event.get('data', {}))):
                        tool_events.append(event)
                    elif event_type == 'llm_response':
                        final_response = event.get('data', {}).get('content', '')
                except json.JSONDecodeError:
                    continue
        
        print(f"🔧 Tool events: {len(tool_events)}")
        print(f"📝 Final response: {final_response}")
        
        if len(tool_events) > 0:
            print(f"❌ FAILED: Tools executed for 'Hi' without history")
            return False
        else:
            print(f"✅ PASSED: No tools executed for 'Hi' without history")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing 'Hi' Scenario with Proper Conversation History")
    print("Make sure backend is running on localhost:9000")
    print()
    
    success1 = test_hi_with_conversation_history()
    success2 = test_hi_without_history()
    
    if success1 and success2:
        print("\n🎉 All 'Hi' scenario tests passed!")
        print("✅ 'Hi' is properly handled as CONVERSATION intent")
        print("✅ Conversation history with tool workflows doesn't interfere")
        print("✅ System responds appropriately to greetings")
    else:
        print("\n❌ Some 'Hi' scenario tests failed!")
        print("❌ 'Hi' may still be triggering tool workflows")
    
    exit(0 if (success1 and success2) else 1)
