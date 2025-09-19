"""
Test Phase 3: LangGraph Multi-step Workflow Support

This test file validates the Phase 3 LangGraph integration:
- Advanced intent detection for multi-step workflows
- Workflow planning and execution
- Context passing between steps
- Multi-step response generation
- API endpoint integration with workflow routing
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from app.services.langgraph_agent import (
    MultiStepAgentState,
    detect_intent_advanced_node,
    plan_workflow_node,
    execute_multi_step_node,
    generate_multi_step_response_node,
    _simple_multi_step_intent_detection,
    _parse_advanced_intent_response,
    _extract_search_query,
    _extract_claim_parameters,
    _prepare_parameters_with_context,
    create_advanced_agent_graph,
    get_advanced_agent_graph
)
from app.services.agent import AgentService


class TestPhase3AdvancedIntentDetection:
    """Test Phase 3 advanced intent detection for multi-step workflows."""
    
    @pytest.mark.asyncio
    async def test_llm_multi_step_intent_detection(self):
        """Test LLM-based intent detection for multi-step workflows."""
        # Mock LLM response
        mock_llm_response = Mock()
        mock_llm_response.content = """
WORKFLOW_TYPE: multi_step
INTENT: research and draft workflow
TOOLS: prior_art_search_tool,claim_drafting_tool
PARAMETERS: {"step1": {"tool": "prior_art_search_tool", "params": {"query": "AI patents"}}, "step2": {"tool": "claim_drafting_tool", "params": {"user_query": "draft 5 claims", "prior_art_context": "{step1_result}"}}}
"""
        
        # Mock LLM client
        mock_llm_client = AsyncMock()
        mock_llm_client.ainvoke.return_value = mock_llm_response
        
        # Mock agent service
        with patch('app.services.langgraph_agent.AgentService') as mock_agent_class:
            mock_agent = Mock()
            mock_agent._get_llm_client.return_value = mock_llm_client
            mock_agent_class.return_value = mock_agent
            
            state = MultiStepAgentState(
                user_input="find prior art for AI patents and then draft 5 claims",
                document_content="",
                conversation_history=[],
                available_tools=[
                    {"name": "prior_art_search_tool", "description": "Search for prior art"},
                    {"name": "claim_drafting_tool", "description": "Draft patent claims"}
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
            
            assert result["intent_type"] == "research and draft workflow"
            assert result["execution_metadata"]["workflow_type"] == "multi_step"
            assert "prior_art_search_tool" in result["execution_metadata"]["tools"]
            assert "claim_drafting_tool" in result["execution_metadata"]["tools"]
    
    @pytest.mark.asyncio
    async def test_llm_single_tool_intent_detection(self):
        """Test LLM-based intent detection for single tool workflows."""
        mock_llm_response = Mock()
        mock_llm_response.content = """
WORKFLOW_TYPE: single_tool
INTENT: search prior art
TOOLS: prior_art_search_tool
PARAMETERS: {"query": "AI patents"}
"""
        
        mock_llm_client = AsyncMock()
        mock_llm_client.ainvoke.return_value = mock_llm_response
        
        with patch('app.services.langgraph_agent.AgentService') as mock_agent_class:
            mock_agent = Mock()
            mock_agent._get_llm_client.return_value = mock_llm_client
            mock_agent_class.return_value = mock_agent
            
            state = MultiStepAgentState(
                user_input="find prior art for AI patents",
                document_content="",
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
            
            result = await detect_intent_advanced_node(state)
            
            assert result["intent_type"] == "search prior art"
            assert result["execution_metadata"]["workflow_type"] == "single_tool"
            assert result["execution_metadata"]["tools"] == ["prior_art_search_tool"]
    
    @pytest.mark.asyncio
    async def test_simple_multi_step_intent_detection(self):
        """Test fallback simple multi-step intent detection."""
        state = MultiStepAgentState(
            user_input="find prior art and then draft claims",
            document_content="",
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
        
        result = await _simple_multi_step_intent_detection(state)
        
        assert result["intent_type"] == "multi-step workflow"
        assert result["execution_metadata"]["workflow_type"] == "multi_step"
    
    def test_parse_advanced_intent_response_multi_step(self):
        """Test parsing LLM response for multi-step workflow."""
        response_text = """
WORKFLOW_TYPE: multi_step
INTENT: research and draft
TOOLS: prior_art_search_tool,claim_drafting_tool
PARAMETERS: {"step1": {"tool": "prior_art_search_tool", "params": {"query": "AI patents"}}}
"""
        
        workflow_type, intent, tools, params = _parse_advanced_intent_response(response_text)
        
        assert workflow_type == "multi_step"
        assert intent == "research and draft"
        assert "prior_art_search_tool" in tools
        assert "claim_drafting_tool" in tools
        assert "step1" in params


class TestPhase3WorkflowPlanning:
    """Test Phase 3 workflow planning functionality."""
    
    @pytest.mark.asyncio
    async def test_plan_workflow_prior_art_and_draft(self):
        """Test workflow planning for prior art search + claim drafting."""
        state = MultiStepAgentState(
            user_input="find prior art for AI patents and draft 5 claims",
            document_content="test document",
            conversation_history=[],
            available_tools=[
                {"name": "prior_art_search_tool", "description": "Search prior art"},
                {"name": "claim_drafting_tool", "description": "Draft claims"}
            ],
            workflow_plan=[],
            current_step=0,
            total_steps=0,
            step_results={},
            selected_tool="",
            tool_parameters={},
            final_response="",
            intent_type="multi-step workflow",
            execution_metadata={"workflow_type": "multi_step"}
        )
        
        result = await plan_workflow_node(state)
        
        assert len(result["workflow_plan"]) == 2
        assert result["total_steps"] == 2
        assert result["workflow_plan"][0]["tool"] == "prior_art_search_tool"
        assert result["workflow_plan"][1]["tool"] == "claim_drafting_tool"
        assert result["workflow_plan"][1]["depends_on"] == 1
        assert "{prior_art_results}" in result["workflow_plan"][1]["parameters"]["prior_art_context"]
    
    @pytest.mark.asyncio
    async def test_plan_workflow_draft_and_analyze(self):
        """Test workflow planning for claim drafting + analysis."""
        state = MultiStepAgentState(
            user_input="draft 5 claims for blockchain and analyze them",
            document_content="test document",
            conversation_history=[],
            available_tools=[
                {"name": "claim_drafting_tool", "description": "Draft claims"},
                {"name": "claim_analysis_tool", "description": "Analyze claims"}
            ],
            workflow_plan=[],
            current_step=0,
            total_steps=0,
            step_results={},
            selected_tool="",
            tool_parameters={},
            final_response="",
            intent_type="multi-step workflow",
            execution_metadata={"workflow_type": "multi_step"}
        )
        
        result = await plan_workflow_node(state)
        
        assert len(result["workflow_plan"]) == 2
        assert result["workflow_plan"][0]["tool"] == "claim_drafting_tool"
        assert result["workflow_plan"][1]["tool"] == "claim_analysis_tool"
        assert result["workflow_plan"][1]["depends_on"] == 1
        assert "{draft_claims}" in result["workflow_plan"][1]["parameters"]["claims_context"]
    
    @pytest.mark.asyncio
    async def test_plan_workflow_web_search_and_patents(self):
        """Test workflow planning for web search + patent search."""
        state = MultiStepAgentState(
            user_input="search web for blockchain patents and find related patents",
            document_content="",
            conversation_history=[],
            available_tools=[
                {"name": "web_search_tool", "description": "Web search"},
                {"name": "prior_art_search_tool", "description": "Patent search"}
            ],
            workflow_plan=[],
            current_step=0,
            total_steps=0,
            step_results={},
            selected_tool="",
            tool_parameters={},
            final_response="",
            intent_type="multi-step workflow",
            execution_metadata={"workflow_type": "multi_step"}
        )
        
        result = await plan_workflow_node(state)
        
        assert len(result["workflow_plan"]) == 2
        assert result["workflow_plan"][0]["tool"] == "web_search_tool"
        assert result["workflow_plan"][1]["tool"] == "prior_art_search_tool"
        assert result["workflow_plan"][1]["depends_on"] == 1
        assert "{web_search_results}" in result["workflow_plan"][1]["parameters"]["web_context"]
    
    def test_extract_search_query(self):
        """Test search query extraction."""
        query = _extract_search_query("find prior art for AI patents", "prior art")
        assert query == "AI patents"
        
        query = _extract_search_query("search for blockchain technology", "search")
        assert query == "blockchain technology"
        
        query = _extract_search_query("find patents about machine learning", "find")
        assert query == "patents about machine learning"
    
    def test_extract_claim_parameters(self):
        """Test claim parameter extraction."""
        params = _extract_claim_parameters("draft 5 claims for blockchain")
        assert params == "draft 5 claims for blockchain"
        
        params = _extract_claim_parameters("create patent claims about AI")
        assert params == "draft patent claims"


class TestPhase3MultiStepExecution:
    """Test Phase 3 multi-step execution functionality."""
    
    @pytest.mark.asyncio
    async def test_execute_multi_step_success(self):
        """Test successful multi-step execution."""
        # Mock MCP orchestrator
        mock_orchestrator = AsyncMock()
        mock_orchestrator.execute_tool.side_effect = [
            {"success": True, "result": "Prior art search completed", "data": [{"title": "AI Patent 1"}]},
            {"success": True, "result": "Claims drafted successfully", "claims": ["Claim 1", "Claim 2"]}
        ]
        
        # Mock agent service
        with patch('app.services.langgraph_agent.AgentService') as mock_agent_class:
            mock_agent = Mock()
            mock_agent._get_mcp_orchestrator.return_value = mock_orchestrator
            mock_agent_class.return_value = mock_agent
            
            state = MultiStepAgentState(
                user_input="test",
                document_content="",
                conversation_history=[],
                available_tools=[],
                workflow_plan=[
                    {
                        "step": 1,
                        "tool": "prior_art_search_tool",
                        "parameters": {"query": "AI patents"},
                        "depends_on": None,
                        "output_key": "prior_art_results"
                    },
                    {
                        "step": 2,
                        "tool": "claim_drafting_tool",
                        "parameters": {
                            "user_query": "draft claims",
                            "prior_art_context": "{prior_art_results}"
                        },
                        "depends_on": 1,
                        "output_key": "draft_claims"
                    }
                ],
                current_step=0,
                total_steps=2,
                step_results={},
                selected_tool="",
                tool_parameters={},
                final_response="",
                intent_type="multi-step workflow",
                execution_metadata={}
            )
            
            result = await execute_multi_step_node(state)
            
            assert len(result["step_results"]) == 2
            assert result["current_step"] == 2
            assert result["step_results"][1]["success"] is True
            assert result["step_results"][2]["success"] is True
            mock_orchestrator.execute_tool.assert_called()
    
    @pytest.mark.asyncio
    async def test_execute_multi_step_with_context_passing(self):
        """Test multi-step execution with context passing."""
        # Mock MCP orchestrator
        mock_orchestrator = AsyncMock()
        mock_orchestrator.execute_tool.side_effect = [
            {"success": True, "result": "Prior art search completed", "data": [{"title": "AI Patent 1"}]},
            {"success": True, "result": "Claims drafted with context", "claims": ["Claim 1", "Claim 2"]}
        ]
        
        with patch('app.services.langgraph_agent.AgentService') as mock_agent_class:
            mock_agent = Mock()
            mock_agent._get_mcp_orchestrator.return_value = mock_orchestrator
            mock_agent_class.return_value = mock_agent
            
            state = MultiStepAgentState(
                user_input="test",
                document_content="",
                conversation_history=[],
                available_tools=[],
                workflow_plan=[
                    {
                        "step": 1,
                        "tool": "prior_art_search_tool",
                        "parameters": {"query": "AI patents"},
                        "depends_on": None,
                        "output_key": "prior_art_results"
                    },
                    {
                        "step": 2,
                        "tool": "claim_drafting_tool",
                        "parameters": {
                            "user_query": "draft claims",
                            "prior_art_context": "{prior_art_results}"
                        },
                        "depends_on": 1,
                        "output_key": "draft_claims"
                    }
                ],
                current_step=0,
                total_steps=2,
                step_results={},
                selected_tool="",
                tool_parameters={},
                final_response="",
                intent_type="multi-step workflow",
                execution_metadata={}
            )
            
            result = await execute_multi_step_node(state)
            
            # Verify context was passed correctly
            calls = mock_orchestrator.execute_tool.call_args_list
            assert len(calls) == 2
            
            # First call should have original parameters
            first_call_args = calls[0][0]
            assert first_call_args[0] == "prior_art_search_tool"
            assert first_call_args[1]["query"] == "AI patents"
            
            # Second call should have context substitution
            second_call_args = calls[1][0]
            assert second_call_args[0] == "claim_drafting_tool"
            assert "Prior art search completed" in second_call_args[1]["prior_art_context"]
    
    @pytest.mark.asyncio
    async def test_execute_multi_step_error_handling(self):
        """Test multi-step execution error handling."""
        # Mock MCP orchestrator to raise exception on second step
        mock_orchestrator = AsyncMock()
        mock_orchestrator.execute_tool.side_effect = [
            {"success": True, "result": "Prior art search completed"},
            Exception("Tool execution failed")
        ]
        
        with patch('app.services.langgraph_agent.AgentService') as mock_agent_class:
            mock_agent = Mock()
            mock_agent._get_mcp_orchestrator.return_value = mock_orchestrator
            mock_agent_class.return_value = mock_agent
            
            state = MultiStepAgentState(
                user_input="test",
                document_content="",
                conversation_history=[],
                available_tools=[],
                workflow_plan=[
                    {
                        "step": 1,
                        "tool": "prior_art_search_tool",
                        "parameters": {"query": "AI patents"},
                        "depends_on": None,
                        "output_key": "prior_art_results"
                    },
                    {
                        "step": 2,
                        "tool": "claim_drafting_tool",
                        "parameters": {"user_query": "draft claims"},
                        "depends_on": 1,
                        "output_key": "draft_claims"
                    }
                ],
                current_step=0,
                total_steps=2,
                step_results={},
                selected_tool="",
                tool_parameters={},
                final_response="",
                intent_type="multi-step workflow",
                execution_metadata={}
            )
            
            result = await execute_multi_step_node(state)
            
            assert len(result["step_results"]) == 2
            assert result["step_results"][1]["success"] is True
            assert result["step_results"][2]["success"] is False
            assert "Tool execution failed" in result["step_results"][2]["error"]
    
    def test_prepare_parameters_with_context(self):
        """Test parameter preparation with context substitution."""
        step_results = {
            1: {"success": True, "result": "Prior art search results"},
            2: {"success": True, "result": "Draft claims results"}
        }
        
        state = MultiStepAgentState(
            user_input="test",
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
        
        parameters = {
            "user_query": "draft claims",
            "prior_art_context": "{prior_art_results}",
            "claims_context": "{draft_claims}",
            "document_reference": "{document_content}",
            "normal_param": "normal value"
        }
        
        result = _prepare_parameters_with_context(parameters, step_results, state)
        
        assert result["user_query"] == "draft claims"
        assert result["prior_art_context"] == "Prior art search results"
        assert result["claims_context"] == "Draft claims results"
        assert result["document_reference"] == "test document"
        assert result["normal_param"] == "normal value"


class TestPhase3ResponseGeneration:
    """Test Phase 3 multi-step response generation."""
    
    @pytest.mark.asyncio
    async def test_generate_multi_step_response_success(self):
        """Test multi-step response generation for successful execution."""
        state = MultiStepAgentState(
            user_input="test",
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
            intent_type="multi-step workflow",
            execution_metadata={}
        )
        
        result = await generate_multi_step_response_node(state)
        
        assert "Prior Art Search Results" in result["final_response"]
        assert "Draft Claims" in result["final_response"]
        assert "Prior art search results" in result["final_response"]
        assert "Draft claims results" in result["final_response"]
        assert result["intent_type"] == "multi_step_workflow"
    
    @pytest.mark.asyncio
    async def test_generate_multi_step_response_partial_failure(self):
        """Test multi-step response generation for partial failure."""
        state = MultiStepAgentState(
            user_input="test",
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
                2: {"success": False, "error": "Tool execution failed"}
            },
            selected_tool="",
            tool_parameters={},
            final_response="",
            intent_type="multi-step workflow",
            execution_metadata={}
        )
        
        result = await generate_multi_step_response_node(state)
        
        assert "completed some steps but encountered issues" in result["final_response"]
        assert "Step 2 (claim_drafting_tool) failed" in result["final_response"]
        assert "Tool execution failed" in result["final_response"]
    
    @pytest.mark.asyncio
    async def test_generate_multi_step_response_no_results(self):
        """Test multi-step response generation with no results."""
        state = MultiStepAgentState(
            user_input="test",
            document_content="",
            conversation_history=[],
            available_tools=[],
            workflow_plan=[],
            current_step=0,
            total_steps=0,
            step_results={},
            selected_tool="",
            tool_parameters={},
            final_response="",
            intent_type="multi-step workflow",
            execution_metadata={}
        )
        
        result = await generate_multi_step_response_node(state)
        
        assert "not sure how to help" in result["final_response"]


class TestPhase3AdvancedAgentGraph:
    """Test Phase 3 advanced agent graph functionality."""
    
    def test_create_advanced_agent_graph(self):
        """Test advanced agent graph creation."""
        graph = create_advanced_agent_graph()
        assert graph is not None
    
    def test_get_advanced_agent_graph_singleton(self):
        """Test that get_advanced_agent_graph returns singleton."""
        graph1 = get_advanced_agent_graph()
        graph2 = get_advanced_agent_graph()
        assert graph1 is graph2
    
    @pytest.mark.asyncio
    async def test_full_advanced_workflow_multi_step(self):
        """Test complete advanced workflow for multi-step execution."""
        graph = get_advanced_agent_graph()
        
        initial_state = MultiStepAgentState(
            user_input="find prior art for AI patents and draft 5 claims",
            document_content="test document",
            conversation_history=[],
            available_tools=[
                {"name": "prior_art_search_tool", "description": "Search prior art"},
                {"name": "claim_drafting_tool", "description": "Draft claims"}
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
        
        # Mock the MCP orchestrator for execution
        with patch('app.services.langgraph_agent.AgentService') as mock_agent_class:
            mock_agent = Mock()
            mock_orchestrator = AsyncMock()
            mock_orchestrator.execute_tool.side_effect = [
                {"success": True, "result": "Prior art search completed"},
                {"success": True, "result": "Claims drafted successfully"}
            ]
            mock_agent._get_mcp_orchestrator.return_value = mock_orchestrator
            mock_agent._get_llm_client.return_value = None  # Use simple detection
            mock_agent_class.return_value = mock_agent
            
            result = await graph.ainvoke(initial_state)
            
            assert result["intent_type"] == "multi-step workflow"
            assert result["total_steps"] == 2
            assert len(result["workflow_plan"]) == 2
            assert result["final_response"] is not None


class TestPhase3AgentServiceIntegration:
    """Test Phase 3 integration with AgentService."""
    
    @pytest.mark.asyncio
    async def test_agent_service_advanced_langgraph(self):
        """Test AgentService advanced LangGraph method."""
        # Mock MCP orchestrator
        mock_orchestrator = AsyncMock()
        mock_orchestrator.execute_tool.side_effect = [
            {"success": True, "result": "Prior art search completed"},
            {"success": True, "result": "Claims drafted successfully"}
        ]
        
        # Mock agent service
        with patch('app.services.agent.AgentService') as mock_agent_class:
            mock_agent = Mock()
            mock_agent._get_mcp_orchestrator.return_value = mock_orchestrator
            mock_agent._get_llm_client.return_value = None  # Use simple detection
            mock_agent_class.return_value = mock_agent
            
            agent_service = AgentService()
            
            result = await agent_service.process_user_message_advanced_langgraph(
                user_message="find prior art for AI patents and draft 5 claims",
                document_content="test document",
                available_tools=[
                    {"name": "prior_art_search_tool", "description": "Search prior art"},
                    {"name": "claim_drafting_tool", "description": "Draft claims"}
                ],
                frontend_chat_history=[]
            )
            
            assert result["success"] is True
            assert result["intent_type"] == "multi-step workflow"
            assert result["workflow_metadata"]["total_steps"] == 2
            assert result["workflow_metadata"]["workflow_type"] == "multi_step"
            assert "Prior art search completed" in result["response"] or "Claims drafted successfully" in result["response"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
