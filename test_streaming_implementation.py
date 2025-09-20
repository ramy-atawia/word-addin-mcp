#!/usr/bin/env python3
"""
Test case for LangGraph streaming implementation.

This test verifies:
1. Backend streaming endpoint works
2. LangGraph native streaming functions correctly
3. Frontend can consume streaming events
4. End-to-end streaming flow works
"""

import asyncio
import json
import time
import requests
from typing import AsyncGenerator, Dict, Any
import sys
import os

# Add the backend to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_agent_service_streaming():
    """Test the agent service streaming method directly."""
    print("🧪 Testing Agent Service Streaming...")
    
    try:
        from app.services.agent import AgentService
        
        agent_service = AgentService()
        
        # Test data
        test_message = "Hello, can you help me with patent research?"
        test_context = {
            "document_content": "Test document content",
            "chat_history": "[]",
            "available_tools": "web_search,prior_art_search"
        }
        
        print(f"📝 Testing with message: '{test_message}'")
        
        # Collect streaming events
        events = []
        async for event in agent_service.process_user_message_streaming(
            user_message=test_message,
            document_content=test_context["document_content"],
            available_tools=[],
            frontend_chat_history=[]
        ):
            events.append(event)
            event_type = event.get('event_type', 'unknown')
            data = event.get('data', {})
            if isinstance(data, dict):
                message = data.get('message', 'No message')
            else:
                message = str(data)[:50] + "..." if len(str(data)) > 50 else str(data)
            print(f"📡 Event: {event_type} - {message}")
            
            # Stop after reasonable number of events or if we get an error
            if len(events) > 20 or event['event_type'] in ['workflow_error', 'workflow_complete']:
                break
        
        print(f"✅ Agent service streaming test completed. Received {len(events)} events.")
        return True
        
    except Exception as e:
        print(f"❌ Agent service streaming test failed: {e}")
        return False

def test_api_streaming_endpoint():
    """Test the streaming API endpoint."""
    print("\n🧪 Testing API Streaming Endpoint...")
    
    try:
        # Test data
        test_data = {
            "message": "Hello, can you help me with patent research?",
            "context": {
                "document_content": "Test document content",
                "chat_history": "[]",
                "available_tools": "web_search,prior_art_search"
            }
        }
        
        print(f"📝 Testing with message: '{test_data['message']}'")
        
        # Make streaming request
        response = requests.post(
            "http://localhost:8000/api/v1/mcp/agent/chat/stream",
            json=test_data,
            headers={"Content-Type": "application/json"},
            stream=True
        )
        
        if response.status_code != 200:
            print(f"❌ API request failed with status {response.status_code}")
            return False
        
        print("📡 Streaming response received:")
        
        # Process streaming response
        event_count = 0
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith('data: '):
                try:
                    event_data = line[6:]  # Remove 'data: ' prefix
                    if event_data.strip():
                        event = json.loads(event_data)
                        event_count += 1
                        event_type = event.get('event_type', 'unknown')
                        data = event.get('data', {})
                        if isinstance(data, dict):
                            message = data.get('message', 'No message')
                        else:
                            message = str(data)[:50] + "..." if len(str(data)) > 50 else str(data)
                        print(f"📡 Event {event_count}: {event_type} - {message}")
                        
                        # Stop after reasonable number of events
                        if event_count > 20:
                            break
                            
                except json.JSONDecodeError as e:
                    print(f"⚠️  Failed to parse event: {e}")
                    continue
        
        print(f"✅ API streaming test completed. Received {event_count} events.")
        return True
        
    except Exception as e:
        print(f"❌ API streaming test failed: {e}")
        return False

def test_frontend_streaming_service():
    """Test the frontend streaming service (simulated)."""
    print("\n🧪 Testing Frontend Streaming Service...")
    
    try:
        # Simulate the frontend streaming service
        import requests
        
        test_data = {
            "message": "Hello, can you help me with patent research?",
            "context": {
                "document_content": "Test document content",
                "chat_history": "[]",
                "available_tools": "web_search,prior_art_search"
            }
        }
        
        print(f"📝 Testing frontend streaming with message: '{test_data['message']}'")
        
        # Simulate the frontend fetch request
        response = requests.post(
            "http://localhost:8000/api/v1/mcp/agent/chat/stream",
            json=test_data,
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            },
            stream=True
        )
        
        if response.status_code != 200:
            print(f"❌ Frontend streaming request failed with status {response.status_code}")
            return False
        
        # Simulate the frontend streaming processing
        events = []
        buffer = ""
        
        for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
            buffer += chunk
            
            # Process complete lines
            lines = buffer.split('\n')
            buffer = lines.pop() or ''
            
            for line in lines:
                if line.startswith('data: '):
                    try:
                        event_data = line[6:]
                        if event_data.strip():
                            event = json.loads(event_data)
                            events.append(event)
                            print(f"📡 Frontend Event: {event['event_type']}")
                            
                            # Simulate frontend callbacks
                            if event['event_type'] == 'workflow_complete':
                                print("✅ Workflow completed successfully")
                                break
                            elif event['event_type'] in ['workflow_error', 'stream_error']:
                                print(f"❌ Workflow error: {event.get('data', {}).get('message', 'Unknown error')}")
                                break
                                
                    except json.JSONDecodeError as e:
                        print(f"⚠️  Failed to parse frontend event: {e}")
                        continue
        
        print(f"✅ Frontend streaming test completed. Processed {len(events)} events.")
        return True
        
    except Exception as e:
        print(f"❌ Frontend streaming test failed: {e}")
        return False

def test_langgraph_native_streaming():
    """Test LangGraph native streaming capabilities."""
    print("\n🧪 Testing LangGraph Native Streaming...")
    
    try:
        from app.services.langgraph_agent_unified import get_agent_graph
        
        # Get the LangGraph agent
        agent_graph = get_agent_graph()
        
        if not agent_graph:
            print("❌ LangGraph agent not available")
            return False
        
        print("📝 Testing LangGraph .astream() method...")
        
        # Test initial state
        initial_state = {
            "user_input": "Hello, test message",
            "document_content": "",
            "conversation_history": [],
            "available_tools": [],
            "selected_tool": "",
            "tool_parameters": {},
            "tool_result": None,
            "final_response": "",
            "intent_type": "",
            "workflow_plan": None,
            "current_step": 0,
            "total_steps": 0,
            "step_results": {}
        }
        
        # Test streaming
        chunk_count = 0
        async def test_streaming():
            nonlocal chunk_count
            async for chunk in agent_graph.astream(
                initial_state,
                stream_mode=["updates", "messages"]
            ):
                chunk_count += 1
                if isinstance(chunk, dict):
                    print(f"📡 LangGraph Chunk {chunk_count}: {list(chunk.keys())}")
                else:
                    print(f"📡 LangGraph Chunk {chunk_count}: {type(chunk)} - {chunk}")
                
                # Stop after reasonable number of chunks
                if chunk_count > 10:
                    break
        
        # Run the async test
        import asyncio
        asyncio.run(test_streaming())
        
        print(f"✅ LangGraph native streaming test completed. Received {chunk_count} chunks.")
        return True
        
    except Exception as e:
        print(f"❌ LangGraph native streaming test failed: {e}")
        return False

async def run_all_tests():
    """Run all streaming tests."""
    print("🚀 Starting LangGraph Streaming Implementation Tests\n")
    
    tests = [
        ("LangGraph Native Streaming", test_langgraph_native_streaming),
        ("Agent Service Streaming", test_agent_service_streaming),
        ("API Streaming Endpoint", test_api_streaming_endpoint),
        ("Frontend Streaming Service", test_frontend_streaming_service),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print('='*60)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Streaming implementation is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the implementation.")
    
    return passed == len(results)

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
