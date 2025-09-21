"""
Unified LangGraph Agent Service

A simplified, unified LangGraph implementation that handles both single-tool
and multi-step workflows in one clean architecture.

Features:
- Single unified state management
- Intelligent workflow detection
- Context-aware tool execution
- Clean, maintainable code
"""

import structlog
from typing import TypedDict, List, Dict, Any, Optional
from unittest.mock import Mock

logger = structlog.get_logger()

# Conditional LangGraph import
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    # Create mock classes for when LangGraph is not available
    class StateGraph:
        def __init__(self, state_type):
            pass
        def add_node(self, name, func):
            pass
        def add_edge(self, from_node, to_node):
            pass
        def add_conditional_edges(self, from_node, condition_func, mapping):
            pass
        def compile(self):
            return Mock()
    
    class END:
        pass


class AgentState(TypedDict):
    """Unified agent state for both single-tool and multi-step workflows."""
    
    # User input and context
    user_input: str
    document_content: str
    conversation_history: List[Dict[str, Any]]
    available_tools: List[Dict[str, Any]]
    
    # Tool execution
    selected_tool: str
    tool_parameters: Dict[str, Any]
    tool_result: Any
    
    # Response generation
    final_response: str
    intent_type: str
    
    # Multi-step workflow (optional)
    workflow_plan: Optional[List[Dict[str, Any]]]
    current_step: int
    total_steps: int
    step_results: Dict[str, Any]


async def detect_intent_node(state: AgentState) -> AgentState:
    """
    Detect user intent and determine if single-tool or multi-step workflow is needed.
    """
    logger.debug("Detecting intent and workflow type")
    
    user_input = state["user_input"]
    available_tools = state["available_tools"]
    conversation_history = state.get("conversation_history", [])
    document_content = state.get("document_content", "")
    
    from app.services.agent import AgentService
    agent_service = AgentService()
    
    # Get LLM client
    llm_client = agent_service._get_llm_client()
    if not llm_client:
        raise RuntimeError("LLM client not available - cannot perform intent detection")
    
    # Create tool descriptions for LLM
    tool_descriptions = []
    for tool in available_tools:
        tool_descriptions.append(f"- {tool['name']}: {tool.get('description', 'No description')}")
    
    tools_text = "\n".join(tool_descriptions) if tool_descriptions else "No tools available"
    
    # Prepare conversation history context
    conversation_context = ""
    if conversation_history:
        recent_history = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
        history_text = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in recent_history
        ])
        conversation_context = f"{history_text}"
    
    # Prepare document content context
    document_context = ""
    if document_content:
        doc_preview = document_content[:10000] + "..." if len(document_content) > 10000 else document_content
        document_context = f"{doc_preview}"
    
    # LLM prompt for intent detection
    prompt = f"""
You are an AI assistant that analyzes user queries and determines the appropriate workflow.

Available tools:
{tools_text}

## CURRENT USER MESSAGE:
"{user_input}"

## CONVERSATION HISTORY (for context only):
{conversation_context if conversation_context else "No previous conversation."}

## DOCUMENT CONTENT (for context only):
{document_context if document_context else "No document content."}

CRITICAL: Analyze ONLY the CURRENT USER MESSAGE above. The conversation history and document content are provided for context only and should NOT influence your workflow decision unless the current message explicitly references them.

Analyze the user's intent and determine if this requires:
1. SINGLE_TOOL: One tool execution (e.g., "search for AI patents", "draft 5 claims for blockchain")
2. MULTI_STEP: Multiple sequential tool executions (e.g., "search for AI patents then draft 5 claims")
3. CONVERSATION: General conversation (e.g., "hello how are you", "draft a letter", "write an email")

IMPORTANT RULES:
- PRIORITIZE the current user message over conversation history
- Simple greetings like "hi", "hello", "hey" should ALWAYS be CONVERSATION
- Only use SINGLE_TOOL for PATENT-RELATED tasks (search, prior art, claim drafting, claim analysis)
- Use CONVERSATION for general requests like "draft a letter", "write an email", "compose a message"
- Extract the actual search terms from the CURRENT user query for patent-related searches
- For patent claim drafting, use "draft X claims for [topic]" format
- "prior art search" or "prior art" should ALWAYS use prior_art_search_tool
- "draft claims" or "draft X claims" should use claim_drafting_tool
- "web search" or "search for" should use web_search_tool
- "draft a letter", "write an email", "compose a message" should ALWAYS use CONVERSATION
- Only use claim_drafting_tool for PATENT CLAIM drafting, not general document drafting

IMPORTANT: Extract the actual search terms from the CURRENT user query only. For example:
- "web search ramy atawia then prior art search" → extract "ramy atawia" for web search
- "search for blockchain technology" → extract "blockchain technology"
- "prior art search AI patents" → extract "AI patents"

Respond in this exact format:
WORKFLOW_TYPE: [SINGLE_TOOL, MULTI_STEP, or CONVERSATION]
TOOL: [tool_name for single tool, or first tool for multi-step, or empty for conversation]
INTENT: [brief description of intent]
PARAMETERS: [JSON object with tool parameters]

Examples:
- "web search ramy atawia then prior art search" → WORKFLOW_TYPE: MULTI_STEP, TOOL: web_search_tool, INTENT: web search then prior art, PARAMETERS: {{"query": "ramy atawia"}}
- "prior art search" → WORKFLOW_TYPE: SINGLE_TOOL, TOOL: prior_art_search_tool, INTENT: search prior art, PARAMETERS: {{"query": "prior art search"}}
- "find prior art for AI patents" → WORKFLOW_TYPE: SINGLE_TOOL, TOOL: prior_art_search_tool, INTENT: search prior art, PARAMETERS: {{"query": "AI patents"}}
- "search for blockchain patents" → WORKFLOW_TYPE: SINGLE_TOOL, TOOL: prior_art_search_tool, INTENT: search prior art, PARAMETERS: {{"query": "blockchain patents"}}
- "draft 5 claims for blockchain" → WORKFLOW_TYPE: SINGLE_TOOL, TOOL: claim_drafting_tool, INTENT: draft claims, PARAMETERS: {{"user_query": "draft 5 claims for blockchain", "num_claims": 5}}
- "draft claims for AI system" → WORKFLOW_TYPE: SINGLE_TOOL, TOOL: claim_drafting_tool, INTENT: draft claims, PARAMETERS: {{"user_query": "draft claims for AI system"}}
- "draft a letter" → WORKFLOW_TYPE: CONVERSATION, TOOL: , INTENT: draft letter, PARAMETERS: {{}}
- "write an email" → WORKFLOW_TYPE: CONVERSATION, TOOL: , INTENT: write email, PARAMETERS: {{}}
- "compose a message" → WORKFLOW_TYPE: CONVERSATION, TOOL: , INTENT: compose message, PARAMETERS: {{}}
- "hello how are you" → WORKFLOW_TYPE: CONVERSATION, TOOL: , INTENT: greeting, PARAMETERS: {{}}
- "hi" → WORKFLOW_TYPE: CONVERSATION, TOOL: , INTENT: greeting, PARAMETERS: {{}}
- "hey" → WORKFLOW_TYPE: CONVERSATION, TOOL: , INTENT: greeting, PARAMETERS: {{}}
"""
    
    # Get LLM response
    response = llm_client.generate_text(
        prompt=prompt,
        max_tokens=2000,
        temperature=0.0,
        system_message="You are an AI assistant that analyzes user queries and determines the appropriate workflow."
    )
    
    if not response.get("success"):
        raise RuntimeError(f"LLM intent detection failed: {response.get('error', 'Unknown error')}")
    
    response_text = response.get("text", "")
    if not response_text.strip():
        raise RuntimeError("LLM returned empty response for intent detection")
    
    # Parse LLM response
    workflow_type, selected_tool, intent_type, tool_parameters = _parse_llm_response(response_text)
    
    # Validate parsed response
    if workflow_type not in ["SINGLE_TOOL", "MULTI_STEP", "CONVERSATION"]:
        raise RuntimeError(f"Invalid workflow type from LLM: {workflow_type}")
    
    if workflow_type in ["SINGLE_TOOL", "MULTI_STEP"] and not selected_tool:
        raise RuntimeError(f"Tool required for {workflow_type} but none provided by LLM")
    
    logger.debug(f"LLM detected workflow: {workflow_type}, tool: {selected_tool}")
    
    # Set intent_type based on workflow_type for consistency
    if workflow_type == "MULTI_STEP":
        final_intent_type = "multi_step"
    elif workflow_type == "CONVERSATION":
        # Use LLM-generated intent type directly
        final_intent_type = intent_type
    else:
        final_intent_type = "single_tool"
    
    return {
        **state,
        "selected_tool": selected_tool,
        "intent_type": final_intent_type,
        "tool_parameters": tool_parameters,
        "workflow_plan": []  # Always create workflow plan, even for single tools
    }


# Removed _simple_intent_detection - no fallbacks, fail fast with clear errors


# Removed _create_tool_mapping - no fallbacks, fail fast with clear errors


# Removed _has_multi_step_indicators - no fallbacks, fail fast with clear errors


# Removed _get_default_parameters - no fallbacks, fail fast with clear errors


def _parse_llm_response(response_text: str) -> tuple[str, str, str, dict]:
    """Parse LLM response for intent detection."""
    try:
        lines = response_text.strip().split('\n')
        workflow_type = "CONVERSATION"
        tool = ""
        intent = "conversation"
        parameters = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith("WORKFLOW_TYPE:"):
                workflow_type = line.split(":", 1)[1].strip()
            elif line.startswith("TOOL:"):
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
        
        return workflow_type, tool, intent, parameters
        
    except Exception as e:
        logger.warning(f"Failed to parse LLM response: {e}")
        return "CONVERSATION", "", "conversation", {}


async def plan_workflow_node(state: AgentState) -> AgentState:
    """
    Plan workflow - always creates a plan (single tool is just 1-step workflow).
    """
    logger.debug("Planning workflow")
    
    # Always create a workflow plan
    if state.get("workflow_plan") is not None and len(state.get("workflow_plan", [])) > 0:
        return state
    
    # If it's a conversation (any non-tool intent), don't create a workflow plan
    if state.get("intent_type") not in ["single_tool", "multi_step", "multi_step_workflow", "tool_execution"]:
        return {
            **state,
            "workflow_plan": [],
            "total_steps": 0,
            "current_step": 0,
            "step_results": {}
        }
    
    # If we already have a selected tool from intent detection AND it's not multi-step, create simple plan
    if state.get("selected_tool") and state.get("intent_type") not in ["multi_step", "multi_step_workflow"]:
        return {
            **state,
            "workflow_plan": [{
                "step": 1,
                "tool": state["selected_tool"],
                "params": state["tool_parameters"],
                "output_key": f"{state['selected_tool']}_results"
            }],
            "total_steps": 1,
            "current_step": 0,
            "step_results": {}
        }
    
    # Only proceed with LLM workflow planning if it's a multi-step workflow
    if state.get("intent_type") not in ["multi_step", "multi_step_workflow"]:
        raise RuntimeError(f"Invalid intent type for workflow planning: {state.get('intent_type')}")
    
    user_input = state["user_input"]
    conversation_history = state.get("conversation_history", [])
    document_content = state.get("document_content", "")
    
    from app.services.agent import AgentService
    agent_service = AgentService()
    
    # Get LLM client
    llm_client = agent_service._get_llm_client()
    if not llm_client:
        raise RuntimeError("LLM client not available - cannot perform workflow planning")
    
    # Get available tools and create descriptions
    available_tools = state.get("available_tools", [])
    tool_descriptions = []
    for tool in available_tools:
        tool_descriptions.append(f"- {tool['name']}: {tool.get('description', 'No description')}")
    tools_text = "\n".join(tool_descriptions) if tool_descriptions else "No tools available"
    
    # Prepare context
    conversation_context = ""
    if conversation_history:
        recent_history = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
        history_text = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in recent_history
        ])
        conversation_context = f"\n\nConversation History:\n{history_text}"
    
    document_context = ""
    if document_content:
        doc_preview = document_content[:5000] + "..." if len(document_content) > 5000 else document_content
        document_context = f"\n\nDocument Content:\n'''\n{doc_preview}\n'''"
    
    # LLM prompt for workflow planning
    prompt = f"""
You are an AI assistant that creates execution plans for multi-step workflows.

Available tools:
{tools_text}

User query: "{user_input}"{conversation_context}{document_context}

Create a step-by-step execution plan. Each step should specify:
- step: step number (1, 2, 3, etc.)
- tool: tool name to execute
- params: parameters for the tool
- output_key: key to store results (e.g., "search_results", "draft_results")

Respond with a JSON array of steps:
[
  {{"step": 1, "tool": "web_search_tool", "params": {{"query": "extracted query"}}, "output_key": "web_search_results"}},
  {{"step": 2, "tool": "claim_drafting_tool", "params": {{"user_query": "draft claims", "conversation_context": "{{web_search_results}}"}}, "output_key": "draft_results"}}
]

Examples:
- "web search ramy atawia then prior art search" → [{{"step": 1, "tool": "web_search_tool", "params": {{"query": "ramy atawia"}}, "output_key": "web_search_results"}}, {{"step": 2, "tool": "prior_art_search_tool", "params": {{"query": "prior art search"}}, "output_key": "prior_art_results"}}]
- "search for AI patents then draft 5 claims" → [{{"step": 1, "tool": "prior_art_search_tool", "params": {{"query": "AI patents"}}, "output_key": "prior_art_results"}}, {{"step": 2, "tool": "claim_drafting_tool", "params": {{"user_query": "draft 5 claims", "prior_art_context": "{{prior_art_results}}"}}, "output_key": "draft_results"}}]
"""
    
    # Get LLM response
    response = llm_client.generate_text(
        prompt=prompt,
        max_tokens=2000,
        temperature=0.0,
        system_message="You are an AI assistant that analyzes user queries and determines the appropriate workflow."
    )
    
    if not response.get("success"):
        raise RuntimeError(f"LLM workflow planning failed: {response.get('error', 'Unknown error')}")
    
    response_text = response.get("text", "")
    if not response_text.strip():
        raise RuntimeError("LLM returned empty response for workflow planning")
    
    # Parse workflow plan
    workflow_plan = _parse_workflow_plan(response_text)
    
    if not workflow_plan:
        raise RuntimeError("Failed to parse workflow plan from LLM response")
    
    return {
        **state,
        "workflow_plan": workflow_plan,
        "total_steps": len(workflow_plan),
        "current_step": 0,
        "step_results": {}
    }


# Removed _simple_workflow_planning - no fallbacks, fail fast with clear errors


# Removed _create_dynamic_workflow_plan - no fallbacks, fail fast with clear errors


# Removed _create_pattern_based_workflow - no fallbacks, fail fast with clear errors


# Removed _get_configured_parameters - no fallbacks, fail fast with clear errors


# Removed _detect_workflow_tools and _add_context_to_parameters - no fallbacks, fail fast with clear errors


def _get_tool_display_name(tool_name: str, available_tools: List[Dict[str, Any]]) -> str:
    """Get user-friendly display name for a tool."""
    # Look for tool in available tools first
    for tool in available_tools:
        if tool.get("name") == tool_name:
            # Use tool's display name if available, otherwise use description
            display_name = tool.get("display_name") or tool.get("description", tool_name)
            # Clean up the display name
            if display_name and display_name != tool_name:
                return display_name.replace("Tool", "").replace("tool", "").strip()
    
    # Fallback to tool name with proper formatting
    if tool_name == "prior_art_search_tool":
        return "Prior Art Search Results"
    elif tool_name == "claim_drafting_tool":
        return "Draft Claims"
    elif tool_name == "claim_analysis_tool":
        return "Claim Analysis"
    elif tool_name == "web_search_tool":
        return "Web Search Results"
    else:
        # Convert tool_name to readable format
        return tool_name.replace("_", " ").replace("tool", "").strip().title() + " Results"


def _parse_workflow_plan(response_text: str) -> List[Dict[str, Any]]:
    """Parse LLM workflow plan response."""
    try:
        import json
        # Extract JSON from response
        start_idx = response_text.find('[')
        end_idx = response_text.rfind(']') + 1
        if start_idx != -1 and end_idx != -1:
            json_text = response_text[start_idx:end_idx]
            return json.loads(json_text)
    except Exception as e:
        logger.warning(f"Failed to parse workflow plan: {e}")
    
    return []


async def execute_tool_node(state: AgentState) -> AgentState:
    """
    Execute tools - always uses multi-step workflow (single tool is 1-step).
    """
    logger.debug("Executing tools")
    
    # Always use multi-step workflow (single tool is just 1 step)
    return await _execute_multi_step_workflow(state)




async def _execute_multi_step_workflow(state: AgentState) -> AgentState:
    """Execute multi-step workflow."""
    workflow_plan = state["workflow_plan"]
    current_step = state["current_step"]
    step_results = state["step_results"]
    
    if current_step >= len(workflow_plan):
        return state
    
    try:
        from app.services.agent import AgentService
        agent_service = AgentService()
        
        # Get MCP orchestrator
        orchestrator = agent_service._get_mcp_orchestrator()
        if not orchestrator:
            raise RuntimeError("MCP orchestrator not available")
        
        # Get current step
        step = workflow_plan[current_step]
        
        # Prepare parameters with context substitution
        params = _prepare_parameters_with_context(step["params"], step_results)
        
        # Execute tool
        result = await orchestrator.execute_tool(
            tool_name=step["tool"],
            parameters=params
        )
        
        # Store result
        step_results[step["output_key"]] = result
        
        return {
            **state,
            "current_step": current_step + 1,
            "step_results": step_results,
            "tool_result": result  # For compatibility
        }
        
    except Exception as e:
        logger.error(f"Multi-step execution failed at step {current_step}: {e}")
        step_results[f"step_{current_step}_error"] = str(e)
        return {
            **state,
            "current_step": current_step + 1,
            "step_results": step_results,
            "tool_result": {"error": str(e), "success": False}
        }


def _prepare_parameters_with_context(params: Dict[str, Any], step_results: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare parameters with context substitution."""
    prepared_params = {}
    
    for key, value in params.items():
        if isinstance(value, str) and "{{" in value and "}}" in value:
            # Simple context substitution
            for result_key, result_value in step_results.items():
                if f"{{{{{result_key}}}}}" in value:
                    if isinstance(result_value, dict) and "result" in result_value:
                        # Extract formatted content
                        formatted_content = result_value["result"]
                        value = value.replace(f"{{{{{result_key}}}}}", str(formatted_content))
                    else:
                        value = value.replace(f"{{{{{result_key}}}}}", str(result_value))
            prepared_params[key] = value
        else:
            prepared_params[key] = value
    
    return prepared_params


async def generate_response_node(state: AgentState) -> AgentState:
    """
    Generate final response from tool results - always uses multi-step response.
    """
    logger.debug("Generating response")
    
    # Always use multi-step response (single tool is just 1 step)
    return await _generate_multi_step_response(state)




async def _generate_conversational_response(state: AgentState) -> str:
    """Generate conversational response using LLM."""
    user_input = state["user_input"]
    conversation_history = state.get("conversation_history", [])
    
    try:
        from app.services.agent import AgentService
        agent_service = AgentService()
        
        # Get LLM client
        llm_client = agent_service._get_llm_client()
        if not llm_client:
            return "Hello! I'm here to help you with patent research, claim drafting, and document analysis. What would you like to work on today?"
        
        # Prepare conversation context
        conversation_context = ""
        if conversation_history:
            recent_history = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
            history_text = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in recent_history
            ])
            conversation_context = f"{history_text}"
        
        # Create conversational prompt
        prompt = f"""You are a helpful AI assistant that can help with a wide range of tasks including patent research, document drafting, general questions, and more.

## CURRENT USER MESSAGE:
{user_input}

## CONVERSATION HISTORY (chronological order, oldest to newest):
{conversation_context if conversation_context else "No previous conversation."}

## INSTRUCTIONS:
Please respond to the CURRENT USER MESSAGE above. Consider the relevance of the previous conversation history when crafting your response:

- If the current message is a continuation of a previous topic, acknowledge the context
- If the current message is completely new, respond to it directly without forcing connections to old topics
- If the current message is a greeting or general question, respond naturally without over-referencing old conversations
- Focus primarily on the current message while using previous context only when genuinely relevant

You can help with:
- Answer general knowledge questions
- Help with document drafting (letters, emails, reports, etc.)
- Provide friendly greetings and conversation
- Explain concepts and provide information
- Help with writing and communication tasks
- Assist with patent-related work when relevant

IMPORTANT: 
- Respond directly to the current user message
- Do not format your response as a conversation or include "User:" or "Assistant:" labels
- For simple greetings like "hi", "hello", "hey", respond with a friendly greeting and ask how you can help
- Do not reference previous conversation topics unless the current message explicitly asks about them
- Just provide a helpful response

Be helpful, professional, and engaging. Generate actual content when requested (like drafting documents) rather than just explaining what you can do.

Keep responses concise but comprehensive."""
        
        # Get LLM response
        response = llm_client.generate_text(
            prompt=prompt,
            max_tokens=1000,
            temperature=0.7,
            system_message="You are a helpful AI assistant for patent research and document analysis. Be friendly, professional, and helpful."
        )
        
        if response.get("success"):
            return response.get("text", "Hello! How can I help you today?")
        else:
            return "Hello! I'm here to help you with patent research, claim drafting, and document analysis. What would you like to work on today?"
            
    except Exception as e:
        logger.warning(f"Conversational response generation failed: {e}")
        return "Hello! I'm here to help you with patent research, claim drafting, and document analysis. What would you like to work on today?"


async def _generate_multi_step_response(state: AgentState) -> AgentState:
    """Generate response for multi-step workflow (including single tool as 1-step)."""
    step_results = state.get("step_results", {})
    workflow_plan = state.get("workflow_plan", [])
    intent_type = state.get("intent_type", "tool_execution")
    
    # Handle conversation intents (any non-tool intent)
    if intent_type not in ["single_tool", "multi_step", "multi_step_workflow", "tool_execution"]:
        logger.debug("Generating conversational response")
        final_response = await _generate_conversational_response(state)
        return {
            **state,
            "final_response": final_response,
            "intent_type": intent_type
        }
    
    if not step_results:
        final_response = "I'm not sure how to help with that request."
    else:
        # Check if any step failed
        failed_steps = [step for step in workflow_plan 
                       if step["output_key"] in step_results and 
                       isinstance(step_results[step["output_key"]], dict) and 
                       not step_results[step["output_key"]].get("success", True)]
        
        if failed_steps:
            # Handle partial failure
            final_response = "I completed some steps but encountered issues with others. "
            for step in failed_steps:
                error_msg = step_results[step["output_key"]].get("error", "Unknown error")
                final_response += f"Step {step['step']} ({step['tool']}) failed: {error_msg}. "
        else:
            # All steps completed successfully
            response_parts = []
            
            for step in workflow_plan:
                step_result = step_results.get(step["output_key"])
                
                if step_result and not step_result.get("error"):
                    # Extract formatted content
                    formatted_content = step_result.get("result", str(step_result))
                    
                    # Format step result with proper content
                    tool_name = step["tool"]
                    
                    # Get tool display name from available tools or use default
                    display_name = _get_tool_display_name(tool_name, state.get("available_tools", []))
                    
                    # Format with dynamic header
                    response_parts.append(f"**{display_name}:**\n{formatted_content}")
            
            if response_parts:
                final_response = "\n\n".join(response_parts)
            else:
                final_response = "I completed the workflow but didn't get any results."
    
    # Determine intent type based on workflow length, but preserve non-tool intents
    if intent_type not in ["single_tool", "multi_step", "multi_step_workflow", "tool_execution"]:
        workflow_intent = intent_type
    else:
        workflow_intent = "multi_step_workflow" if len(workflow_plan) > 1 else "single_tool_workflow"
    
    return {
        **state,
        "final_response": final_response,
        "intent_type": workflow_intent
    }


def _route_workflow(state: AgentState) -> str:
    """Route workflow based on state."""
    # Route non-tool intents directly to response generation
    if state.get("intent_type") not in ["single_tool", "multi_step", "multi_step_workflow", "tool_execution"]:
        return "response_generation"
    elif state.get("workflow_plan") is not None and len(state.get("workflow_plan", [])) > 0:
        return "tool_execution"
    else:
        return "response_generation"


def _route_multi_step(state: AgentState) -> str:
    """Route multi-step workflow."""
    current_step = state.get("current_step", 0)
    total_steps = state.get("total_steps", 0)
    
    if current_step < total_steps:
        return "tool_execution"  # Continue with next step
    else:
        return "response_generation"  # All steps done, generate response


def create_agent_graph() -> StateGraph:
    """
    Create unified LangGraph workflow.
    
    This single graph handles both single-tool and multi-step workflows
    with intelligent routing and context-aware execution.
    """
    logger.info("Creating unified LangGraph workflow")
    
    # Create the workflow
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("intent_detection", detect_intent_node)
    workflow.add_node("workflow_planning", plan_workflow_node)
    workflow.add_node("tool_execution", execute_tool_node)
    workflow.add_node("response_generation", generate_response_node)
    
    # Add edges
    # Entry point: START -> intent_detection
    workflow.add_edge("__start__", "intent_detection")
    workflow.add_edge("intent_detection", "workflow_planning")
    workflow.add_conditional_edges(
        "workflow_planning",
        _route_workflow,
        {
            "tool_execution": "tool_execution",
            "response_generation": "response_generation"
        }
    )
    workflow.add_conditional_edges(
        "tool_execution",
        _route_multi_step,
        {
            "tool_execution": "tool_execution",
            "response_generation": "response_generation"
        }
    )
    workflow.add_edge("response_generation", END)
    
    # Compile the workflow
    return workflow.compile()


def get_agent_graph() -> StateGraph:
    """Get the compiled agent graph with lazy initialization."""
    if not hasattr(get_agent_graph, '_graph'):
        get_agent_graph._graph = create_agent_graph()
    return get_agent_graph._graph
