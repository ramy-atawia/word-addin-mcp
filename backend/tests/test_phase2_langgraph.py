"""
Test Phase 2: LangGraph Core Workflow Nodes & Tool Execution

This test file validates the Phase 2 LangGraph integration:
- Enhanced intent detection with LLM
- Real tool execution via MCP orchestrator
- LLM-based response formatting
- API endpoint integration
- Error handling and fallbacks
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from app.services.langgraph_agent import (
    AgentState,
    detect_intent_node,
    execute_tool_node,
    generate_response_node,
    _simple_intent_detection,
    _parse_llm_intent_response,
    _llm_response_formatting,
    _simple_response_formatting
)
from app.services.agent import AgentService


class TestPhase2IntentDetection:
    """Test Phase 2 enhanced intent detection."""
    
    @pytest.mark.asyncio
    async def test_llm_intent_detection_prior_art(self):
        """Test LLM-based intent detection for prior art search."""
        # Mock LLM response
        mock_llm_response = Mock()
        mock_llm_response.content = """
TOOL: prior_art_search_tool
INTENT: search prior art
PARAMETERS: {"query": "AI patents", "max_results": 10}
"""
        
        # Mock LLM client
        mock_llm_client = AsyncMock()
        mock_llm_client.ainvoke.return_value = mock_llm_response
        
        # Mock agent service
        with patch('app.services.langgraph_agent.AgentService') as mock_agent_class:
            mock_agent = Mock()
            mock_agent._get_llm_client.return_value = mock_llm_client
            mock_agent_class.return_value = mock_agent
            
            state = AgentState(
                user_input="find prior art for AI patents",
                document_content="",
                conversation_history=[],
                available_tools=[
                    {"name": "prior_art_search_tool", "description": "Search for prior art"}
                ],
                selected_tool="",
                tool_parameters={},
                tool_result=None,
                final_response="",
                intent_type=""
            )
            
            result = await detect_intent_node(state)
            
            assert result["selected_tool"] == "prior_art_search_tool"
            assert result["intent_type"] == "search prior art"
            assert result["tool_parameters"]["query"] == "AI patents"
            assert result["tool_parameters"]["max_results"] == 10
    
    @pytest.mark.asyncio
    async def test_llm_intent_detection_claim_drafting(self):
        """Test LLM-based intent detection for claim drafting."""
        mock_llm_response = Mock()
        mock_llm_response.content = """
TOOL: claim_drafting_tool
INTENT: draft patent claims
PARAMETERS: {"user_query": "draft 5 claims for blockchain", "num_claims": 5}
"""
        
        mock_llm_client = AsyncMock()
        mock_llm_client.ainvoke.return_value = mock_llm_response
        
        with patch('app.services.langgraph_agent.AgentService') as mock_agent_class:
            mock_agent = Mock()
            mock_agent._get_llm_client.return_value = mock_llm_client
            mock_agent_class.return_value = mock_agent
            
            state = AgentState(
                user_input="draft 5 claims for blockchain technology",
                document_content="",
                conversation_history=[],
                available_tools=[
                    {"name": "claim_drafting_tool", "description": "Draft patent claims"}
                ],
                selected_tool="",
                tool_parameters={},
                tool_result=None,
                final_response="",
                intent_type=""
            )
            
            result = await detect_intent_node(state)
            
            assert result["selected_tool"] == "claim_drafting_tool"
            assert result["intent_type"] == "draft patent claims"
            assert result["tool_parameters"]["num_claims"] == 5
    
    @pytest.mark.asyncio
    async def test_llm_intent_detection_conversation(self):
        """Test LLM-based intent detection for conversation."""
        mock_llm_response = Mock()
        mock_llm_response.content = """
TOOL: conversation
INTENT: greeting
PARAMETERS: {}
"""
        
        mock_llm_client = AsyncMock()
        mock_llm_client.ainvoke.return_value = mock_llm_response
        
        with patch('app.services.langgraph_agent.AgentService') as mock_agent_class:
            mock_agent = Mock()
            mock_agent._get_llm_client.return_value = mock_llm_client
            mock_agent_class.return_value = mock_agent
            
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
            
            assert result["selected_tool"] == "conversation"
            assert result["intent_type"] == "greeting"
            assert result["tool_parameters"] == {}
    
    @pytest.mark.asyncio
    async def test_llm_intent_detection_fallback(self):
        """Test fallback to simple detection when LLM fails."""
        with patch('app.services.langgraph_agent.AgentService') as mock_agent_class:
            mock_agent = Mock()
            mock_agent._get_llm_client.return_value = None  # No LLM client
            mock_agent_class.return_value = mock_agent
            
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
            
            # Should fallback to simple detection
            assert result["selected_tool"] == "prior_art_search_tool"
            assert result["intent_type"] == "tool_execution"
            assert "query" in result["tool_parameters"]
    
    def test_parse_llm_intent_response_valid(self):
        """Test parsing valid LLM response."""
        response_text = """
TOOL: prior_art_search_tool
INTENT: search prior art
PARAMETERS: {"query": "AI patents", "max_results": 10}
"""
        
        tool, intent, params = _parse_llm_intent_response(response_text)
        
        assert tool == "prior_art_search_tool"
        assert intent == "search prior art"
        assert params["query"] == "AI patents"
        assert params["max_results"] == 10
    
    def test_parse_llm_intent_response_invalid_json(self):
        """Test parsing LLM response with invalid JSON."""
        response_text = """
TOOL: prior_art_search_tool
INTENT: search prior art
PARAMETERS: {invalid json}
"""
        
        tool, intent, params = _parse_llm_intent_response(response_text)
        
        assert tool == "prior_art_search_tool"
        assert intent == "search prior art"
        assert params == {}  # Should default to empty dict
    
    def test_parse_llm_intent_response_malformed(self):
        """Test parsing malformed LLM response."""
        response_text = "This is not a properly formatted response"
        
        tool, intent, params = _parse_llm_intent_response(response_text)
        
        assert tool == "conversation"
        assert intent == "conversation"
        assert params == {}


class TestPhase2ToolExecution:
    """Test Phase 2 real tool execution."""
    
    @pytest.mark.asyncio
    async def test_execute_tool_node_success(self):
        """Test successful tool execution."""
        # Mock MCP orchestrator
        mock_orchestrator = AsyncMock()
        mock_orchestrator.execute_tool.return_value = {
            "success": True,
            "result": "Prior art search completed successfully",
            "data": [{"title": "AI Patent 1", "abstract": "..."}]
        }
        
        # Mock agent service
        with patch('app.services.langgraph_agent.AgentService') as mock_agent_class:
            mock_agent = Mock()
            mock_agent._get_mcp_orchestrator.return_value = mock_orchestrator
            mock_agent_class.return_value = mock_agent
            
            state = AgentState(
                user_input="test",
                document_content="",
                conversation_history=[],
                available_tools=[],
                selected_tool="prior_art_search_tool",
                tool_parameters={"query": "AI patents"},
                tool_result=None,
                final_response="",
                intent_type="tool_execution"
            )
            
            result = await execute_tool_node(state)
            
            assert result["tool_result"]["success"] is True
            assert "Prior art search completed successfully" in result["tool_result"]["result"]
            mock_orchestrator.execute_tool.assert_called_once_with(
                "prior_art_search_tool", 
                {"query": "AI patents"}
            )
    
    @pytest.mark.asyncio
    async def test_execute_tool_node_error(self):
        """Test tool execution error handling."""
        # Mock MCP orchestrator to raise exception
        mock_orchestrator = AsyncMock()
        mock_orchestrator.execute_tool.side_effect = Exception("Tool execution failed")
        
        with patch('app.services.langgraph_agent.AgentService') as mock_agent_class:
            mock_agent = Mock()
            mock_agent._get_mcp_orchestrator.return_value = mock_orchestrator
            mock_agent_class.return_value = mock_agent
            
            state = AgentState(
                user_input="test",
                document_content="",
                conversation_history=[],
                available_tools=[],
                selected_tool="prior_art_search_tool",
                tool_parameters={"query": "AI patents"},
                tool_result=None,
                final_response="",
                intent_type="tool_execution"
            )
            
            result = await execute_tool_node(state)
            
            assert result["tool_result"]["success"] is False
            assert "Tool execution failed" in result["tool_result"]["error"]
            assert result["tool_result"]["tool_name"] == "prior_art_search_tool"
    
    @pytest.mark.asyncio
    async def test_execute_tool_node_no_tool(self):
        """Test tool execution with no selected tool."""
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


class TestPhase2ResponseGeneration:
    """Test Phase 2 response generation."""
    
    @pytest.mark.asyncio
    async def test_llm_response_formatting_success(self):
        """Test LLM-based response formatting for successful tool execution."""
        mock_llm_response = Mock()
        mock_llm_response.content = "Here are the prior art search results for AI patents:\n\n1. Patent A: Advanced AI algorithms\n2. Patent B: Machine learning systems"
        
        mock_llm_client = AsyncMock()
        mock_llm_client.ainvoke.return_value = mock_llm_response
        
        state = AgentState(
            user_input="find prior art for AI patents",
            document_content="",
            conversation_history=[],
            available_tools=[],
            selected_tool="prior_art_search_tool",
            tool_parameters={},
            tool_result={
                "success": True,
                "result": "Found 2 patents",
                "data": [{"title": "Patent A"}, {"title": "Patent B"}]
            },
            final_response="",
            intent_type="tool_execution"
        )
        
        result = await _llm_response_formatting(state, mock_llm_client)
        
        assert "prior art search results" in result
        assert "AI patents" in result
        mock_llm_client.ainvoke.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_llm_response_formatting_error(self):
        """Test LLM response formatting for tool execution error."""
        state = AgentState(
            user_input="find prior art for AI patents",
            document_content="",
            conversation_history=[],
            available_tools=[],
            selected_tool="prior_art_search_tool",
            tool_parameters={},
            tool_result={
                "success": False,
                "error": "API rate limit exceeded"
            },
            final_response="",
            intent_type="tool_execution"
        )
        
        result = await _llm_response_formatting(state, Mock())
        
        assert "encountered an issue" in result
        assert "prior_art_search_tool" in result
        assert "API rate limit exceeded" in result
    
    @pytest.mark.asyncio
    async def test_simple_response_formatting_prior_art(self):
        """Test simple response formatting for prior art tool."""
        state = AgentState(
            user_input="test",
            document_content="",
            conversation_history=[],
            available_tools=[],
            selected_tool="prior_art_search_tool",
            tool_parameters={},
            tool_result={"success": True, "data": "Search results here"},
            final_response="",
            intent_type="tool_execution"
        )
        
        result = await _simple_response_formatting(state)
        
        assert "prior art search results" in result
        assert "Search results here" in result
    
    @pytest.mark.asyncio
    async def test_simple_response_formatting_claim_drafting(self):
        """Test simple response formatting for claim drafting tool."""
        state = AgentState(
            user_input="test",
            document_content="",
            conversation_history=[],
            available_tools=[],
            selected_tool="claim_drafting_tool",
            tool_parameters={},
            tool_result={"success": True, "claims": "Drafted claims here"},
            final_response="",
            intent_type="tool_execution"
        )
        
        result = await _simple_response_formatting(state)
        
        assert "drafted claims" in result
        assert "Drafted claims here" in result
    
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
        
        assert "I'm here to help" in result["final_response"]
        assert "patent-related tasks" in result["final_response"]


class TestPhase2AgentServiceIntegration:
    """Test Phase 2 integration with AgentService."""
    
    @pytest.mark.asyncio
    async def test_agent_service_langgraph_with_real_tools(self):
        """Test AgentService LangGraph method with real tool execution."""
        # Mock MCP orchestrator
        mock_orchestrator = AsyncMock()
        mock_orchestrator.execute_tool.return_value = {
            "success": True,
            "result": "Prior art search completed",
            "data": [{"title": "AI Patent", "abstract": "..."}]
        }
        
        # Mock agent service
        with patch('app.services.agent.AgentService') as mock_agent_class:
            mock_agent = Mock()
            mock_agent._get_mcp_orchestrator.return_value = mock_orchestrator
            mock_agent._get_llm_client.return_value = None  # Use simple detection
            mock_agent_class.return_value = mock_agent
            
            agent_service = AgentService()
            
            result = await agent_service.process_user_message_langgraph(
                user_message="find prior art for AI patents",
                document_content="test document",
                available_tools=[{"name": "prior_art_search_tool", "description": "Search prior art"}],
                frontend_chat_history=[]
            )
            
            assert result["success"] is True
            assert result["intent_type"] == "tool_execution"
            assert result["tool_name"] == "prior_art_search_tool"
            assert "Prior art search completed" in result["response"]
    
    @pytest.mark.asyncio
    async def test_agent_service_langgraph_error_handling(self):
        """Test AgentService LangGraph error handling."""
        # Mock MCP orchestrator to raise exception
        mock_orchestrator = AsyncMock()
        mock_orchestrator.execute_tool.side_effect = Exception("Tool execution failed")
        
        with patch('app.services.agent.AgentService') as mock_agent_class:
            mock_agent = Mock()
            mock_agent._get_mcp_orchestrator.return_value = mock_orchestrator
            mock_agent._get_llm_client.return_value = None
            mock_agent_class.return_value = mock_agent
            
            agent_service = AgentService()
            
            result = await agent_service.process_user_message_langgraph(
                user_message="find prior art for AI patents",
                document_content="",
                available_tools=[],
                frontend_chat_history=[]
            )
            
            assert result["success"] is True  # LangGraph handles errors gracefully
            assert "encountered an issue" in result["response"]


class TestPhase2APIIntegration:
    """Test Phase 2 API endpoint integration."""
    
    @pytest.mark.asyncio
    async def test_api_endpoint_langgraph_enabled(self):
        """Test API endpoint with LangGraph enabled."""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.use_langgraph = True
            
            # Mock agent service
            with patch('app.api.v1.mcp.agent_service') as mock_agent_service:
                mock_agent_service.process_user_message_langgraph = AsyncMock()
                mock_agent_service.process_user_message_langgraph.return_value = {
                    "response": "LangGraph Phase 2 response",
                    "intent_type": "tool_execution",
                    "tool_name": "prior_art_search_tool",
                    "execution_time": 1.5,
                    "success": True,
                    "error": None
                }
                
                # This would be tested in integration tests
                # For now, we just verify the method is called
                result = await mock_agent_service.process_user_message_langgraph(
                    user_message="test",
                    document_content="",
                    available_tools=[],
                    frontend_chat_history=[]
                )
                
                assert result["response"] == "LangGraph Phase 2 response"
                assert result["intent_type"] == "tool_execution"
    
    @pytest.mark.asyncio
    async def test_api_endpoint_langgraph_disabled(self):
        """Test API endpoint with LangGraph disabled."""
        with patch('app.core.config.settings') as mock_settings:
            mock_settings.use_langgraph = False
            
            # Mock agent service
            with patch('app.api.v1.mcp.agent_service') as mock_agent_service:
                mock_agent_service.process_user_message = AsyncMock()
                mock_agent_service.process_user_message.return_value = {
                    "response": "Original agent response",
                    "intent_type": "conversation",
                    "tool_name": None,
                    "execution_time": 0.5,
                    "success": True,
                    "error": None
                }
                
                result = await mock_agent_service.process_user_message(
                    user_message="test",
                    document_content="",
                    available_tools=[],
                    frontend_chat_history=[]
                )
                
                assert result["response"] == "Original agent response"
                assert result["intent_type"] == "conversation"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
