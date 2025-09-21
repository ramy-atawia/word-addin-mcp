#!/usr/bin/env python3
"""
Test that single tool requests now work as multi-step workflows (1-step).
This verifies that the architectural change is working correctly.
"""

import requests
import json
import time

def test_single_tool_as_multistep():
    """Test that single tool requests are handled as 1-step multi-step workflows."""
    print("🧪 Testing Single Tool as Multi-Step Workflow")
    print("=" * 50)
    
    # Test cases for single tool requests
    test_cases = [
        {
            "message": "search for AI patents",
            "expected_tool": "prior_art_search_tool",
            "description": "Prior art search"
        },
        {
            "message": "draft 5 claims for blockchain",
            "expected_tool": "claim_drafting_tool", 
            "description": "Claim drafting"
        },
        {
            "message": "web search machine learning",
            "expected_tool": "web_search_tool",
            "description": "Web search"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: '{test_case['message']}'")
        print(f"📝 Expected: {test_case['description']}")
        
        test_data = {
            "message": test_case["message"],
            "context": {
                "document_content": "",
                "chat_history": "[]",
                "available_tools": "web_search_tool,prior_art_search_tool,claim_drafting_tool,claim_analysis_tool"
            }
        }
        
        try:
            response = requests.post(
                "http://localhost:9000/api/v1/mcp/agent/chat/stream",
                json=test_data,
                headers={"Content-Type": "application/json"},
                stream=True,
                timeout=20
            )
            
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Failed: {response.text}")
                continue
            
            # Process events
            tool_events = []
            final_response = ""
            workflow_events = []
            all_events = []
            
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith('data: '):
                    try:
                        event = json.loads(line[6:])
                        all_events.append(event)
                        event_type = event.get('event_type', '')
                        
                        if 'tool' in event_type.lower() and 'complete' not in event_type.lower():
                            tool_events.append(event)
                        elif event_type == 'llm_response':
                            final_response = event.get('data', {}).get('content', '')
                        elif 'langgraph_chunk' in event_type:
                            workflow_events.append(event)
                            # Check if this langgraph_chunk contains tool execution
                            data = event.get('data', {})
                            if 'updates' in data and 'updates' in data['updates']:
                                updates = data['updates']['updates']
                                if 'tool_execution' in updates:
                                    tool_events.append(event)
                        
                    except json.JSONDecodeError:
                        continue
            
            # Analyze results
            print(f"🔧 Tool events: {len(tool_events)}")
            print(f"📡 Workflow events: {len(workflow_events)}")
            print(f"📡 Total events: {len(all_events)}")
            print(f"📝 Final response: {final_response[:100]}...")
            
            # Debug: Show event types
            event_types = [e.get('event_type', 'unknown') for e in all_events]
            print(f"🔍 Event types: {event_types}")
            
            # Check if tools were executed (should be > 0 for tool requests)
            if len(tool_events) > 0:
                print(f"✅ PASSED: Tools executed for '{test_case['message']}'")
                print(f"   Tool events: {[e.get('event_type') for e in tool_events]}")
            else:
                print(f"❌ FAILED: No tools executed for '{test_case['message']}'")
                return False
                
        except Exception as e:
            print(f"❌ Error testing '{test_case['message']}': {e}")
            return False
    
    return True

def test_multistep_workflow():
    """Test that multi-step workflows still work correctly."""
    print("\n🧪 Testing Multi-Step Workflow")
    print("=" * 50)
    
    test_data = {
        "message": "web search AI patents then draft 3 claims",
        "context": {
            "document_content": "",
            "chat_history": "[]",
            "available_tools": "web_search_tool,prior_art_search_tool,claim_drafting_tool,claim_analysis_tool"
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:9000/api/v1/mcp/agent/chat/stream",
            json=test_data,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=25
        )
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Failed: {response.text}")
            return False
        
        # Process events
        tool_events = []
        final_response = ""
        
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                try:
                    event = json.loads(line[6:])
                    event_type = event.get('event_type', '')
                    
                    if 'tool' in event_type.lower() and 'complete' not in event_type.lower():
                        tool_events.append(event)
                    elif event_type == 'llm_response':
                        final_response = event.get('data', {}).get('content', '')
                    elif 'langgraph_chunk' in event_type:
                        # Check if this langgraph_chunk contains tool execution
                        data = event.get('data', {})
                        if 'updates' in data and 'updates' in data['updates']:
                            updates = data['updates']['updates']
                            if 'tool_execution' in updates:
                                tool_events.append(event)
                    
                except json.JSONDecodeError:
                    continue
        
        print(f"🔧 Tool events: {len(tool_events)}")
        print(f"📝 Final response: {final_response[:100]}...")
        
        # Multi-step should have tool events (at least 1, ideally more)
        if len(tool_events) > 0:
            print(f"✅ PASSED: Multi-step workflow executed ({len(tool_events)} tool events)")
            # Check if response contains both search and draft content
            if "search" in final_response.lower() and "claim" in final_response.lower():
                print(f"✅ PASSED: Response contains both search and claim content")
            else:
                print(f"⚠️  WARNING: Response may not contain both search and claim content")
            return True
        else:
            print(f"❌ FAILED: Multi-step workflow didn't execute properly")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Simplified Architecture (Single Tool as Multi-Step)")
    print("Make sure backend is running on localhost:9000")
    print()
    
    success1 = test_single_tool_as_multistep()
    success2 = test_multistep_workflow()
    
    if success1 and success2:
        print("\n🎉 All tests passed!")
        print("✅ Single tool requests work as 1-step multi-step workflows")
        print("✅ Multi-step workflows still work correctly")
        print("✅ Architecture simplification successful")
    else:
        print("\n❌ Some tests failed!")
        print("❌ Architecture changes may have issues")
    
    exit(0 if (success1 and success2) else 1)
