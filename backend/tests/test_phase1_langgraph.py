"""
Test Phase 1: LangGraph Foundation Setup

This test file validates the Phase 1 LangGraph integration:
- Basic workflow structure
- State management
- Node execution
- Integration with AgentService
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from app.services.langgraph_agent import (
    AgentState,
    detect_intent_node,
    execute_tool_node,
    generate_response_node,
    create_basic_agent_graph,
    get_basic_agent_graph
)
from app.services.agent import AgentService


class TestPhase1LangGraph:
    """Test Phase 1 LangGraph functionality."""
    
    def test_agent_state_structure(self):
        """Test that AgentState has correct structure."""
        state = AgentState(
            user_input="test input",
            document_content="test document",
            conversation_history=[],
            available_tools=[],
            selected_tool="",
            tool_parameters={},
            tool_result=None,
            final_response="",
            intent_type=""
        )
        
        # Verify all required fields are present
        assert "user_input" in state
        assert "document_content" in state
        assert "conversation_history" in state
        assert "available_tools" in state
        assert "selected_tool" in state
        assert "tool_parameters" in state
        assert "tool_result" in state
        assert "final_response" in state
        assert "intent_type" in state
    
    @pytest.mark.asyncio
    async def test_detect_intent_node_prior_art(self):
        """Test intent detection for prior art search."""
        state = AgentState(
            user_input="find prior art for AI patents",
            document_content="",
            conversation_history=[],
            available_tools=[],
            selected_tool="",
            tool_parameters={},
            tool_result=None,
            final_response="",
            intent_type=""
        )
        
        result = await detect_intent_node(state)
        
        assert result["selected_tool"] == "prior_art_search_tool"
        assert result["intent_type"] == "tool_execution"
        assert result["user_input"] == state["user_input"]
    
    @pytest.mark.asyncio
    async def test_detect_intent_node_claim_drafting(self):
        """Test intent detection for claim drafting."""
        state = AgentState(
            user_input="draft 5 claims for blockchain technology",
            document_content="",
            conversation_history=[],
            available_tools=[],
            selected_tool="",
            tool_parameters={},
            tool_result=None,
            final_response="",
            intent_type=""
        )
        
        result = await detect_intent_node(state)
        
        assert result["selected_tool"] == "claim_drafting_tool"
        assert result["intent_type"] == "tool_execution"
    
    @pytest.mark.asyncio
    async def test_detect_intent_node_conversation(self):
        """Test intent detection for conversation."""
        state = AgentState(
            user_input="hello, how are you?",
            document_content="",
            conversation_history=[],
            available_tools=[],
            selected_tool="",
            tool_parameters={},
            tool_result=None,
            final_response="",
            intent_type=""
        )
        
        result = await detect_intent_node(state)
        
        assert result["selected_tool"] == ""
        assert result["intent_type"] == "conversation"
    
    @pytest.mark.asyncio
    async def test_execute_tool_node_with_tool(self):
        """Test tool execution with selected tool."""
        state = AgentState(
            user_input="test",
            document_content="",
            conversation_history=[],
            available_tools=[],
            selected_tool="prior_art_search_tool",
            tool_parameters={},
            tool_result=None,
            final_response="",
            intent_type="tool_execution"
        )
        
        result = await execute_tool_node(state)
        
        assert result["tool_result"] is not None
        assert "Phase 1" in result["tool_result"]
        assert "prior_art_search_tool" in result["tool_result"]
    
    @pytest.mark.asyncio
    async def test_execute_tool_node_no_tool(self):
        """Test tool execution without selected tool."""
        state = AgentState(
            user_input="test",
            document_content="",
            conversation_history=[],
            available_tools=[],
            selected_tool="",
            tool_parameters={},
            tool_result=None,
            final_response="",
            intent_type="conversation"
        )
        
        result = await execute_tool_node(state)
        
        assert result["tool_result"] is None
    
    @pytest.mark.asyncio
    async def test_generate_response_node_conversation(self):
        """Test response generation for conversation."""
        state = AgentState(
            user_input="hello",
            document_content="",
            conversation_history=[],
            available_tools=[],
            selected_tool="",
            tool_parameters={},
            tool_result=None,
            final_response="",
            intent_type="conversation"
        )
        
        result = await generate_response_node(state)
        
        assert "Phase 1" in result["final_response"]
        assert "LangGraph foundation active" in result["final_response"]
    
    @pytest.mark.asyncio
    async def test_generate_response_node_with_tool_result(self):
        """Test response generation with tool result."""
        state = AgentState(
            user_input="test",
            document_content="",
            conversation_history=[],
            available_tools=[],
            selected_tool="prior_art_search_tool",
            tool_parameters={},
            tool_result="Phase 1: Tool prior_art_search_tool would be executed here",
            final_response="",
            intent_type="tool_execution"
        )
        
        result = await generate_response_node(state)
        
        assert "Phase 1" in result["final_response"]
        assert "prior_art_search_tool" in result["final_response"]
    
    @pytest.mark.asyncio
    async def test_generate_response_node_no_tool_result(self):
        """Test response generation without tool result."""
        state = AgentState(
            user_input="test",
            document_content="",
            conversation_history=[],
            available_tools=[],
            selected_tool="",
            tool_parameters={},
            tool_result=None,
            final_response="",
            intent_type="tool_execution"
        )
        
        result = await generate_response_node(state)
        
        assert "not sure how to help" in result["final_response"]
    
    def test_create_basic_agent_graph(self):
        """Test basic agent graph creation."""
        graph = create_basic_agent_graph()
        
        # Verify graph is created successfully
        assert graph is not None
        # Note: We can't easily test the internal structure without
        # exposing implementation details, so we just verify it's created
    
    def test_get_basic_agent_graph_singleton(self):
        """Test that get_basic_agent_graph returns singleton."""
        graph1 = get_basic_agent_graph()
        graph2 = get_basic_agent_graph()
        
        # Should return the same instance
        assert graph1 is graph2
    
    @pytest.mark.asyncio
    async def test_full_workflow_prior_art(self):
        """Test complete workflow for prior art search."""
        graph = get_basic_agent_graph()
        
        initial_state = AgentState(
            user_input="find prior art for AI patents",
            document_content="test document",
            conversation_history=[],
            available_tools=[],
            selected_tool="",
            tool_parameters={},
            tool_result=None,
            final_response="",
            intent_type=""
        )
        
        result = await graph.ainvoke(initial_state)
        
        # Verify workflow completed successfully
        assert result["intent_type"] == "tool_execution"
        assert result["selected_tool"] == "prior_art_search_tool"
        assert result["tool_result"] is not None
        assert result["final_response"] is not None
        assert "Phase 1" in result["final_response"]
    
    @pytest.mark.asyncio
    async def test_full_workflow_conversation(self):
        """Test complete workflow for conversation."""
        graph = get_basic_agent_graph()
        
        initial_state = AgentState(
            user_input="hello, how are you?",
            document_content="",
            conversation_history=[],
            available_tools=[],
            selected_tool="",
            tool_parameters={},
            tool_result=None,
            final_response="",
            intent_type=""
        )
        
        result = await graph.ainvoke(initial_state)
        
        # Verify workflow completed successfully
        assert result["intent_type"] == "conversation"
        assert result["selected_tool"] == ""
        assert result["final_response"] is not None
        assert "Phase 1" in result["final_response"]


class TestPhase1AgentServiceIntegration:
    """Test Phase 1 integration with AgentService."""
    
    @pytest.mark.asyncio
    async def test_agent_service_langgraph_method(self):
        """Test AgentService LangGraph method."""
        agent_service = AgentService()
        
        # Test with prior art search
        result = await agent_service.process_user_message_langgraph(
            user_message="find prior art for AI patents",
            document_content="test document",
            available_tools=[],
            frontend_chat_history=[]
        )
        
        # Verify response format matches existing API
        assert "response" in result
        assert "intent_type" in result
        assert "tool_name" in result
        assert "execution_time" in result
        assert "success" in result
        assert "error" in result
        
        # Verify content
        assert result["success"] is True
        assert result["intent_type"] == "tool_execution"
        assert result["tool_name"] == "prior_art_search_tool"
        assert "Phase 1" in result["response"]
    
    @pytest.mark.asyncio
    async def test_agent_service_langgraph_conversation(self):
        """Test AgentService LangGraph method with conversation."""
        agent_service = AgentService()
        
        result = await agent_service.process_user_message_langgraph(
            user_message="hello, how are you?",
            document_content="",
            available_tools=[],
            frontend_chat_history=[]
        )
        
        assert result["success"] is True
        assert result["intent_type"] == "conversation"
        assert result["tool_name"] is None
        assert "Phase 1" in result["response"]
    
    @pytest.mark.asyncio
    async def test_agent_service_langgraph_error_handling(self):
        """Test AgentService LangGraph error handling."""
        agent_service = AgentService()
        
        # Mock the LangGraph agent to raise an error
        with patch.object(agent_service, '_get_langgraph_agent', return_value=None):
            result = await agent_service.process_user_message_langgraph(
                user_message="test",
                document_content="",
                available_tools=[],
                frontend_chat_history=[]
            )
            
            assert result["success"] is False
            assert "error" in result
            assert "LangGraph agent not available" in result["response"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
