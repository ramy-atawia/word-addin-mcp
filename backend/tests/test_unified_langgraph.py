"""
Tests for unified LangGraph architecture.

This module tests the simplified, unified LangGraph implementation
that handles both single-tool and multi-step workflows.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from backend.app.services.langgraph_agent_unified import (
    AgentState,
    detect_intent_node,
    plan_workflow_node,
    execute_tool_node,
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
    async def test_plan_workflow_node(self):
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
            workflow_plan=None,
            current_step=0,
            total_steps=0,
            step_results={}
        )
        
        result = await plan_workflow_node(state)
        assert "workflow_plan" in result
        assert "total_steps" in result
        assert "current_step" in result
    
    @pytest.mark.asyncio
    async def test_execute_tool_node_single(self):
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
            
            result = await execute_tool_node(state)
            assert "tool_result" in result
    
    @pytest.mark.asyncio
    async def test_execute_tool_node_multi_step(self):
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
            
            result = await execute_tool_node(state)
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
        assert "Web Search Results" in result["final_response"]
    
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
        assert "Web Search Results" in result["final_response"]
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
