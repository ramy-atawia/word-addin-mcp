"""
Tests for unified LangGraph architecture.

This module tests the simplified, unified LangGraph implementation
that handles both single-tool and multi-step workflows.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.langgraph_agent_unified import (
    AgentState,
    detect_intent_node,
    execute_workflow_node,
    generate_response_node,
    create_agent_graph,
    get_agent_graph
)


class TestUnifiedLangGraph:
    """Test unified LangGraph components."""
    
    def test_agent_state_structure(self):
        """Test AgentState structure."""
        state = AgentState(
            user_input="test input",
            document_content="test document",
            conversation_history=[],
            available_tools=[],
            selected_tool="",
            tool_parameters={},
            tool_result=None,
            final_response="",
            intent_type="",
            workflow_plan=None,
            current_step=0,
            total_steps=0,
            step_results={}
        )
        
        assert state["user_input"] == "test input"
        assert state["document_content"] == "test document"
        assert state["workflow_plan"] is None
        assert state["current_step"] == 0
    
    @pytest.mark.asyncio
    async def test_detect_intent_node(self):
        """Test intent detection node."""
        state = AgentState(
            user_input="search for AI patents",
            document_content="",
            conversation_history=[],
            available_tools=[],
            selected_tool="",
            tool_parameters={},
            tool_result=None,
            final_response="",
            intent_type="",
            workflow_plan=None,
            current_step=0,
            total_steps=0,
            step_results={}
        )
        
        result = await detect_intent_node(state)
        assert "selected_tool" in result
        assert "intent_type" in result
        assert "tool_parameters" in result
    
    @pytest.mark.asyncio
    async def test_execute_workflow_node(self):
        """Test workflow planning node."""
        state = AgentState(
            user_input="search for AI patents then draft 5 claims",
            document_content="",
            conversation_history=[],
            available_tools=[],
            selected_tool="",
            tool_parameters={},
            tool_result=None,
            final_response="",
            intent_type="",
            workflow_plan=[],
            current_step=0,
            total_steps=0,
            step_results={}
        )
        
        result = await execute_workflow_node(state)
        assert "workflow_plan" in result
        assert "total_steps" in result
        assert "current_step" in result
    
    @pytest.mark.asyncio
    async def test_execute_workflow_node_single(self):
        """Test single tool execution."""
        state = AgentState(
            user_input="search for AI patents",
            document_content="",
            conversation_history=[],
            available_tools=[],
            selected_tool="web_search_tool",
            tool_parameters={"query": "AI patents"},
            tool_result=None,
            final_response="",
            intent_type="tool_execution",
            workflow_plan=[{"step": 1, "tool": "web_search_tool", "params": {"query": "AI patents"}, "output_key": "search_results"}],
            current_step=0,
            total_steps=1,
            step_results={}
        )
        
        # Mock the MCP orchestrator
        with patch('backend.app.services.agent.AgentService') as mock_agent_service_class:
            mock_agent_service = Mock()
            mock_orchestrator = Mock()
            mock_orchestrator.execute_tool = AsyncMock(return_value={"success": True, "result": "Mock result"})
            mock_agent_service._get_mcp_orchestrator.return_value = mock_orchestrator
            mock_agent_service_class.return_value = mock_agent_service
            
            result = await execute_workflow_node(state)
            assert "tool_result" in result
    
    @pytest.mark.asyncio
    async def test_execute_workflow_node_multi_step(self):
        """Test multi-step tool execution."""
        state = AgentState(
            user_input="search for AI patents then draft 5 claims",
            document_content="",
            conversation_history=[],
            available_tools=[],
            selected_tool="",
            tool_parameters={},
            tool_result=None,
            final_response="",
            intent_type="multi_step",
            workflow_plan=[
                {"step": 1, "tool": "web_search_tool", "params": {"query": "AI patents"}, "output_key": "search_results"},
                {"step": 2, "tool": "claim_drafting_tool", "params": {"user_query": "draft 5 claims"}, "output_key": "draft_results"}
            ],
            current_step=0,
            total_steps=2,
            step_results={}
        )
        
        # Mock the MCP orchestrator
        with patch('backend.app.services.agent.AgentService') as mock_agent_service_class:
            mock_agent_service = Mock()
            mock_orchestrator = Mock()
            mock_orchestrator.execute_tool = AsyncMock(return_value={"success": True, "result": "Mock result"})
            mock_agent_service._get_mcp_orchestrator.return_value = mock_orchestrator
            mock_agent_service_class.return_value = mock_agent_service
            
            result = await execute_workflow_node(state)
            assert "current_step" in result
            assert "step_results" in result
    
    @pytest.mark.asyncio
    async def test_generate_response_node_single(self):
        """Test single tool response generation."""
        state = AgentState(
            user_input="search for AI patents",
            document_content="",
            conversation_history=[],
            available_tools=[],
            selected_tool="web_search_tool",
            tool_parameters={"query": "AI patents"},
            tool_result={"success": True, "result": "Search results here"},
            final_response="",
            intent_type="tool_execution",
            workflow_plan=[{"step": 1, "tool": "web_search_tool", "params": {"query": "AI patents"}, "output_key": "search_results"}],
            current_step=1,
            total_steps=1,
            step_results={"search_results": {"success": True, "result": "Search results here"}}
        )
        
        result = await generate_response_node(state)
        assert "final_response" in result
        assert "Search results here" in result["final_response"]
        assert "**Web Search:**" in result["final_response"]
    
    @pytest.mark.asyncio
    async def test_generate_response_node_multi_step(self):
        """Test multi-step response generation."""
        state = AgentState(
            user_input="search for AI patents then draft 5 claims",
            document_content="",
            conversation_history=[],
            available_tools=[],
            selected_tool="",
            tool_parameters={},
            tool_result=None,
            final_response="",
            intent_type="multi_step",
            workflow_plan=[
                {"step": 1, "tool": "web_search_tool", "params": {"query": "AI patents"}, "output_key": "search_results"},
                {"step": 2, "tool": "claim_drafting_tool", "params": {"user_query": "draft 5 claims"}, "output_key": "draft_results"}
            ],
            current_step=2,
            total_steps=2,
            step_results={
                "search_results": {"success": True, "result": "Search results here"},
                "draft_results": {"success": True, "result": "Draft claims here"}
            }
        )
        
        result = await generate_response_node(state)
        assert "final_response" in result
        assert "**Web Search:**" in result["final_response"]
        assert "Draft Claims" in result["final_response"]
    
    def test_create_agent_graph(self):
        """Test agent graph creation."""
        graph = create_agent_graph()
        assert graph is not None
        # Graph should have the expected nodes
        assert hasattr(graph, 'nodes')
    
    def test_get_agent_graph(self):
        """Test agent graph lazy initialization."""
        graph1 = get_agent_graph()
        graph2 = get_agent_graph()
        # Should return the same instance (lazy initialization)
        assert graph1 is graph2


class TestUnifiedLangGraphIntegration:
    """Test unified LangGraph integration with AgentService."""
    
    @pytest.mark.asyncio
    async def test_agent_service_unified_langgraph_integration(self):
        """Test AgentService integration with unified LangGraph."""
        from backend.app.services.agent import AgentService
        
        # Mock the unified LangGraph agent
        async def mock_ainvoke(state):
            return {
                "final_response": "Mock unified LangGraph response",
                "intent_type": "mock_intent",
                "selected_tool": "mock_tool",
                "workflow_plan": [],
                "total_steps": 1,
                "current_step": 1
            }
        
        mock_agent = Mock()
        mock_agent.ainvoke = mock_ainvoke
        
        with patch('backend.app.services.agent.AgentService._get_unified_langgraph_agent', return_value=mock_agent):
            agent_service = AgentService()
            
            # Test unified LangGraph processing
            result = await agent_service.process_user_message_unified_langgraph(
                user_message="test message",
                document_content="test document",
                available_tools=[],
                frontend_chat_history=[]
            )
            
            assert "response" in result
            assert "intent_type" in result
            assert "execution_time" in result
            assert "workflow_metadata" in result
            assert result["success"] is True
            
            # Test workflow_metadata structure
            workflow_metadata = result["workflow_metadata"]
            assert "total_steps" in workflow_metadata
            assert "completed_steps" in workflow_metadata
            assert "workflow_type" in workflow_metadata
            assert "workflow_plan" in workflow_metadata
            
            # Test workflow_type classification logic
            # Single step (1) should be classified as "single_tool"
        assert workflow_metadata["workflow_type"] == "single_tool"
        assert workflow_metadata["total_steps"] == 1

    @pytest.mark.asyncio
    async def test_complex_multi_step_workflow(self):
        """Test complex multi-step workflow: web search -> prior art -> claims -> report."""
        # Mock the LLM client for intent detection
        mock_llm_client = Mock()
        mock_llm_client.generate_text.return_value = {
            "success": True,
            "text": """WORKFLOW_TYPE: MULTI_STEP
TOOL: web_search_tool
INTENT: search web for 5G technical information then perform prior art search followed by claims drafting and final report generation
PARAMETERS: {"query": "5G technical report"}"""
        }
        
        # Mock the LLM client for workflow planning
        mock_workflow_llm_client = Mock()
        mock_workflow_llm_client.generate_text.return_value = {
            "success": True,
            "text": """[
  {"step": 1, "tool": "web_search_tool", "params": {"query": "5G technical report"}, "output_key": "web_search_results"},
  {"step": 2, "tool": "prior_art_search_tool", "params": {"query": "5G technology patents"}, "output_key": "prior_art_results"},
  {"step": 3, "tool": "claim_drafting_tool", "params": {"user_query": "draft claims for 5G technology", "prior_art_context": "{{prior_art_results}}"}, "output_key": "claim_results"},
  {"step": 4, "tool": "claim_analysis_tool", "params": {"user_query": "analyze claims for 5G technology", "claim_context": "{{claim_results}}"}, "output_key": "analysis_results"}
]"""
        }
        
        # Mock the MCP orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.execute_tool = AsyncMock()
        
        # Mock tool execution results
        mock_orchestrator.execute_tool.side_effect = [
            # Web search result
            {
                "success": True,
                "result": "Web search results for 5G technical report: Found 15 relevant articles about 5G technology, network architecture, and implementation challenges.",
                "status": "success"
            },
            # Prior art search result
            {
                "success": True,
                "result": "Prior Art Search Report: Found 8 relevant patents related to 5G technology, including US Patent 10,123,456 for '5G Network Optimization' and US Patent 10,234,567 for '5G Antenna Design'.",
                "status": "success"
            },
            # Claim drafting result
            {
                "success": True,
                "result": "Patent Claims for 5G Technology:\n\nClaim 1: A method for optimizing 5G network performance...\nClaim 2: A system for 5G antenna configuration...",
                "status": "success"
            },
            # Claim analysis result
            {
                "success": True,
                "result": "Claim Analysis Report: The drafted claims show strong novelty and non-obviousness. Recommendations for improvement include adding dependent claims for specific 5G protocols.",
                "status": "success"
            }
        ]
        
        # Mock the agent service
        mock_agent_service = Mock()
        mock_agent_service._get_llm_client.side_effect = [mock_llm_client, mock_workflow_llm_client]
        mock_agent_service._get_mcp_orchestrator.return_value = mock_orchestrator
        
        with patch('app.services.agent.AgentService', return_value=mock_agent_service):
            # Test the complete workflow
            initial_state = AgentState(
                user_input="I am writing a technical report on 5g please help me search web then perform prior art search followed by claims and then the final report",
                document_content="",
                conversation_history=[],
                available_tools=[
                    {"name": "web_search_tool", "description": "Search the web for information"},
                    {"name": "prior_art_search_tool", "description": "Search for prior art patents"},
                    {"name": "claim_drafting_tool", "description": "Draft patent claims"},
                    {"name": "claim_analysis_tool", "description": "Analyze patent claims"}
                ],
                selected_tool="",
                tool_parameters={},
                tool_result=None,
                final_response="",
                intent_type="",
                workflow_plan=None,
                current_step=0,
                total_steps=0,
                step_results={}
            )
            
            # Step 1: Intent Detection
            intent_result = await detect_intent_node(initial_state)
            assert intent_result["intent_type"] == "multi_step"
            assert intent_result["selected_tool"] == "web_search_tool"
            assert intent_result["workflow_plan"] == []
            
            # Step 2: Workflow Planning
            plan_result = await execute_workflow_node(intent_result)
            assert plan_result["workflow_plan"] is not None
            assert len(plan_result["workflow_plan"]) == 4
            assert plan_result["total_steps"] == 4
            assert plan_result["current_step"] == 0
            
            # Verify workflow plan structure
            workflow_plan = plan_result["workflow_plan"]
            assert workflow_plan[0]["tool"] == "web_search_tool"
            assert workflow_plan[1]["tool"] == "prior_art_search_tool"
            assert workflow_plan[2]["tool"] == "claim_drafting_tool"
            assert workflow_plan[3]["tool"] == "claim_analysis_tool"
            
            # Step 3: Execute all tools (4 steps)
            current_state = plan_result
            for step_num in range(4):
                current_state = await execute_workflow_node(current_state)
                assert current_state["current_step"] == step_num + 1
                # Check that the step result is stored with the correct output_key
                output_key = workflow_plan[step_num]["output_key"]
                assert output_key in current_state["step_results"]
            
            # Step 4: Generate final response
            final_result = await generate_response_node(current_state)
            assert final_result["final_response"] is not None
            assert len(final_result["final_response"]) > 0
            
            # Verify the response contains results from all tools
            response = final_result["final_response"]
            assert "Search the web for information" in response
            assert "Search for prior art patents" in response
            assert "Draft patent claims" in response
            assert "Analyze patent claims" in response
            
            # Verify the response contains actual content
            assert "5G technical report" in response
            assert "5G technology" in response
            assert "Patent Claims for 5G Technology" in response
            assert "Claim Analysis Report" in response
            
            # Verify all tools were called
            assert mock_orchestrator.execute_tool.call_count == 4
            
            # Verify tool calls with correct parameters
            calls = mock_orchestrator.execute_tool.call_args_list
            assert calls[0][1]["tool_name"] == "web_search_tool"  # tool_name
            assert calls[1][1]["tool_name"] == "prior_art_search_tool"
            assert calls[2][1]["tool_name"] == "claim_drafting_tool"
            assert calls[3][1]["tool_name"] == "claim_analysis_tool"
            
            print(f"✅ Complex multi-step workflow test passed!")
            print(f"   - Intent: {intent_result['intent_type']}")
            print(f"   - Workflow steps: {len(workflow_plan)}")
            print(f"   - Tools executed: {mock_orchestrator.execute_tool.call_count}")
            print(f"   - Response length: {len(final_result['final_response'])} characters")

    @pytest.mark.asyncio
    async def test_multi_step_workflow_with_failure(self):
        """Test multi-step workflow with tool failure."""
        # Mock the LLM client for intent detection
        mock_llm_client = Mock()
        mock_llm_client.generate_text.return_value = {
            "success": True,
            "text": """WORKFLOW_TYPE: MULTI_STEP
TOOL: web_search_tool
INTENT: search web then prior art search
PARAMETERS: {"query": "5G technology"}"""
        }
        
        # Mock the LLM client for workflow planning
        mock_workflow_llm_client = Mock()
        mock_workflow_llm_client.generate_text.return_value = {
            "success": True,
            "text": """[
  {"step": 1, "tool": "web_search_tool", "params": {"query": "5G technology"}, "output_key": "web_search_results"},
  {"step": 2, "tool": "prior_art_search_tool", "params": {"query": "5G patents"}, "output_key": "prior_art_results"}
]"""
        }
        
        # Mock the MCP orchestrator with one failure
        mock_orchestrator = Mock()
        mock_orchestrator.execute_tool = AsyncMock()
        mock_orchestrator.execute_tool.side_effect = [
            # Web search succeeds
            {
                "success": True,
                "result": "Web search results for 5G technology",
                "status": "success"
            },
            # Prior art search fails
            Exception("Prior art search service unavailable")
        ]
        
        # Mock the agent service
        mock_agent_service = Mock()
        mock_agent_service._get_llm_client.side_effect = [mock_llm_client, mock_workflow_llm_client]
        mock_agent_service._get_mcp_orchestrator.return_value = mock_orchestrator
        
        with patch('app.services.agent.AgentService', return_value=mock_agent_service):
            # Test the workflow with failure
            initial_state = AgentState(
                user_input="search web then prior art search",
                document_content="",
                conversation_history=[],
                available_tools=[
                    {"name": "web_search_tool", "description": "Search the web"},
                    {"name": "prior_art_search_tool", "description": "Search for prior art"}
                ],
                selected_tool="",
                tool_parameters={},
                tool_result=None,
                final_response="",
                intent_type="",
                workflow_plan=None,
                current_step=0,
                total_steps=0,
                step_results={}
            )
            
            # Execute workflow
            intent_result = await detect_intent_node(initial_state)
            plan_result = await execute_workflow_node(intent_result)
            
            # Execute tools (first succeeds, second fails)
            current_state = plan_result
                current_state = await execute_workflow_node(current_state)  # Web search - succeeds
            current_state = await execute_workflow_node(current_state)  # Prior art - fails
            
            # Generate response
            final_result = await generate_response_node(current_state)
            
            # Verify failure handling - check the actual response format
            response = final_result["final_response"]
            print(f"Actual response: {response}")
            
            # The response should contain the successful step and error information
            assert "Search the web" in response
            assert "Web search results for 5G technology" in response
            # The error should be stored in step_results but may not be in the final response
            assert "step_1_error" in current_state["step_results"] or "prior_art_search_tool_error" in current_state["step_results"]
            
            print(f"✅ Multi-step workflow failure test passed!")
            print(f"   - Response contains failure message: {'I completed some steps' in final_result['final_response']}")
            print(f"   - Error details included: {'Prior art search service unavailable' in final_result['final_response']}")
