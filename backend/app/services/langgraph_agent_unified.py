"""
Simplified LangGraph Agent Service

A clean, unified LangGraph implementation that handles both conversation
and tool workflows without over-complication.

Features:
- Simple unified state management
- Clear workflow routing
- Minimal dependencies and error handling
- Clean, maintainable code
"""

import structlog
import json
from typing import TypedDict, List, Dict, Any, Optional

logger = structlog.get_logger()

# LangGraph import - fail clearly if not available
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.error("LangGraph is required but not installed. Please install with: pip install langgraph")
    raise ImportError("LangGraph is required for this agent service. Install with: pip install langgraph")


class AgentState(TypedDict):
    """Unified agent state for all workflows."""
    # Input
    user_input: str
    document_content: Optional[str]
    conversation_history: List[Dict[str, Any]]
    available_tools: List[Dict[str, Any]]
    
    # Processing
    intent_type: str  # 'conversation' or 'tool_workflow'
    workflow_plan: List[Dict[str, Any]]
    current_step: int
    step_results: Dict[str, Any]
    
    # Output
    final_response: str


async def detect_intent_node(state: AgentState) -> AgentState:
    """Detect whether this is a conversation or tool workflow."""
    logger.debug("Detecting intent")
    
    user_input = state["user_input"]
    available_tools = state.get("available_tools", [])
    
    # Simple pattern-based intent detection first
    intent_type, workflow_plan = _simple_intent_detection(user_input, available_tools)
    
    # If we have tools and it's unclear, use LLM
    if intent_type == "unclear" and available_tools:
        try:
            intent_type, workflow_plan = await _llm_intent_detection(state)
        except Exception as e:
            logger.warning(f"LLM intent detection failed: {e}")
            # Default to conversation for safety
            intent_type = "conversation"
            workflow_plan = []
    
    return {
        **state,
        "intent_type": intent_type,
        "workflow_plan": workflow_plan,
        "current_step": 0,
        "step_results": {}
    }


def _simple_intent_detection(user_input: str, available_tools: List[Dict]) -> tuple[str, List[Dict]]:
    """Simple pattern-based intent detection."""
    user_lower = user_input.lower().strip()
    
    # Clear conversation indicators
    conversation_patterns = [
        "hello", "hi", "hey", "how are you", "what's up",
        "draft a letter", "write an email", "compose a message",
        "draft a report", "write a document", "help me write"
    ]
    
    if any(pattern in user_lower for pattern in conversation_patterns):
        return "conversation", []
    
    # Clear tool workflow indicators
    tool_patterns = {
        "prior_art_search_tool": ["prior art", "search patents", "find patents"],
        "claim_drafting_tool": ["draft claims", "write claims", "generate claims"],
        "claim_analysis_tool": ["analyze claims", "review claims", "check claims"],
        "web_search_tool": ["web search", "search for", "find information"]
    }
    
    tool_names = [tool.get("name", "") for tool in available_tools]
    
    for tool_name in tool_names:
        if tool_name in tool_patterns:
            patterns = tool_patterns[tool_name]
            if any(pattern in user_lower for pattern in patterns):
                # Create simple single-step workflow
                workflow = [{
                    "step": 1,
                    "tool": tool_name,
                    "params": _extract_tool_params(user_input, tool_name),
                    "output_key": f"{tool_name}_result"
                }]
                return "tool_workflow", workflow
    
    # Default to unclear for LLM analysis
    return "unclear", []


def _extract_tool_params(user_input: str, tool_name: str) -> Dict[str, Any]:
    """Extract basic parameters for tools."""
    if tool_name == "prior_art_search_tool":
        # Extract search query
        query = user_input
        for prefix in ["prior art search", "search for", "find"]:
            if prefix in user_input.lower():
                query = user_input.lower().replace(prefix, "").strip()
                break
        return {"query": query or user_input}
    
    elif tool_name == "claim_drafting_tool":
        # Extract user query - the tool doesn't use num_claims parameter
        return {
            "user_query": user_input
        }
    
    elif tool_name == "web_search_tool":
        # Extract search query
        query = user_input
        for prefix in ["web search", "search for", "find"]:
            if prefix in user_input.lower():
                query = user_input.lower().replace(prefix, "").strip()
                break
        return {"query": query or user_input}
    
    # Default: pass user input
    return {"query": user_input}


async def _llm_intent_detection(state: AgentState) -> tuple[str, List[Dict]]:
    """Use LLM for intent detection when patterns are unclear."""
    user_input = state["user_input"]
    available_tools = state.get("available_tools", [])
    
    from app.services.agent import AgentService
    agent_service = AgentService()
    
    llm_client = agent_service._get_llm_client()
    if not llm_client:
        # No fallback - this is a real dependency failure
        raise RuntimeError("LLM client is required for intent detection but not available")
    
    # Create tool list
    tool_list = "\n".join([f"- {tool['name']}: {tool.get('description', '')}" 
                          for tool in available_tools])
    
    prompt = f"""Analyze this user request and determine if it needs tools or is just conversation.

User request: "{user_input}"

Available tools:
{tool_list}

Respond with exactly one of:
- CONVERSATION (for greetings, general writing, non-tool requests)
- TOOL_WORKFLOW (for patent searches, claim drafting, analysis)

If TOOL_WORKFLOW, also provide a JSON plan like:
[{{"step": 1, "tool": "tool_name", "params": {{"key": "value"}}, "output_key": "result_key"}}]

Format:
TYPE: [CONVERSATION or TOOL_WORKFLOW]
PLAN: [JSON array or empty for conversation]"""
    
    response = llm_client.generate_text(
        prompt=prompt,
        max_tokens=1000,
        temperature=0.0
    )
    
    if not response.get("success"):
        raise RuntimeError(f"LLM intent detection failed: {response.get('error', 'Unknown error')}")
    
    return _parse_llm_intent(response.get("text", ""))


def _parse_llm_intent(response_text: str) -> tuple[str, List[Dict]]:
    """Parse LLM intent detection response."""
    lines = response_text.strip().split('\n')
    intent_type = "conversation"
    workflow_plan = []
    
    for line in lines:
        line = line.strip()
        if line.startswith("TYPE:"):
            type_value = line.split(":", 1)[1].strip().upper()
            if type_value == "TOOL_WORKFLOW":
                intent_type = "tool_workflow"
            else:
                intent_type = "conversation"
        elif line.startswith("PLAN:") and intent_type == "tool_workflow":
            plan_text = line.split(":", 1)[1].strip()
            if plan_text and plan_text != "empty":
                try:
                    workflow_plan = json.loads(plan_text)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse workflow plan from LLM")
                    workflow_plan = []
    
    return intent_type, workflow_plan


async def execute_workflow_node(state: AgentState) -> AgentState:
    """Execute the workflow plan step by step."""
    logger.debug("Executing workflow")
    
    workflow_plan = state.get("workflow_plan", [])
    current_step = state.get("current_step", 0)
    step_results = state.get("step_results", {})
    
    if current_step >= len(workflow_plan):
        return state  # All steps completed
    
    try:
        from app.services.agent import AgentService
        agent_service = AgentService()
        
        orchestrator = agent_service._get_mcp_orchestrator()
        if not orchestrator:
            raise RuntimeError("MCP orchestrator is required for tool execution but not available")
        
        # Get current step
        step = workflow_plan[current_step]
        tool_name = step["tool"]
        params = step["params"]
        output_key = step["output_key"]
        
        # Add context from previous steps if needed
        params = _add_context_to_params(params, step_results)
        
        # Execute tool
        logger.debug(f"Executing {tool_name} with params: {params}")
        result = await orchestrator.execute_tool(tool_name, params)
        
        # Store result
        step_results[output_key] = result
        
        return {
            **state,
            "current_step": current_step + 1,
            "step_results": step_results
        }
        
    except Exception as e:
        logger.error(f"Step {current_step} failed: {e}")
        # Store error and continue
        step_results[f"step_{current_step}_error"] = str(e)
        return {
            **state,
            "current_step": current_step + 1,
            "step_results": step_results
        }


def _add_context_to_params(params: Dict[str, Any], step_results: Dict[str, Any]) -> Dict[str, Any]:
    """Add context from previous steps to parameters."""
    enhanced_params = params.copy()
    
    # Simple context injection
    for key, value in enhanced_params.items():
        if isinstance(value, str) and "{{" in value and "}}" in value:
            for result_key, result_value in step_results.items():
                placeholder = f"{{{{{result_key}}}}}"
                if placeholder in value:
                    context_text = str(result_value.get("result", result_value))
                    enhanced_params[key] = value.replace(placeholder, context_text)
    
    return enhanced_params


async def generate_response_node(state: AgentState) -> AgentState:
    """Generate final response based on intent type."""
    logger.debug("Generating response")
    
    intent_type = state.get("intent_type", "conversation")
    
    if intent_type == "conversation":
        final_response = await _generate_conversation_response(state)
    else:
        final_response = await _generate_workflow_response(state)
    
    return {
        **state,
        "final_response": final_response
    }


async def _generate_conversation_response(state: AgentState) -> str:
    """Generate conversational response."""
    user_input = state["user_input"]
    conversation_history = state.get("conversation_history", [])
    
    try:
        from app.services.agent import AgentService
        agent_service = AgentService()
        
        llm_client = agent_service._get_llm_client()
        if not llm_client:
            raise RuntimeError("LLM client is required for conversation but not available")
        
        # Build context
        context = ""
        if conversation_history:
            recent = conversation_history[-3:]  # Last 3 messages
            context = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" 
                               for msg in recent])
        
        prompt = f"""You are a helpful AI assistant. Respond naturally to the user's message.

Current message: "{user_input}"

Recent conversation:
{context if context else "No previous conversation"}

Provide a helpful, natural response. Be concise but complete."""
        
        response = llm_client.generate_text(
            prompt=prompt,
            max_tokens=800,
            temperature=0.7
        )
        
        if response.get("success"):
            return response.get("text", "")
        else:
            raise RuntimeError(f"LLM conversation generation failed: {response.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Conversation response generation failed: {e}")
        raise


async def _generate_workflow_response(state: AgentState) -> str:
    """Generate response from workflow results."""
    step_results = state.get("step_results", {})
    workflow_plan = state.get("workflow_plan", [])
    
    if not step_results:
        return "I wasn't able to complete that request."
    
    response_parts = []
    
    for step in workflow_plan:
        output_key = step["output_key"]
        if output_key in step_results:
            result = step_results[output_key]
            
            if isinstance(result, dict) and result.get("success", True):
                # Extract formatted content
                content = result.get("result", str(result))
                
                # Simple tool name formatting
                tool_name = step["tool"].replace("_tool", "").replace("_", " ").title()
                response_parts.append(f"**{tool_name}:**\n{content}")
            elif f"step_{step['step']-1}_error" in step_results:
                error_msg = step_results[f"step_{step['step']-1}_error"]
                response_parts.append(f"Step {step['step']} failed: {error_msg}")
    
    if response_parts:
        return "\n\n".join(response_parts)
    else:
        return "I completed the workflow but didn't get clear results."


def _route_after_intent(state: AgentState) -> str:
    """Route after intent detection."""
    intent_type = state.get("intent_type", "conversation")
    workflow_plan = state.get("workflow_plan", [])
    
    if intent_type == "tool_workflow" and workflow_plan:
        return "execute_workflow"
    else:
        return "generate_response"


def _route_workflow_continue(state: AgentState) -> str:
    """Route workflow continuation."""
    current_step = state.get("current_step", 0)
    workflow_plan = state.get("workflow_plan", [])
    
    if current_step < len(workflow_plan):
        return "execute_workflow"
    else:
        return "generate_response"


def create_agent_graph():
    """Create the simplified LangGraph workflow."""
    logger.info("Creating simplified LangGraph workflow")
    
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("detect_intent", detect_intent_node)
    workflow.add_node("execute_workflow", execute_workflow_node)
    workflow.add_node("generate_response", generate_response_node)
    
    # Add edges
    workflow.add_edge("__start__", "detect_intent")
    workflow.add_conditional_edges(
        "detect_intent",
        _route_after_intent,
        {
            "execute_workflow": "execute_workflow",
            "generate_response": "generate_response"
        }
    )
    workflow.add_conditional_edges(
        "execute_workflow",
        _route_workflow_continue,
        {
            "execute_workflow": "execute_workflow",
            "generate_response": "generate_response"
        }
    )
    workflow.add_edge("generate_response", END)
    
    return workflow.compile()


# Global graph instance with lazy initialization
_agent_graph = None

def get_agent_graph():
    """Get the compiled agent graph."""
    global _agent_graph
    if _agent_graph is None:
        _agent_graph = create_agent_graph()
    return _agent_graph