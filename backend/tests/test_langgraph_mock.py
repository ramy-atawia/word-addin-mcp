"""
Mock-based LangGraph Tests

This test file validates LangGraph functionality using mocks,
so it can run without LangGraph being installed.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Mock LangGraph imports
class MockStateGraph:
    def __init__(self, state_type):
        self.state_type = state_type
        self.nodes = {}
        self.edges = []
        self.entry_point = None
    
    def add_node(self, name: str, func):
        self.nodes[name] = func
    
    def add_edge(self, from_node: str, to_node: str):
        self.edges.append((from_node, to_node))
    
    def add_conditional_edges(self, from_node: str, condition_func, mapping: Dict[str, str]):
        self.conditional_edges = (from_node, condition_func, mapping)
    
    def set_entry_point(self, node: str):
        self.entry_point = node
    
    def compile(self):
        return MockCompiledGraph(self)

class MockCompiledGraph:
    def __init__(self, graph):
        self.graph = graph
    
    async def ainvoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Mock workflow execution
        return {
            "final_response": "Mock response from LangGraph",
            "intent_type": "mock_intent",
            "selected_tool": "mock_tool",
            "workflow_plan": [{"step": 1, "tool": "mock_tool", "parameters": {}}],
            "total_steps": 1,
            "current_step": 1,
            "step_results": {1: {"success": True, "result": "Mock result"}}
        }

class MockEND:
    pass

# Mock the LangGraph imports
with patch.dict('sys.modules', {
    'langgraph': Mock(),
    'langgraph.graph': Mock(StateGraph=MockStateGraph, END=MockEND)
}):
    from app.services.langgraph_agent import (
        AgentState,
        MultiStepAgentState,
        detect_intent_node,
        execute_tool_node,
        generate_response_node,
        detect_intent_advanced_node,
        plan_workflow_node,
        execute_multi_step_node,
        generate_multi_step_response_node,
        create_basic_agent_graph,
        get_basic_agent_graph,
        create_advanced_agent_graph,
        get_advanced_agent_graph
    )


class TestLangGraphMock:
    """Test LangGraph functionality with mocks."""
    
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
        
        assert state["user_input"] == "test input"
        assert state["document_content"] == "test document"
        assert isinstance(state["conversation_history"], list)
        assert isinstance(state["available_tools"], list)
    
    def test_multi_step_agent_state_structure(self):
        """Test that MultiStepAgentState has correct structure."""
        state = MultiStepAgentState(
            user_input="test input",
            document_content="test document",
            conversation_history=[],
            available_tools=[],
            workflow_plan=[],
            current_step=0,
            total_steps=0,
            step_results={},
            selected_tool="",
            tool_parameters={},
            final_response="",
            intent_type="",
            execution_metadata={}
        )
        
        assert state["user_input"] == "test input"
        assert state["workflow_plan"] == []
        assert state["current_step"] == 0
        assert state["total_steps"] == 0
    
    @pytest.mark.asyncio
    async def test_detect_intent_node(self):
        """Test intent detection node."""
        state = AgentState(
            user_input="test input",
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
        assert "intent_type" in result
        assert "selected_tool" in result
        assert "tool_parameters" in result
    
    @pytest.mark.asyncio
    async def test_execute_tool_node(self):
        """Test tool execution node."""
        state = AgentState(
            user_input="test input",
            document_content="",
            conversation_history=[],
            available_tools=[],
            selected_tool="web_search_tool",
            tool_parameters={"query": "test"},
            tool_result=None,
            final_response="",
            intent_type="tool_execution"
        )
        
        # Mock the MCP orchestrator
        with patch('app.services.agent.AgentService') as mock_agent_service_class:
            mock_agent_service = Mock()
            mock_orchestrator = Mock()
            mock_orchestrator.execute_tool = Mock(return_value={"success": True, "result": "Mock result"})
            mock_agent_service._get_mcp_orchestrator.return_value = mock_orchestrator
            mock_agent_service_class.return_value = mock_agent_service
            
            result = await execute_tool_node(state)
            assert "tool_result" in result
    
    @pytest.mark.asyncio
    async def test_generate_response_node(self):
        """Test response generation node."""
        state = AgentState(
            user_input="test input",
            document_content="",
            conversation_history=[],
            available_tools=[],
            selected_tool="web_search_tool",
            tool_parameters={},
            tool_result={"success": True, "result": "Mock result"},
            final_response="",
            intent_type="tool_execution"
        )
        
        result = await generate_response_node(state)
        assert "final_response" in result
        assert result["final_response"] != ""
    
    @pytest.mark.asyncio
    async def test_detect_intent_advanced_node(self):
        """Test advanced intent detection node."""
        state = MultiStepAgentState(
            user_input="draft 1 claim for 5G in AI, then perform prior art",
            document_content="",
            conversation_history=[],
            available_tools=[
                {"name": "claim_drafting_tool", "description": "Draft patent claims"},
                {"name": "prior_art_search_tool", "description": "Search prior art"}
            ],
            workflow_plan=[],
            current_step=0,
            total_steps=0,
            step_results={},
            selected_tool="",
            tool_parameters={},
            final_response="",
            intent_type="",
            execution_metadata={}
        )
        
        result = await detect_intent_advanced_node(state)
        assert "intent_type" in result
        assert "execution_metadata" in result
    
    @pytest.mark.asyncio
    async def test_plan_workflow_node(self):
        """Test workflow planning node."""
        state = MultiStepAgentState(
            user_input="draft 1 claim for 5G in AI, then perform prior art",
            document_content="",
            conversation_history=[],
            available_tools=[
                {"name": "claim_drafting_tool", "description": "Draft patent claims"},
                {"name": "prior_art_search_tool", "description": "Search prior art"}
            ],
            workflow_plan=[],
            current_step=0,
            total_steps=0,
            step_results={},
            selected_tool="",
            tool_parameters={},
            final_response="",
            intent_type="multi_step",
            execution_metadata={"workflow_type": "multi_step"}
        )
        
        result = await plan_workflow_node(state)
        assert "workflow_plan" in result
        assert "total_steps" in result
        assert "current_step" in result
        assert "step_results" in result
    
    @pytest.mark.asyncio
    async def test_execute_multi_step_node(self):
        """Test multi-step execution node."""
        state = MultiStepAgentState(
            user_input="draft 1 claim for 5G in AI, then perform prior art",
            document_content="",
            conversation_history=[],
            available_tools=[
                {"name": "claim_drafting_tool", "description": "Draft patent claims"},
                {"name": "prior_art_search_tool", "description": "Search prior art"}
            ],
            workflow_plan=[
                {"step": 1, "tool": "prior_art_search_tool", "parameters": {"query": "5G AI"}, "output_key": "prior_art_results"},
                {"step": 2, "tool": "claim_drafting_tool", "parameters": {"user_query": "draft 1 claim"}, "output_key": "draft_claims"}
            ],
            current_step=0,
            total_steps=2,
            step_results={},
            selected_tool="",
            tool_parameters={},
            final_response="",
            intent_type="multi_step",
            execution_metadata={}
        )
        
        # Mock the MCP orchestrator
        with patch('app.services.agent.AgentService') as mock_agent_service_class:
            mock_agent_service = Mock()
            mock_orchestrator = Mock()
            mock_orchestrator.execute_tool = Mock(return_value={"success": True, "result": "Mock result"})
            mock_agent_service._get_mcp_orchestrator.return_value = mock_orchestrator
            mock_agent_service_class.return_value = mock_agent_service
            
            result = await execute_multi_step_node(state)
            assert "step_results" in result
            assert "current_step" in result
    
    @pytest.mark.asyncio
    async def test_generate_multi_step_response_node(self):
        """Test multi-step response generation node."""
        state = MultiStepAgentState(
            user_input="draft 1 claim for 5G in AI, then perform prior art",
            document_content="",
            conversation_history=[],
            available_tools=[],
            workflow_plan=[
                {"step": 1, "tool": "prior_art_search_tool", "output_key": "prior_art_results"},
                {"step": 2, "tool": "claim_drafting_tool", "output_key": "draft_claims"}
            ],
            current_step=2,
            total_steps=2,
            step_results={
                1: {"success": True, "result": "Prior art search results"},
                2: {"success": True, "result": "Draft claims results"}
            },
            selected_tool="",
            tool_parameters={},
            final_response="",
            intent_type="multi_step",
            execution_metadata={}
        )
        
        result = await generate_multi_step_response_node(state)
        assert "final_response" in result
        assert "Prior Art Search Results" in result["final_response"]
        assert "Draft Claims" in result["final_response"]
    
    def test_create_basic_agent_graph(self):
        """Test basic agent graph creation."""
        graph = create_basic_agent_graph()
        assert graph is not None
        assert hasattr(graph, 'ainvoke')
    
    def test_get_basic_agent_graph(self):
        """Test basic agent graph retrieval."""
        graph1 = get_basic_agent_graph()
        graph2 = get_basic_agent_graph()
        assert graph1 is graph2  # Should be cached
    
    def test_create_advanced_agent_graph(self):
        """Test advanced agent graph creation."""
        graph = create_advanced_agent_graph()
        assert graph is not None
        assert hasattr(graph, 'ainvoke')
    
    def test_get_advanced_agent_graph(self):
        """Test advanced agent graph retrieval."""
        graph1 = get_advanced_agent_graph()
        graph2 = get_advanced_agent_graph()
        assert graph1 is graph2  # Should be cached


class TestLangGraphIntegration:
    """Test LangGraph integration with AgentService."""
    
    @pytest.mark.asyncio
    async def test_agent_service_langgraph_integration(self):
        """Test AgentService integration with LangGraph."""
        from app.services.agent import AgentService
        
        # Mock the LangGraph agent
        async def mock_ainvoke(state):
            return {
                "final_response": "Mock LangGraph response",
                "intent_type": "mock_intent",
                "selected_tool": "mock_tool"
            }
        
        mock_agent = Mock()
        mock_agent.ainvoke = mock_ainvoke
        
        with patch('app.services.agent.AgentService._get_langgraph_agent', return_value=mock_agent):
            agent_service = AgentService()
            
            # Test basic LangGraph processing
            result = await agent_service.process_user_message_langgraph(
                user_message="test message",
                document_content="test document",
                available_tools=[],
                frontend_chat_history=[]
            )
            
            assert "response" in result
            assert "intent_type" in result
            assert "execution_time" in result
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_agent_service_advanced_langgraph_integration(self):
        """Test AgentService integration with advanced LangGraph."""
        from app.services.agent import AgentService
        
        # Mock the advanced LangGraph agent
        async def mock_ainvoke_advanced(state):
            return {
                "final_response": "Mock advanced LangGraph response",
                "intent_type": "multi_step_workflow",
                "workflow_plan": [{"step": 1, "tool": "mock_tool"}],
                "total_steps": 1,
                "current_step": 1
            }
        
        mock_agent = Mock()
        mock_agent.ainvoke = mock_ainvoke_advanced
        
        with patch('app.services.agent.AgentService._get_advanced_langgraph_agent', return_value=mock_agent):
            agent_service = AgentService()
            
            # Test advanced LangGraph processing
            result = await agent_service.process_user_message_advanced_langgraph(
                user_message="draft 1 claim for 5G in AI, then perform prior art",
                document_content="test document",
                available_tools=[],
                frontend_chat_history=[]
            )
            
            assert "response" in result
            assert "intent_type" in result
            assert "workflow_metadata" in result
            assert result["success"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
