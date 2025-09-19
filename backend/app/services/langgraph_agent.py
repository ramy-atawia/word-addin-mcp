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
    
    Phase 1: Basic implementation that reuses existing logic.
    """
    logger.debug("LangGraph Phase 1: Detecting intent")
    
    # For Phase 1, we'll use a simple approach
    # In Phase 2, this will be fully implemented
    user_input = state["user_input"].lower()
    
    # Simple intent detection
    if "prior art" in user_input or "search" in user_input:
        selected_tool = "prior_art_search_tool"
        intent_type = "tool_execution"
    elif "draft" in user_input or "claim" in user_input:
        selected_tool = "claim_drafting_tool"
        intent_type = "tool_execution"
    elif "analyze" in user_input:
        selected_tool = "claim_analysis_tool"
        intent_type = "tool_execution"
    else:
        selected_tool = ""
        intent_type = "conversation"
    
    return {
        **state,
        "selected_tool": selected_tool,
        "intent_type": intent_type,
        "tool_parameters": {}
    }


async def execute_tool_node(state: AgentState) -> AgentState:
    """
    Execute the selected tool.
    
    Phase 1: Basic implementation that will be enhanced in Phase 2.
    """
    logger.debug(f"LangGraph Phase 1: Executing tool {state['selected_tool']}")
    
    if not state["selected_tool"]:
        return {**state, "tool_result": None}
    
    # For Phase 1, we'll return a placeholder
    # In Phase 2, this will integrate with MCP orchestrator
    tool_result = f"Phase 1: Tool {state['selected_tool']} would be executed here"
    
    return {**state, "tool_result": tool_result}


async def generate_response_node(state: AgentState) -> AgentState:
    """
    Generate final response from tool result.
    
    Phase 1: Basic response generation.
    """
    logger.debug("LangGraph Phase 1: Generating response")
    
    if state["intent_type"] == "conversation":
        final_response = "Phase 1: I'm here to help! (LangGraph foundation active)"
    elif state["tool_result"]:
        final_response = f"Phase 1: {state['tool_result']}"
    else:
        final_response = "Phase 1: I'm not sure how to help with that request."
    
    return {**state, "final_response": final_response}


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
