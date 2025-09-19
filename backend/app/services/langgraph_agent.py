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


class MultiStepAgentState(TypedDict):
    """Advanced agent state for Phase 3 - multi-step workflow support."""
    
    # User input and context
    user_input: str
    document_content: str
    conversation_history: List[Dict[str, Any]]
    available_tools: List[Dict[str, Any]]
    
    # Workflow planning
    workflow_plan: List[Dict[str, Any]]  # Multi-step execution plan
    current_step: int                    # Current step index
    total_steps: int                     # Total steps in workflow
    step_results: Dict[str, Any]         # Results from each step
    
    # Tool execution (current step)
    selected_tool: str                   # Current tool being executed
    tool_parameters: Dict[str, Any]      # Parameters for current tool
    
    # Response generation
    final_response: str
    intent_type: str
    execution_metadata: Dict[str, Any]   # Execution tracking


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
PARAMETERS: [JSON object with tool parameters, or empty object {{}}]

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
    
    # Enhanced simple detection with more specific matching
    if "prior art" in user_input or "patent" in user_input:
        selected_tool = "prior_art_search_tool"
        intent_type = "tool_execution"
        tool_parameters = {"query": user_input}
    elif "web search" in user_input or ("search" in user_input and "web" in user_input):
        selected_tool = "web_search_tool"
        intent_type = "tool_execution"
        tool_parameters = {"query": user_input}
    elif "search" in user_input or "find" in user_input:
        # Default to web search for general search queries
        selected_tool = "web_search_tool"
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
    
    # Extract formatted content from tool result for LLM processing
    formatted_content = tool_result.get("result", str(tool_result)) if isinstance(tool_result, dict) else str(tool_result)
    
    # Create prompt for response formatting
    prompt = f"""
You are an AI assistant that formats tool execution results into user-friendly responses.

User's original request: "{user_input}"
Tool executed: {tool_name}
Tool result: {formatted_content}

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
    
    # Extract formatted content from tool result
    formatted_content = tool_result.get("result", str(tool_result)) if isinstance(tool_result, dict) else str(tool_result)
    
    # Simple formatting based on tool type
    if tool_name == "prior_art_search_tool":
        return f"Here are the prior art search results:\n\n{formatted_content}"
    elif tool_name == "claim_drafting_tool":
        return f"Here are the drafted claims:\n\n{formatted_content}"
    elif tool_name == "claim_analysis_tool":
        return f"Here's the claim analysis:\n\n{formatted_content}"
    else:
        return f"Tool execution completed:\n\n{formatted_content}"


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


# Phase 3: Multi-step workflow functions
async def detect_intent_advanced_node(state: MultiStepAgentState) -> MultiStepAgentState:
    """
    Advanced intent detection for multi-step workflows.
    
    Phase 3: Analyzes user input for multi-step patterns.
    """
    logger.debug("LangGraph Phase 3: Detecting advanced intent for multi-step workflow")
    
    user_input = state["user_input"]
    available_tools = state["available_tools"]
    
    try:
        from app.services.agent import AgentService
        agent_service = AgentService()
        
        # Get LLM client
        llm_client = agent_service._get_llm_client()
        if not llm_client:
            return await _simple_multi_step_intent_detection(state)
        
        # Create tool descriptions for LLM
        tool_descriptions = []
        for tool in available_tools:
            tool_descriptions.append(f"- {tool['name']}: {tool.get('description', 'No description')}")
        
        tools_text = "\n".join(tool_descriptions) if tool_descriptions else "No tools available"
        
        # LLM prompt for multi-step intent detection
        prompt = f"""
You are an AI assistant that analyzes user queries and determines if they require multi-step workflows.

Available tools:
{tools_text}

User query: "{user_input}"

Analyze if this query requires multiple steps or can be handled with a single tool.

Multi-step indicators:
- Multiple actions: "find X and then draft Y"
- Sequential dependencies: "search for prior art, then analyze it, then draft claims"
- Complex workflows: "research patents, analyze them, create a report, and export it"

Respond in this exact format:
WORKFLOW_TYPE: [single_tool, multi_step, or conversation]
INTENT: [brief description of intent]
TOOLS: [comma-separated list of tools needed, or empty for conversation]
PARAMETERS: [JSON object with parameters for each tool]

Examples:
- "find prior art for AI patents" → WORKFLOW_TYPE: single_tool, INTENT: search prior art, TOOLS: prior_art_search_tool, PARAMETERS: {{"query": "AI patents"}}
- "find prior art and draft 5 claims" → WORKFLOW_TYPE: multi_step, INTENT: research and draft, TOOLS: prior_art_search_tool,claim_drafting_tool, PARAMETERS: {{"step1": {{"tool": "prior_art_search_tool", "params": {{"query": "AI patents"}}}}, "step2": {{"tool": "claim_drafting_tool", "params": {{"user_query": "draft 5 claims", "prior_art_context": "{{step1_result}}"}}}}}}
- "hello how are you" → WORKFLOW_TYPE: conversation, INTENT: greeting, TOOLS: , PARAMETERS: {{}}
"""
        
        # Get LLM response
        response = await llm_client.ainvoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Parse LLM response
        workflow_type, intent, tools, parameters = _parse_advanced_intent_response(response_text)
        
        logger.debug(f"LangGraph Phase 3: Detected workflow type '{workflow_type}' with intent '{intent}'")
        
        return {
            **state,
            "intent_type": intent,
            "execution_metadata": {
                "workflow_type": workflow_type,
                "tools": tools,
                "parameters": parameters
            }
        }
        
    except Exception as e:
        logger.warning(f"LangGraph Phase 3: Advanced intent detection failed, using fallback: {e}")
        return await _simple_multi_step_intent_detection(state)


async def _simple_multi_step_intent_detection(state: MultiStepAgentState) -> MultiStepAgentState:
    """Fallback simple multi-step intent detection for Phase 3."""
    user_input = state["user_input"].lower()
    
    # Check for multi-step patterns
    multi_step_indicators = [
        "and then", "then", "after", "followed by", "next",
        "find", "search", "draft", "analyze", "create"
    ]
    
    # Count action words
    action_count = sum(1 for indicator in multi_step_indicators if indicator in user_input)
    
    if action_count >= 2:
        workflow_type = "multi_step"
        intent = "multi-step workflow"
    elif "prior art" in user_input or "search" in user_input:
        workflow_type = "single_tool"
        intent = "search prior art"
    elif "draft" in user_input or "claim" in user_input:
        workflow_type = "single_tool"
        intent = "draft claims"
    else:
        workflow_type = "conversation"
        intent = "conversation"
    
    return {
        **state,
        "intent_type": intent,
        "execution_metadata": {
            "workflow_type": workflow_type,
            "tools": [],
            "parameters": {}
        }
    }


def _parse_advanced_intent_response(response_text: str) -> tuple[str, str, list, dict]:
    """Parse LLM response for advanced intent detection."""
    try:
        lines = response_text.strip().split('\n')
        workflow_type = "conversation"
        intent = "conversation"
        tools = []
        parameters = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith("WORKFLOW_TYPE:"):
                workflow_type = line.split(":", 1)[1].strip()
            elif line.startswith("INTENT:"):
                intent = line.split(":", 1)[1].strip()
            elif line.startswith("TOOLS:"):
                tools_text = line.split(":", 1)[1].strip()
                tools = [t.strip() for t in tools_text.split(",") if t.strip()]
            elif line.startswith("PARAMETERS:"):
                params_text = line.split(":", 1)[1].strip()
                if params_text and params_text != "{}":
                    try:
                        import json
                        parameters = json.loads(params_text)
                    except json.JSONDecodeError:
                        parameters = {}
        
        return workflow_type, intent, tools, parameters
        
    except Exception as e:
        logger.warning(f"Failed to parse advanced intent response: {e}")
        return "conversation", "conversation", [], {}


async def plan_workflow_node(state: MultiStepAgentState) -> MultiStepAgentState:
    """
    Plan multi-step workflow execution using LLM-based planning.
    
    Phase 3: Uses LLM to intelligently plan workflow based on user intent.
    """
    logger.debug("LangGraph Phase 3: Planning multi-step workflow with LLM")
    
    user_input = state["user_input"]
    available_tools = state["available_tools"]
    execution_metadata = state.get("execution_metadata", {})
    
    try:
        from app.services.agent import AgentService
        agent_service = AgentService()
        
        # Get LLM client
        llm_client = agent_service._get_llm_client()
        if not llm_client:
            return await _simple_workflow_planning(state)
        
        # Create tool descriptions for LLM
        tool_descriptions = []
        for tool in available_tools:
            tool_descriptions.append(f"- {tool['name']}: {tool.get('description', 'No description')}")
        
        tools_text = "\n".join(tool_descriptions) if tool_descriptions else "No tools available"
        
        # LLM prompt for workflow planning
        prompt = f"""
You are an AI workflow planner that creates execution plans for complex user queries.

Available tools:
{tools_text}

User query: "{user_input}"

Analyze the user's query and create a step-by-step execution plan. Consider:
1. What information needs to be gathered first?
2. What tools should be used in sequence?
3. How should results from one step inform the next step?
4. What context should be passed between steps?

Create a JSON workflow plan with this structure:
{{
  "workflow_plan": [
    {{
      "step": 1,
      "tool": "tool_name",
      "parameters": {{"param1": "value1", "param2": "value2"}},
      "depends_on": null,
      "output_key": "step1_results",
      "description": "What this step accomplishes"
    }},
    {{
      "step": 2,
      "tool": "tool_name", 
      "parameters": {{"param1": "value1", "context": "{{step1_results}}"}},
      "depends_on": 1,
      "output_key": "step2_results",
      "description": "What this step accomplishes"
    }}
  ]
}}

Guidelines:
- Use context substitution like "{{step1_results}}" to pass data between steps
- Make parameters specific to each tool's requirements
- Ensure logical flow and dependencies
- Include meaningful descriptions
- Use available tools only
- For search queries, extract the actual search terms from the user input
- For claim drafting, include context from previous steps when available

Examples:
- "web search ramy atawia, then draft 3 claims" → web_search_tool → claim_drafting_tool
- "find prior art for AI patents and analyze them" → prior_art_search_tool → claim_analysis_tool
- "draft 5 claims for blockchain" → claim_drafting_tool (single step)
"""
        
        # Get LLM response
        response = await llm_client.ainvoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Parse LLM response
        workflow_plan = _parse_llm_workflow_plan(response_text)
        
        if not workflow_plan:
            logger.warning("LangGraph Phase 3: LLM workflow planning failed, using fallback")
            return await _simple_workflow_planning(state)
        
        logger.debug(f"LangGraph Phase 3: LLM created workflow plan with {len(workflow_plan)} steps")
        
        return {
            **state,
            "workflow_plan": workflow_plan,
            "total_steps": len(workflow_plan),
            "current_step": 0,
            "step_results": {}
        }
        
    except Exception as e:
        logger.warning(f"LangGraph Phase 3: LLM workflow planning failed, using fallback: {e}")
        return await _simple_workflow_planning(state)


def _parse_llm_workflow_plan(response_text: str) -> List[Dict[str, Any]]:
    """Parse LLM response for workflow planning."""
    try:
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_match:
            logger.warning("No JSON found in LLM workflow response")
            return []
        
        json_str = json_match.group(0)
        parsed = json.loads(json_str)
        
        workflow_plan = parsed.get("workflow_plan", [])
        
        # Validate workflow plan structure
        for step in workflow_plan:
            required_fields = ["step", "tool", "parameters", "output_key"]
            if not all(field in step for field in required_fields):
                logger.warning(f"Invalid workflow step: missing required fields")
                return []
        
        logger.debug(f"Parsed workflow plan with {len(workflow_plan)} steps")
        return workflow_plan
        
    except Exception as e:
        logger.warning(f"Failed to parse LLM workflow plan: {e}")
        return []


async def _simple_workflow_planning(state: MultiStepAgentState) -> MultiStepAgentState:
    """Simple fallback workflow planning."""
    logger.debug("LangGraph Phase 3: Using simple workflow planning fallback")
    
    user_input = state["user_input"]
    available_tools = state["available_tools"]
    
    # Create tool mapping for easy lookup
    tool_map = {tool["name"]: tool for tool in available_tools}
    
    # Simple heuristic: if query contains "search" and "draft", create a 2-step plan
    if "search" in user_input.lower() and "draft" in user_input.lower():
        workflow_plan = []
        
        # Step 1: Web search
        if "web_search_tool" in tool_map:
            search_query = user_input.replace("web search", "").replace("draft", "").strip()
            workflow_plan.append({
                "step": 1,
                "tool": "web_search_tool",
                "parameters": {"query": search_query},
                "depends_on": None,
                "output_key": "web_search_results"
            })
        
        # Step 2: Claim drafting
        if "claim_drafting_tool" in tool_map:
            claim_query = user_input
            workflow_plan.append({
                "step": 2,
                "tool": "claim_drafting_tool",
                "parameters": {
                    "user_query": claim_query,
                    "conversation_context": "{web_search_results}",
                    "document_reference": state["document_content"]
                },
                "depends_on": 1,
                "output_key": "draft_claims"
            })
    
    # Single step fallback
    if not workflow_plan and available_tools:
        # Prefer workflow tools over thinking tools
        workflow_tools = ["web_search_tool", "prior_art_search_tool", "claim_drafting_tool", "claim_analysis_tool"]
        preferred_tool = None
        
        for tool_name in workflow_tools:
            if tool_name in tool_map:
                preferred_tool = tool_map[tool_name]
                break
        
        if not preferred_tool:
            preferred_tool = available_tools[0]
        
        workflow_plan = [{
            "step": 1,
            "tool": preferred_tool["name"],
            "parameters": {"user_query": user_input},
            "depends_on": None,
            "output_key": "result"
        }]
    
    return {
        **state,
        "workflow_plan": workflow_plan,
        "total_steps": len(workflow_plan),
        "current_step": 0,
        "step_results": {}
    }


def _extract_search_query(user_input: str, context: str) -> str:
    """Extract search query from user input."""
    if context in user_input.lower():
        # Find text after the context word
        start_idx = user_input.lower().find(context) + len(context)
        remaining = user_input[start_idx:].strip()
        
        # Remove common connecting words
        connecting_words = ["and", "then", "for", "about", "on"]
        for word in connecting_words:
            if remaining.startswith(word):
                remaining = remaining[len(word):].strip()
        
        return remaining if remaining else "patent search"
    
    return "patent search"


def _extract_claim_parameters(user_input: str) -> str:
    """Extract claim drafting parameters from user input."""
    if "draft" in user_input.lower():
        start_idx = user_input.lower().find("draft")
        claim_request = user_input[start_idx:].strip()
        return claim_request
    
    return "draft patent claims"


async def execute_multi_step_node(state: MultiStepAgentState) -> MultiStepAgentState:
    """
    Execute multi-step workflow with output passing.
    
    Phase 3: Executes each step in sequence with context passing.
    """
    logger.debug("LangGraph Phase 3: Executing multi-step workflow")
    
    workflow_plan = state["workflow_plan"]
    step_results = state.get("step_results", {})
    current_step = state.get("current_step", 0)
    
    try:
        # Get MCP orchestrator
        from app.services.agent import AgentService
        agent_service = AgentService()
        orchestrator = agent_service._get_mcp_orchestrator()
        
        if not orchestrator:
            raise RuntimeError("MCP orchestrator not available")
        
        # Execute each step in sequence
        for step in workflow_plan:
            step_number = step["step"]
            tool_name = step["tool"]
            
            # Prepare parameters with context substitution
            parameters = _prepare_parameters_with_context(
                step["parameters"], 
                step_results, 
                state
            )
            
            logger.debug(f"LangGraph Phase 3: Executing step {step_number}: {tool_name}")
            
            try:
                # Execute tool
                result = await orchestrator.execute_tool(tool_name, parameters)
                
                # Store result for next step
                step_results[step_number] = result
                
                # Update current step
                current_step = step_number
                
                logger.debug(f"LangGraph Phase 3: Step {step_number} completed successfully")
                
            except Exception as e:
                # Handle tool execution errors
                logger.error(f"LangGraph Phase 3: Step {step_number} failed: {str(e)}")
                step_results[step_number] = {
                    "error": str(e),
                    "success": False,
                    "step": step_number,
                    "tool": tool_name
                }
                break
        
        return {
            **state,
            "step_results": step_results,
            "current_step": current_step
        }
        
    except Exception as e:
        logger.error(f"LangGraph Phase 3: Multi-step execution failed: {str(e)}")
        
        # Return error state
        return {
            **state,
            "step_results": {
                "error": str(e),
                "success": False
            },
            "current_step": current_step
        }


def _prepare_parameters_with_context(
    parameters: Dict[str, Any], 
    step_results: Dict[str, Any], 
    state: MultiStepAgentState
) -> Dict[str, Any]:
    """Prepare tool parameters with context substitution."""
    prepared_params = {}
    
    for key, value in parameters.items():
        if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
            # Context substitution
            context_key = value[1:-1]  # Remove braces
            
            if context_key == "prior_art_results":
                # Get prior art results from step 1
                prior_art = step_results.get(1, {})
                if isinstance(prior_art, dict) and "result" in prior_art:
                    prepared_params[key] = prior_art["result"]
                else:
                    prepared_params[key] = str(prior_art)
            
            elif context_key == "draft_claims":
                # Get draft claims from previous step
                claims = step_results.get(2, {})
                if isinstance(claims, dict) and "result" in claims:
                    prepared_params[key] = claims["result"]
                else:
                    prepared_params[key] = str(claims)
            
            elif context_key == "web_search_results":
                # Get web search results from previous step
                web_results = step_results.get(1, {})
                if isinstance(web_results, dict) and "result" in web_results:
                    prepared_params[key] = web_results["result"]
                else:
                    prepared_params[key] = str(web_results)
            
            elif context_key == "document_content":
                prepared_params[key] = state["document_content"]
            
            else:
                # Fallback to original value
                prepared_params[key] = value
        else:
            prepared_params[key] = value
    
    return prepared_params


async def generate_multi_step_response_node(state: MultiStepAgentState) -> MultiStepAgentState:
    """
    Generate final response from multi-step results.
    
    Phase 3: Combines results from all steps into coherent response.
    """
    logger.debug("LangGraph Phase 3: Generating multi-step response")
    
    step_results = state.get("step_results", {})
    workflow_plan = state.get("workflow_plan", [])
    
    if not step_results:
        final_response = "I'm not sure how to help with that request."
    else:
        # Check if any step failed
        failed_steps = [step for step in workflow_plan 
                       if step["step"] in step_results and 
                       isinstance(step_results[step["step"]], dict) and 
                       not step_results[step["step"]].get("success", True)]
        
        if failed_steps:
            # Handle partial failure
            final_response = "I completed some steps but encountered issues with others. "
            for step in failed_steps:
                error_msg = step_results[step["step"]].get("error", "Unknown error")
                final_response += f"Step {step['step']} ({step['tool']}) failed: {error_msg}. "
        else:
            # All steps completed successfully
            response_parts = []
            
            for step in workflow_plan:
                step_number = step["step"]
                step_result = step_results.get(step_number)
                
                if step_result and not step_result.get("error"):
                    # Extract formatted content from step result
                    formatted_content = step_result.get("result", str(step_result))
                    
                    # Format step result with proper content
                    if step["tool"] == "prior_art_search_tool":
                        response_parts.append(f"**Prior Art Search Results:**\n{formatted_content}")
                    elif step["tool"] == "claim_drafting_tool":
                        response_parts.append(f"**Draft Claims:**\n{formatted_content}")
                    elif step["tool"] == "claim_analysis_tool":
                        response_parts.append(f"**Claim Analysis:**\n{formatted_content}")
                    elif step["tool"] == "web_search_tool":
                        response_parts.append(f"**Web Search Results:**\n{formatted_content}")
                    else:
                        response_parts.append(f"**{step['tool']} Results:**\n{formatted_content}")
            
            if response_parts:
                final_response = "\n\n".join(response_parts)
            else:
                final_response = "I completed the workflow but didn't get any results."
    
    return {
        **state,
        "final_response": final_response,
        "intent_type": "multi_step_workflow"
    }


def create_advanced_agent_graph() -> StateGraph:
    """
    Create advanced LangGraph workflow for Phase 3.
    
    This establishes multi-step workflow support with:
    - Advanced intent detection
    - Workflow planning
    - Multi-step execution with context passing
    - Comprehensive response generation
    """
    logger.info("Creating LangGraph Phase 3 advanced workflow")
    
    # Create the workflow
    workflow = StateGraph(MultiStepAgentState)
    
    # Add nodes
    workflow.add_node("intent_detection", detect_intent_advanced_node)
    workflow.add_node("workflow_planning", plan_workflow_node)
    workflow.add_node("multi_step_execution", execute_multi_step_node)
    workflow.add_node("response_generation", generate_multi_step_response_node)
    
    # Add conditional routing
    workflow.add_conditional_edges(
        "intent_detection",
        _route_workflow_type,
        {
            "single_tool": "workflow_planning",
            "multi_step": "workflow_planning", 
            "conversation": "response_generation"
        }
    )
    
    # Multi-step workflow edges
    workflow.add_edge("workflow_planning", "multi_step_execution")
    workflow.add_edge("multi_step_execution", "response_generation")
    workflow.add_edge("response_generation", END)
    
    # Set entry point
    workflow.set_entry_point("intent_detection")
    
    logger.info("LangGraph Phase 3 advanced workflow created successfully")
    return workflow.compile()


def _route_workflow_type(state: MultiStepAgentState) -> str:
    """Determine workflow type based on intent detection."""
    execution_metadata = state.get("execution_metadata", {})
    workflow_type = execution_metadata.get("workflow_type", "conversation")
    
    if workflow_type == "conversation":
        return "conversation"
    elif workflow_type == "single_tool":
        return "single_tool"
    elif workflow_type == "multi_step":
        return "multi_step"
    else:
        # Default to single_tool for any other workflow type
        return "single_tool"


# Global instance for lazy initialization
_advanced_agent_graph = None


def get_advanced_agent_graph() -> StateGraph:
    """Get the advanced agent graph instance."""
    global _advanced_agent_graph
    if _advanced_agent_graph is None:
        _advanced_agent_graph = create_advanced_agent_graph()
    return _advanced_agent_graph
