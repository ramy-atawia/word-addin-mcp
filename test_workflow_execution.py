#!/usr/bin/env python3
"""
Test actual workflow execution with mock tool responses
"""
import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.langgraph_agent_unified import get_agent_graph

async def test_workflow_execution_with_mocks():
    """Test workflow execution with mocked tool responses"""
    print("🧪 Testing Workflow Execution with Mocked Responses")
    print("=" * 60)
    
    # Mock the MCP orchestrator
    mock_orchestrator = AsyncMock()
    mock_orchestrator.execute_tool = AsyncMock()
    
    # Mock tool responses
    mock_orchestrator.execute_tool.side_effect = [
        # First call - prior art search
        {
            "success": True,
            "result": "**Prior Art Search Report**\n\nFound 15 relevant patents for 5G AI technology...",
            "tool_name": "prior_art_search_tool"
        },
        # Second call - claim drafting
        {
            "success": True,
            "result": "**Draft Claims**\n\n1. A method for 5G AI handover comprising...\n2. A system for intelligent 5G network management...",
            "tool_name": "claim_drafting_tool"
        }
    ]
    
    # Mock the agent service to return our mock orchestrator
    with MagicMock() as mock_agent_service:
        mock_agent_service._get_mcp_orchestrator.return_value = mock_orchestrator
        
        # Patch the agent service import
        import app.services.langgraph_agent_unified as langgraph_module
        original_import = langgraph_module.AgentService
        langgraph_module.AgentService = MagicMock(return_value=mock_agent_service)
        
        try:
            # Test the workflow
            state = {
                "user_input": "prior art search 5g ai, draft 2 claims",
                "document_content": "",
                "conversation_history": [],
                "available_tools": [
                    {"name": "prior_art_search_tool", "description": "Search for prior art patents"},
                    {"name": "claim_drafting_tool", "description": "Draft patent claims"}
                ],
                "selected_tool": "",
                "intent_type": "",
                "tool_parameters": {},
                "workflow_plan": None,
                "current_step": 0,
                "total_steps": 0,
                "step_results": {},
                "final_response": "",
                "success": False,
                "execution_time": 0.0
            }
            
            print("Executing workflow with mocked responses...")
            graph = get_agent_graph()
            result = await graph.ainvoke(state)
            
            print(f"\n📊 Workflow Execution Results:")
            print(f"Intent type: {result.get('intent_type')}")
            print(f"Final response length: {len(result.get('final_response', ''))}")
            print(f"Workflow plan steps: {len(result.get('workflow_plan', []))}")
            print(f"Step results: {list(result.get('step_results', {}).keys())}")
            print(f"Success: {result.get('success')}")
            
            # Check if both tools were called
            assert mock_orchestrator.execute_tool.call_count == 2, f"Expected 2 tool calls, got {mock_orchestrator.execute_tool.call_count}"
            
            # Check if the final response contains both results
            final_response = result.get('final_response', '')
            assert 'Prior Art Search Report' in final_response, "Prior art results not in final response"
            assert 'Draft Claims' in final_response, "Claim drafting results not in final response"
            
            print("\n✅ Workflow execution test passed!")
            print("Both tools were called and results were combined correctly.")
            
        finally:
            # Restore original import
            langgraph_module.AgentService = original_import

async def test_error_handling():
    """Test error handling in workflow execution"""
    print("\n🚨 Testing Error Handling")
    print("=" * 40)
    
    # Mock orchestrator that fails on first tool
    mock_orchestrator = AsyncMock()
    mock_orchestrator.execute_tool = AsyncMock()
    mock_orchestrator.execute_tool.side_effect = [
        # First call fails
        Exception("Tool execution failed"),
        # Second call succeeds
        {
            "success": True,
            "result": "**Draft Claims**\n\n1. A method for error recovery...",
            "tool_name": "claim_drafting_tool"
        }
    ]
    
    with MagicMock() as mock_agent_service:
        mock_agent_service._get_mcp_orchestrator.return_value = mock_orchestrator
        
        import app.services.langgraph_agent_unified as langgraph_module
        original_import = langgraph_module.AgentService
        langgraph_module.AgentService = MagicMock(return_value=mock_agent_service)
        
        try:
            state = {
                "user_input": "prior art search 5g ai, draft 2 claims",
                "document_content": "",
                "conversation_history": [],
                "available_tools": [
                    {"name": "prior_art_search_tool", "description": "Search for prior art patents"},
                    {"name": "claim_drafting_tool", "description": "Draft patent claims"}
                ],
                "selected_tool": "",
                "intent_type": "",
                "tool_parameters": {},
                "workflow_plan": None,
                "current_step": 0,
                "total_steps": 0,
                "step_results": {},
                "final_response": "",
                "success": False,
                "execution_time": 0.0
            }
            
            print("Testing error handling with first tool failure...")
            graph = get_agent_graph()
            result = await graph.ainvoke(state)
            
            print(f"\n📊 Error Handling Results:")
            print(f"Intent type: {result.get('intent_type')}")
            print(f"Final response: {result.get('final_response', '')[:200]}...")
            print(f"Step results: {result.get('step_results', {})}")
            
            # Check if error was handled gracefully
            step_results = result.get('step_results', {})
            has_error = any('error' in key for key in step_results.keys())
            assert has_error, "Error should be recorded in step results"
            
            print("\n✅ Error handling test passed!")
            print("Tool failure was handled gracefully.")
            
        finally:
            langgraph_module.AgentService = original_import

async def test_single_tool_vs_multi_step():
    """Test that single tool commands don't trigger multi-step workflow"""
    print("\n🔍 Testing Single Tool vs Multi-Step Detection")
    print("=" * 50)
    
    test_cases = [
        {
            "input": "prior art search for 5g technology",
            "expected_multi_step": False,
            "description": "Single prior art search"
        },
        {
            "input": "draft 5 claims for AI system",
            "expected_multi_step": False,
            "description": "Single claim drafting"
        },
        {
            "input": "web search for blockchain patents",
            "expected_multi_step": False,
            "description": "Single web search"
        },
        {
            "input": "prior art search 5g ai, draft 2 claims",
            "expected_multi_step": True,
            "description": "Multi-step command"
        }
    ]
    
    for test_case in test_cases:
        state = {
            "user_input": test_case["input"],
            "document_content": "",
            "conversation_history": [],
            "available_tools": [
                {"name": "prior_art_search_tool", "description": "Search for prior art patents"},
                {"name": "claim_drafting_tool", "description": "Draft patent claims"},
                {"name": "web_search_tool", "description": "Search the web"}
            ],
            "selected_tool": "",
            "intent_type": "",
            "tool_parameters": {},
            "workflow_plan": None,
            "current_step": 0,
            "total_steps": 0,
            "step_results": {},
            "final_response": "",
            "success": False,
            "execution_time": 0.0
        }
        
        try:
            graph = get_agent_graph()
            result = await graph.ainvoke(state)
            
            is_multi_step = result.get('intent_type') == 'multi_step'
            expected = test_case["expected_multi_step"]
            
            status = "✅ PASS" if is_multi_step == expected else "❌ FAIL"
            print(f"{status} {test_case['description']}: {is_multi_step} (expected: {expected})")
            
        except Exception as e:
            print(f"❌ FAIL {test_case['description']}: Exception - {str(e)}")

async def main():
    """Run all workflow execution tests"""
    print("🧪 Comprehensive Workflow Execution Testing")
    print("=" * 60)
    
    try:
        await test_workflow_execution_with_mocks()
        await test_error_handling()
        await test_single_tool_vs_multi_step()
        
        print("\n🎉 All workflow execution tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test suite failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
