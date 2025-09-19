"""
LangGraph Agent Service - Phase 1: Foundation Setup

This module provides the basic LangGraph workflow structure for the Word Add-in MCP Project.
Phase 1 focuses on establishing the foundation with basic workflow nodes and state management.

Features:
- Basic workflow structure with nodes and edges
- State management for single-tool execution
- Integration with existing AgentService
- Feature flag support for gradual rollout
"""

import structlog
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END

logger = structlog.get_logger()


class AgentState(TypedDict):
    """Basic agent state for Phase 1 - single tool execution only."""
    
    # User input and context
    user_input: str
    document_content: str
    conversation_history: List[Dict[str, Any]]
    available_tools: List[Dict[str, Any]]
    
    # Tool execution (single tool)
    selected_tool: str
    tool_parameters: Dict[str, Any]
    tool_result: Any
    
    # Response generation
    final_response: str
    intent_type: str


async def detect_intent_node(state: AgentState) -> AgentState:
    """
    Detect user intent and select single tool.
    
    Phase 2: Enhanced implementation with LLM-based intent detection.
    """
    logger.debug("LangGraph Phase 2: Detecting intent with LLM")
    
    user_input = state["user_input"]
    available_tools = state["available_tools"]
    
    # Phase 2: Use LLM for intent detection
    try:
        from app.services.agent import AgentService
        agent_service = AgentService()
        
        # Get LLM client
        llm_client = agent_service._get_llm_client()
        if not llm_client:
            # Fallback to simple detection
            return await _simple_intent_detection(state)
        
        # Create tool descriptions for LLM
        tool_descriptions = []
        for tool in available_tools:
            tool_descriptions.append(f"- {tool['name']}: {tool.get('description', 'No description')}")
        
        tools_text = "\n".join(tool_descriptions) if tool_descriptions else "No tools available"
        
        # LLM prompt for intent detection
        prompt = f"""
You are an AI assistant that analyzes user queries and selects the most appropriate tool.

Available tools:
{tools_text}

User query: "{user_input}"

Analyze the user's intent and select the most appropriate tool. If no tool is suitable, respond with "conversation".

Respond in this exact format:
TOOL: [tool_name or "conversation"]
INTENT: [brief description of intent]
PARAMETERS: [JSON object with tool parameters, or empty object {}]

Examples:
- "find prior art for AI patents" → TOOL: prior_art_search_tool, INTENT: search prior art, PARAMETERS: {{"query": "AI patents"}}
- "draft 5 claims for blockchain" → TOOL: claim_drafting_tool, INTENT: draft claims, PARAMETERS: {{"user_query": "draft 5 claims for blockchain", "num_claims": 5}}
- "hello how are you" → TOOL: conversation, INTENT: greeting, PARAMETERS: {{}}
"""
        
        # Get LLM response
        response = await llm_client.ainvoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Parse LLM response
        selected_tool, intent_type, tool_parameters = _parse_llm_intent_response(response_text)
        
        logger.debug(f"LangGraph Phase 2: LLM detected tool '{selected_tool}' with intent '{intent_type}'")
        
        return {
            **state,
            "selected_tool": selected_tool,
            "intent_type": intent_type,
            "tool_parameters": tool_parameters
        }
        
    except Exception as e:
        logger.warning(f"LangGraph Phase 2: LLM intent detection failed, using fallback: {e}")
        return await _simple_intent_detection(state)


async def _simple_intent_detection(state: AgentState) -> AgentState:
    """Fallback simple intent detection for Phase 2."""
    user_input = state["user_input"].lower()
    
    # Enhanced simple detection
    if "prior art" in user_input or "search" in user_input or "find" in user_input:
        selected_tool = "prior_art_search_tool"
        intent_type = "tool_execution"
        tool_parameters = {"query": user_input}
    elif "draft" in user_input or "claim" in user_input:
        selected_tool = "claim_drafting_tool"
        intent_type = "tool_execution"
        tool_parameters = {"user_query": user_input}
    elif "analyze" in user_input or "analysis" in user_input:
        selected_tool = "claim_analysis_tool"
        intent_type = "tool_execution"
        tool_parameters = {"user_query": user_input}
    else:
        selected_tool = ""
        intent_type = "conversation"
        tool_parameters = {}
    
    return {
        **state,
        "selected_tool": selected_tool,
        "intent_type": intent_type,
        "tool_parameters": tool_parameters
    }


def _parse_llm_intent_response(response_text: str) -> tuple[str, str, dict]:
    """Parse LLM response for intent detection."""
    try:
        lines = response_text.strip().split('\n')
        tool = "conversation"
        intent = "conversation"
        parameters = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith("TOOL:"):
                tool = line.split(":", 1)[1].strip()
            elif line.startswith("INTENT:"):
                intent = line.split(":", 1)[1].strip()
            elif line.startswith("PARAMETERS:"):
                params_text = line.split(":", 1)[1].strip()
                if params_text and params_text != "{}":
                    try:
                        import json
                        parameters = json.loads(params_text)
                    except json.JSONDecodeError:
                        parameters = {}
        
        return tool, intent, parameters
        
    except Exception as e:
        logger.warning(f"Failed to parse LLM intent response: {e}")
        return "conversation", "conversation", {}


async def execute_tool_node(state: AgentState) -> AgentState:
    """
    Execute the selected tool.
    
    Phase 2: Real tool execution with MCP orchestrator integration.
    """
    logger.debug(f"LangGraph Phase 2: Executing tool {state['selected_tool']}")
    
    if not state["selected_tool"]:
        return {**state, "tool_result": None}
    
    try:
        # Phase 2: Real tool execution
        from app.services.agent import AgentService
        agent_service = AgentService()
        
        # Get MCP orchestrator
        orchestrator = agent_service._get_mcp_orchestrator()
        if not orchestrator:
            raise RuntimeError("MCP orchestrator not available")
        
        # Execute tool with parameters
        tool_name = state["selected_tool"]
        tool_parameters = state.get("tool_parameters", {})
        
        logger.debug(f"LangGraph Phase 2: Executing {tool_name} with params: {tool_parameters}")
        
        # Execute tool via MCP orchestrator
        tool_result = await orchestrator.execute_tool(tool_name, tool_parameters)
        
        logger.debug(f"LangGraph Phase 2: Tool execution completed successfully")
        
        return {**state, "tool_result": tool_result}
        
    except Exception as e:
        logger.error(f"LangGraph Phase 2: Tool execution failed: {str(e)}")
        
        # Return error result instead of raising
        error_result = {
            "success": False,
            "error": str(e),
            "tool_name": state["selected_tool"],
            "message": f"Tool execution failed: {str(e)}"
        }
        
        return {**state, "tool_result": error_result}


async def generate_response_node(state: AgentState) -> AgentState:
    """
    Generate final response from tool result.
    
    Phase 2: Enhanced response generation with LLM formatting.
    """
    logger.debug("LangGraph Phase 2: Generating response with LLM")
    
    if state["intent_type"] == "conversation":
        final_response = "I'm here to help! How can I assist you with your patent-related tasks?"
    elif state["tool_result"]:
        # Phase 2: Use LLM to format tool results
        try:
            from app.services.agent import AgentService
            agent_service = AgentService()
            
            # Get LLM client
            llm_client = agent_service._get_llm_client()
            if not llm_client:
                # Fallback to simple formatting
                final_response = await _simple_response_formatting(state)
            else:
                # Use LLM for response formatting
                final_response = await _llm_response_formatting(state, llm_client)
                
        except Exception as e:
            logger.warning(f"LangGraph Phase 2: LLM response formatting failed, using fallback: {e}")
            final_response = await _simple_response_formatting(state)
    else:
        final_response = "I'm not sure how to help with that request. Could you please provide more details?"
    
    return {**state, "final_response": final_response}


async def _llm_response_formatting(state: AgentState, llm_client) -> str:
    """Use LLM to format tool results into user-friendly responses."""
    tool_name = state["selected_tool"]
    tool_result = state["tool_result"]
    user_input = state["user_input"]
    
    # Check if tool execution was successful
    if isinstance(tool_result, dict) and not tool_result.get("success", True):
        # Handle error case
        error_msg = tool_result.get("error", "Unknown error")
        return f"I encountered an issue while executing the {tool_name}: {error_msg}"
    
    # Create prompt for response formatting
    prompt = f"""
You are an AI assistant that formats tool execution results into user-friendly responses.

User's original request: "{user_input}"
Tool executed: {tool_name}
Tool result: {tool_result}

Format the tool result into a clear, helpful response for the user. Focus on:
1. Answering their specific question
2. Highlighting key findings or results
3. Providing actionable insights
4. Being concise but comprehensive

Response should be professional and helpful for patent-related work.
"""
    
    try:
        response = await llm_client.ainvoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        logger.warning(f"LLM response formatting failed: {e}")
        return await _simple_response_formatting(state)


async def _simple_response_formatting(state: AgentState) -> str:
    """Fallback simple response formatting for Phase 2."""
    tool_name = state["selected_tool"]
    tool_result = state["tool_result"]
    
    # Check if tool execution was successful
    if isinstance(tool_result, dict) and not tool_result.get("success", True):
        error_msg = tool_result.get("error", "Unknown error")
        return f"I encountered an issue while executing the {tool_name}: {error_msg}"
    
    # Simple formatting based on tool type
    if tool_name == "prior_art_search_tool":
        return f"Here are the prior art search results:\n\n{tool_result}"
    elif tool_name == "claim_drafting_tool":
        return f"Here are the drafted claims:\n\n{tool_result}"
    elif tool_name == "claim_analysis_tool":
        return f"Here's the claim analysis:\n\n{tool_result}"
    else:
        return f"Tool execution completed:\n\n{tool_result}"


def create_basic_agent_graph() -> StateGraph:
    """
    Create basic LangGraph workflow for Phase 1.
    
    This establishes the foundation with:
    - Intent detection
    - Single tool execution
    - Response generation
    
    Phase 2 will add real tool execution.
    Phase 3 will add multi-step workflows.
    """
    logger.info("Creating LangGraph Phase 1 workflow")
    
    # Create the workflow
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("intent_detection", detect_intent_node)
    workflow.add_node("tool_execution", execute_tool_node)
    workflow.add_node("response_generation", generate_response_node)
    
    # Add edges (simple linear flow for Phase 1)
    workflow.add_edge("intent_detection", "tool_execution")
    workflow.add_edge("tool_execution", "response_generation")
    workflow.add_edge("response_generation", END)
    
    # Set entry point
    workflow.set_entry_point("intent_detection")
    
    logger.info("LangGraph Phase 1 workflow created successfully")
    return workflow.compile()


# Global instance for lazy initialization
_basic_agent_graph = None


def get_basic_agent_graph() -> StateGraph:
    """Get the basic agent graph instance."""
    global _basic_agent_graph
    if _basic_agent_graph is None:
        _basic_agent_graph = create_basic_agent_graph()
    return _basic_agent_graph
