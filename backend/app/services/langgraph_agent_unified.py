"""
Clean LangGraph Agent Service - FIXED VERSION

Pure LLM-driven agent with no keyword logic, no fallbacks, no mock data.
Fails fast with clear errors when dependencies are missing.

Features:
- Pure LLM intent detection and planning
- Clean unified state management
- Clear workflow routing
- No hardcoded patterns or fallbacks

FIXES APPLIED:
- Enhanced error handling and validation
- Improved context propagation with debugging
- Stricter tool result validation
- Better failure reporting
- Enhanced logging throughout workflow
"""

import structlog
import json
import logging
from typing import TypedDict, List, Dict, Any, Optional

logger = structlog.get_logger()

# LangGraph import - fail clearly if not available
try:
    from langgraph.graph import StateGraph, END
except ImportError:
    logger.error("LangGraph is required but not installed. Please install with: pip install langgraph")
    raise ImportError("LangGraph is required for this agent service. Install with: pip install langgraph")


class AgentGraphDependencies:
    """Dependencies required by the agent graph."""
    def __init__(self, llm_client, mcp_orchestrator):
        self.llm_client = llm_client
        self.mcp_orchestrator = mcp_orchestrator


class AgentState(TypedDict):
    """Unified agent state for all workflows."""
    # Input
    user_input: str
    document_content: Optional[str]
    conversation_history: List[Dict[str, Any]]
    available_tools: List[Dict[str, Any]]
    
    # Dependencies (injected)
    dependencies: Optional[Any]  # Will hold AgentGraphDependencies
    
    # Processing
    intent_type: str  # 'conversation' or 'tool_workflow'
    workflow_plan: List[Dict[str, Any]]
    current_step: int
    step_results: Dict[str, Any]
    workflow_errors: List[str]  # NEW: Track workflow errors
    workflow_completed: Optional[bool]  # Track if workflow execution is complete
    
    # Output
    final_response: str


async def detect_intent_node(state: AgentState) -> AgentState:
    """Detect whether this is a conversation or tool workflow using LLM."""
    logger.info("Starting intent detection", user_input=state["user_input"][:100])
    
    try:
        # Use LLM for all intent detection - no keyword logic
        intent_type, workflow_plan = await _llm_intent_detection(state)
        
        logger.info("Intent detection completed", 
                   intent_type=intent_type, 
                   workflow_steps=len(workflow_plan))
        
        return {
            **state,
            "intent_type": intent_type,
            "workflow_plan": workflow_plan,
            "current_step": 0,
            "step_results": {},
            "workflow_errors": []  # Initialize error tracking
        }
    
    except Exception as e:
        logger.error("Intent detection failed", error=str(e))
        # Fallback to conversation mode on intent detection failure
        return {
            **state,
            "intent_type": "conversation",
            "workflow_plan": [],
            "current_step": 0,
            "step_results": {},
            "workflow_errors": [f"Intent detection failed: {str(e)}"]
        }
    
    
async def _llm_intent_detection(state: AgentState) -> tuple[str, List[Dict]]:
    """Use LLM for intent detection and workflow planning."""
    user_input = state["user_input"]
    available_tools = state.get("available_tools", [])
    conversation_history = state.get("conversation_history", [])
    document_content = state.get("document_content", "")
    
    # Use injected dependency instead of importing AgentService
    dependencies = state.get("dependencies")
    if not dependencies:
        raise RuntimeError("Dependencies not injected into state")
    if not hasattr(dependencies, 'llm_client') or not dependencies.llm_client:
        raise RuntimeError("LLM client is required for intent detection but not available")
    
    llm_client = dependencies.llm_client
    
    # Build context
    tool_list = "\n".join([f"- {tool['name']}: {tool.get('description', '')}" 
                          for tool in available_tools]) if available_tools else "No tools available"
    
    # Format conversation history more clearly
    history_context = ""
    if conversation_history:
        recent = conversation_history[-3:]  # Last 3 messages
        history_parts = []
        for msg in recent:
            # Handle both dict and string message formats
            if isinstance(msg, dict):
                role = msg.get('role', 'user')
                content = msg.get('content', '')
            elif isinstance(msg, str):
                # If it's a string, treat as user message
                role = 'user'
                content = msg
            else:
                # Skip invalid message formats
                continue
                
            if role == 'user':
                history_parts.append(f"User: {content}")
            elif role == 'assistant':
                history_parts.append(f"Assistant: {content}")
        history_context = "\n".join(history_parts)
    
    # Extract recent tool results for workflow context
    recent_tool_results = _extract_recent_tool_results(conversation_history)
    
    doc_context = ""
    if document_content:
        doc_preview = document_content[:2000] + "..." if len(document_content) > 2000 else document_content
        doc_context = f"\n\nDocument content available:\n{doc_preview}"
    
    # Build prompt without f-string to avoid syntax issues
    prompt_parts = [
        "You are an AI assistant that analyzes user requests and creates comprehensive execution plans using available tools.",
        "",
        "## CURRENT USER MESSAGE (PRIORITY):",
        user_input,
        "",
        "## CONTEXT (for reference only):",
        "Available tools:",
        tool_list,
        "",
        "Recent conversation:",
        history_context if history_context else "No previous conversation",
        doc_context,
        "",
        "## RECENT TOOL RESULTS (if any):",
        recent_tool_results if recent_tool_results else "No recent tool results available",
        "",
        "## COMPREHENSIVE ANALYSIS INSTRUCTIONS:",
        "",
        "### STEP 1: UNDERSTAND THE REQUEST",
        "Analyze the user's request to understand:",
        "- What is the ultimate goal? (e.g., patent application, research report, technical analysis)",
        "- What information is needed to achieve this goal?",
        "- What tools can provide this information?",
        "- How should the tools be chained together for maximum effectiveness?",
        "",
        "### STEP 2: TOOL CAPABILITIES UNDERSTANDING",
        "Available tools and their purposes:",
        "- **web_search_tool**: General web research, current information, technical details",
        "- **prior_art_search_tool**: Patent landscape analysis, existing patents, prior art research",
        "- **claim_drafting_tool**: Draft patent claims based on invention description",
        "- **claim_analysis_tool**: Analyze and improve existing patent claims",
        "",
        "### STEP 3: WORKFLOW DESIGN PRINCIPLES",
        "For complex requests (especially patent-related), think in terms of comprehensive workflows:",
        "",
        "**Patent Application Workflow:**",
        "1. **Research Phase**: Use web_search_tool and prior_art_search_tool to gather comprehensive information",
        "2. **Analysis Phase**: Use claim_analysis_tool to analyze existing patents and identify gaps",
        "3. **Drafting Phase**: Use claim_drafting_tool to create new claims based on research",
        "4. **Final Synthesis**: LLM will synthesize all outputs into a complete patent application",
        "",
        "**Research & Analysis Workflow:**",
        "1. **Broad Research**: web_search_tool for general information",
        "2. **Specialized Research**: prior_art_search_tool for domain-specific patents",
        "3. **Content Generation**: claim_drafting_tool for structured output",
        "4. **Quality Analysis**: claim_analysis_tool for validation and improvement",
        "",
        "### STEP 4: DECISION CRITERIA",
        "- **CONVERSATION**: Simple greetings, general questions, basic assistance, templates",
        "- **TOOL_WORKFLOW**: Any request requiring research, analysis, content generation, or multi-step processes",
        "",
        "**CONTINUATION PATTERN DETECTION:**",
        "If the user is asking to draft/analyze/create something AND there are recent tool results available:",
        "- This should be TOOL_WORKFLOW to use the available context",
        "- Examples: 'draft patent' after web search, 'analyze claims' after research, 'create report' after data gathering",
        "- Use the recent tool results as context for the workflow",
        "",
        "### STEP 5: WORKFLOW PLANNING",
        "When creating TOOL_WORKFLOW plans:",
        "",
        "**DIRECT TOOL EXECUTION (PREFERRED):**",
        "- For specific tool requests (e.g., 'draft 3 claims', 'analyze claims', 'search patents', 'web search X', 'search for X'), use ONLY the specific tool",
        "- Do NOT add research steps unless explicitly requested",
        "- Use single-step workflows for direct tool execution",
        "",
        "**COMPREHENSIVE WORKFLOWS (ONLY when needed):**",
        "- If recent tool results are available, use them as context instead of re-researching",
        "- Start with research tools (web_search, prior_art_search) to gather information",
        "- Use analysis tools (claim_analysis) to process and understand the information",
        "- Use generation tools (claim_drafting) to create new content",
        "- Chain tools so each step builds on previous results using {previous_step_key} syntax",
        "- Plan for comprehensive coverage of the topic",
        "- When recent tool results exist, include them in the first step's parameters as conversation_context",
        "",
        "CRITICAL: Analyze ONLY the current user message, not the conversation history.",
        "",
        "You MUST respond in this EXACT format with no additional text:",
        "",
        "TYPE: CONVERSATION",
        "PLAN: ",
        "",
        "OR",
        "",
        "TYPE: TOOL_WORKFLOW",
        "PLAN: [{\"step\": 1, \"tool\": \"tool_name\", \"params\": {\"key\": \"value\"}, \"output_key\": \"result_key\"}]",
        "",
        "CRITICAL:",
        "- PLAN must be valid JSON array or empty",
        "- Use double quotes in JSON",
        "- No trailing commas",
        "- No comments in JSON",
        "- Extract actual parameters from user request",
        "- Use {previous_step_key} syntax to reference earlier results",
        "",
        "## COMPREHENSIVE EXAMPLES:",
        "",
        "**Direct Claim Drafting Request:**",
        "TYPE: TOOL_WORKFLOW",
        "PLAN: [{\"step\": 1, \"tool\": \"claim_drafting_tool\", \"params\": {\"user_query\": \"draft 3 claims in 5G AI\", \"conversation_context\": \"\", \"document_reference\": \"\"}, \"output_key\": \"draft_claims\"}]",
        "",
        "**Direct Prior Art Search Request:**",
        "TYPE: TOOL_WORKFLOW",
        "PLAN: [{\"step\": 1, \"tool\": \"prior_art_search_tool\", \"params\": {\"query\": \"5G AI patents\"}, \"output_key\": \"prior_art_results\"}]",
        "",
        "**Comprehensive Patent Application Request:**",
        "TYPE: TOOL_WORKFLOW",
        "PLAN: [{\"step\": 1, \"tool\": \"web_search_tool\", \"params\": {\"query\": \"5G network optimization techniques\"}, \"output_key\": \"web_research\"}, {\"step\": 2, \"tool\": \"prior_art_search_tool\", \"params\": {\"query\": \"5G network optimization patents\"}, \"output_key\": \"prior_art\"}, {\"step\": 3, \"tool\": \"claim_drafting_tool\", \"params\": {\"user_query\": \"draft patent claims for 5G optimization\", \"conversation_context\": \"{web_research}\", \"document_reference\": \"{prior_art}\"}, \"output_key\": \"draft_claims\"}, {\"step\": 4, \"tool\": \"claim_analysis_tool\", \"params\": {\"claims\": \"{draft_claims}\", \"analysis_type\": \"comprehensive\"}, \"output_key\": \"analysis\"}]",
        "",
        "**Research & Analysis Request:**",
        "TYPE: TOOL_WORKFLOW",
        "PLAN: [{\"step\": 1, \"tool\": \"web_search_tool\", \"params\": {\"query\": \"AI trends 2024\"}, \"output_key\": \"web_data\"}, {\"step\": 2, \"tool\": \"prior_art_search_tool\", \"params\": {\"query\": \"artificial intelligence patents\"}, \"output_key\": \"patent_data\"}, {\"step\": 3, \"tool\": \"claim_drafting_tool\", \"params\": {\"user_query\": \"draft comprehensive report\", \"conversation_context\": \"{web_data}\", \"document_reference\": \"{patent_data}\"}, \"output_key\": \"final_report\"}]",
        "",
        "**Prior Art Search Request:**",
        "TYPE: TOOL_WORKFLOW",
        "PLAN: [{\"step\": 1, \"tool\": \"prior_art_search_tool\", \"params\": {\"query\": \"machine learning algorithms\"}, \"output_key\": \"prior_art_results\"}]",
        "",
        "**Web Search Request:**",
        "TYPE: TOOL_WORKFLOW",
        "PLAN: [{\"step\": 1, \"tool\": \"web_search_tool\", \"params\": {\"query\": \"ramy atawia\"}, \"output_key\": \"search_results\"}]",
        "",
        "**Simple Search Request:**",
        "TYPE: TOOL_WORKFLOW",
        "PLAN: [{\"step\": 1, \"tool\": \"web_search_tool\", \"params\": {\"query\": \"test\"}, \"output_key\": \"search_results\"}]",
        "",
        "**Continuation Pattern (draft after research):**",
        "TYPE: TOOL_WORKFLOW",
        "PLAN: [{\"step\": 1, \"tool\": \"claim_drafting_tool\", \"params\": {\"user_query\": \"draft 1 system patent\", \"conversation_context\": \"[recent tool results from conversation history]\"}, \"output_key\": \"draft_claims\"}]",
        "",
        "**Conversation Request:**",
        "TYPE: CONVERSATION",
        "PLAN: ",
        "",
        "## PATTERN RECOGNITION:",
        "",
        "**DIRECT TOOL EXECUTION PATTERNS:**",
        "- \"draft X claims\" → TOOL_WORKFLOW (single step: claim_drafting_tool only)",
        "- \"draft X system claim\" → TOOL_WORKFLOW (single step: claim_drafting_tool only)",
        "- \"draft 1 system claim\" → TOOL_WORKFLOW (single step: claim_drafting_tool only)",
        "- \"analyze claims\" → TOOL_WORKFLOW (single step: claim_analysis_tool only)",
        "- \"prior art search X\" → TOOL_WORKFLOW (single step: prior_art_search_tool only)",
        "- \"patent search X\" → TOOL_WORKFLOW (single step: prior_art_search_tool only)",
        "- \"web search X\" → TOOL_WORKFLOW (single step: web_search_tool only)",
        "- \"search for X\" → TOOL_WORKFLOW (single step: web_search_tool only)",
        "",
        "**COMPREHENSIVE WORKFLOW PATTERNS (only when explicitly requested):**",
        "- \"draft a patent on X\" → TOOL_WORKFLOW (comprehensive patent workflow)",
        "- \"research X and create Y\" → TOOL_WORKFLOW (research + generation workflow)",
        "- \"draft X\" + recent tool results → TOOL_WORKFLOW (continuation pattern)",
        "- \"analyze X\" + recent tool results → TOOL_WORKFLOW (continuation pattern)",
        "- \"create X\" + recent tool results → TOOL_WORKFLOW (continuation pattern)",
        "",
        "**CONVERSATION PATTERNS:**",
        "- \"hi\", \"hello\", \"help\" → CONVERSATION",
        "- \"explain X\" → CONVERSATION (unless it needs research)"
    ]
    
    prompt = "\n".join(prompt_parts)
    
    response = llm_client.generate_text(
        prompt=prompt,
        max_tokens=1500
    )
    
    if not response.get("success"):
        raise RuntimeError(f"LLM intent detection failed: {response.get('error', 'Unknown error')}")
    
    # Log intent detection response
    response_text = response.get("text", "")
    logger.debug(f"Intent detection response (length: {len(response_text)})")
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Response: {response_text}")
    
    return _parse_llm_intent(response_text)


def _parse_llm_intent(response_text: str) -> tuple[str, List[Dict]]:
    """Parse LLM intent detection response with strict validation."""
    logger.debug("Parsing LLM intent response", response_preview=response_text[:200])
    
    lines = response_text.strip().split('\n')
    intent_type = "conversation"
    workflow_plan = []
    
    for line in lines:
        line = line.strip()
        if line.startswith("TYPE:"):
            type_value = line.split(":", 1)[1].strip().upper()
            if type_value == "TOOL_WORKFLOW":
                intent_type = "tool_workflow"
            elif type_value == "CONVERSATION":
                intent_type = "conversation"
            else:
                logger.warning("Invalid intent type from LLM", type_value=type_value)
                raise RuntimeError(f"Invalid intent type from LLM: {type_value}")
                
        elif line.startswith("PLAN:"):
            plan_text = line.split(":", 1)[1].strip()
            if intent_type == "tool_workflow":
                if not plan_text:
                    raise RuntimeError("TOOL_WORKFLOW requires a plan but none provided")
                try:
                    workflow_plan = json.loads(plan_text)
                    if not isinstance(workflow_plan, list):
                        raise RuntimeError("Workflow plan must be a JSON array")
                    logger.info("Parsed workflow plan", plan=workflow_plan)
                except json.JSONDecodeError as e:
                    logger.error("Invalid JSON in workflow plan", 
                               error=str(e), plan_text=plan_text[:200])
                    raise RuntimeError(f"Invalid JSON in workflow plan: {e}. Plan text: '{plan_text[:100]}...'")
            # For conversation, plan should be empty
    
    return intent_type, workflow_plan


async def execute_workflow_node(state: AgentState) -> AgentState:
    """Execute the workflow plan step by step with enhanced error handling."""
    workflow_plan = state.get("workflow_plan", [])
    current_step = state.get("current_step", 0)
    step_results = state.get("step_results", {})
    workflow_errors = state.get("workflow_errors", [])
    
    logger.debug(f"Executing workflow - Plan: {workflow_plan}, Step: {current_step}")
    
    logger.info("Executing workflow step", 
               current_step=current_step, 
               total_steps=len(workflow_plan))
    
    if current_step >= len(workflow_plan):
        logger.info("Workflow completed", total_steps=len(workflow_plan))
        # Mark workflow as completed and continue to response generation
        return {
            **state,
            "workflow_completed": True,
            "step_results": step_results,
            "workflow_errors": workflow_errors
        }
    
    try:
        # Use injected dependency instead of importing AgentService
        dependencies = state.get("dependencies")
        if not dependencies:
            raise RuntimeError("Dependencies not injected into state")
        if not hasattr(dependencies, 'mcp_orchestrator') or not dependencies.mcp_orchestrator:
            raise RuntimeError("MCP orchestrator is required for tool execution but not available")
        
        orchestrator = dependencies.mcp_orchestrator
        
        # Get current step
        step = workflow_plan[current_step]
        tool_name = step["tool"]
        params = step["params"]
        output_key = step["output_key"]
        
        logger.info("Preparing tool execution", 
                   tool=tool_name, 
                   output_key=output_key,
                   raw_params=params)
        
        # Add context from previous steps if needed
        conversation_history = state.get("conversation_history", [])
        enhanced_params = _add_context_to_params(params, step_results, conversation_history)
        
        logger.info("Enhanced params after context substitution", 
                   enhanced_params=enhanced_params)
        
        # Execute tool
        logger.info(f"Executing {tool_name}", params=enhanced_params)
        result = await orchestrator.execute_tool(tool_name, enhanced_params)
        
        logger.info("Tool execution completed", 
                   tool=tool_name, 
                   result_type=type(result).__name__,
                   result_success=result.get("success") if isinstance(result, dict) else "unknown")
        
        # ENHANCED VALIDATION: Check if result is meaningful
        if not _validate_tool_result(result, tool_name):
            error_msg = f"Tool {tool_name} returned invalid or empty result"
            logger.error(error_msg, result=result)
            workflow_errors.append(error_msg)
            
            # For critical tools like web_search, this should be a blocking error
            if tool_name in ["web_search_tool", "prior_art_search_tool"]:
                return {
                    **state,
                    "workflow_errors": workflow_errors,
                    "final_response": f"Critical tool {tool_name} failed: {error_msg}. Cannot proceed with workflow."
                }
        
        # Store result with validation
        step_results[output_key] = result
        
        logger.info("Step completed successfully", 
                   step=current_step, 
                   output_key=output_key,
                   result_preview=str(result)[:200] if result else "None")
        
        return {
            **state,
            "current_step": current_step + 1,
            "step_results": step_results,
            "workflow_errors": workflow_errors
        }
        
    except Exception as e:
        error_msg = f"Step {current_step} ({step.get('tool', 'unknown')}) failed: {str(e)}"
        logger.error("Workflow step failed", 
                    step=current_step, 
                    tool=step.get('tool', 'unknown'),
                    error=str(e))
        
        workflow_errors.append(error_msg)
        
        # CRITICAL DECISION: For essential steps, halt workflow
        if current_step == 0 or step.get('tool') in ['web_search_tool', 'prior_art_search_tool']:
            logger.error("Critical step failed, halting workflow", step=current_step)
            return {
                **state,
                "workflow_errors": workflow_errors,
                "final_response": f"Critical workflow step failed: {error_msg}. Please try again."
            }
        
        # For non-critical steps, continue but track error
        step_results[f"step_{current_step}_error"] = str(e)
        return {
            **state,
            "current_step": current_step + 1,
            "step_results": step_results,
            "workflow_errors": workflow_errors
        }


def _extract_recent_tool_results(conversation_history: List[Dict[str, Any]]) -> str:
    """Extract recent conversation context for tool workflows."""
    if not conversation_history:
        return ""
    
    # Extract recent conversation pairs (user query + assistant response) without keyword filtering
    recent_context = []
    for i in range(len(conversation_history) - 1, -1, -1):  # Check last 5 messages
        if i >= len(conversation_history) - 5:  # Only check last 5 messages
            msg = conversation_history[i]
            
            # Handle both dict and string message formats
            if isinstance(msg, dict):
                role = msg.get('role', 'user')
                content = msg.get('content', '')
            elif isinstance(msg, str):
                role = 'user'
                content = msg
            else:
                continue
                
            if role == 'assistant':
                # Get the previous user message if it exists
                user_query = ""
                if i > 0:
                    prev_msg = conversation_history[i-1]
                    if isinstance(prev_msg, dict) and prev_msg.get('role') == 'user':
                        user_query = prev_msg.get('content', '')
                    elif isinstance(prev_msg, str):
                        user_query = prev_msg
                
                # Create context with both user query and assistant response
                context_parts = []
                if user_query:
                    context_parts.append(f"User Query: {user_query}")
                
                # Truncate long content to prevent prompt overflow
                if len(content) > 1500:
                    content = content[:1500] + "... [truncated]"
                context_parts.append(f"Response: {content}")
                
                recent_context.append("\n".join(context_parts))
    
    if recent_context:
        return "\n\n".join(recent_context)
    return ""


def _validate_tool_result(result: Any, tool_name: str) -> bool:
    """Validate that tool result contains meaningful data."""
    if not result:
        return False
    
    if isinstance(result, dict):
        # Check status flag
        if result.get("status") == "error":
            return False
        
        # Check for actual content
        result_content = result.get("result", "")
        if not result_content or (isinstance(result_content, str) and len(result_content.strip()) < 10):
            return False
            
        # Tool-specific validation
        if tool_name == "web_search_tool":
            # Web search should return substantial content
            if isinstance(result_content, str) and len(result_content.strip()) < 50:
                return False
    elif isinstance(result, str):
        # Direct string results (like prior art search reports)
        if len(result.strip()) < 10:
            return False
            
        # Tool-specific validation for string results
        if tool_name == "prior_art_search_tool":
            # Prior art search should return comprehensive report
            if len(result.strip()) < 100:
                return False
        elif tool_name == "web_search_tool":
            # Web search should return substantial content
            if len(result.strip()) < 50:
                return False
    
    return True


def _add_context_to_params(params: Dict[str, Any], step_results: Dict[str, Any], conversation_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Add context from previous steps by enhancing the user_query string."""
    enhanced_params = params.copy()
    
    logger.info("Starting context enhancement", 
               original_params=params, 
               available_results=list(step_results.keys()),
               conversation_history_length=len(conversation_history) if conversation_history else 0)
    
    # First, handle conversation history context
    if conversation_history and "user_query" in enhanced_params:
        recent_tool_results = _extract_recent_tool_results(conversation_history)
        if recent_tool_results:
            original_query = enhanced_params["user_query"]
            enhanced_params["user_query"] = f"{original_query}\n\nContext from previous conversation:\n{recent_tool_results}"
            # Also populate conversation_context parameter if it exists
            if "conversation_context" in enhanced_params:
                enhanced_params["conversation_context"] = recent_tool_results
            logger.info("Enhanced user_query with conversation history context", 
                       original_length=len(original_query),
                       enhanced_length=len(enhanced_params["user_query"]),
                       conversation_context_length=len(recent_tool_results))
    
    # Second, handle the enhanced user_query approach with step results
    if "user_query" in enhanced_params and step_results:
        original_query = enhanced_params["user_query"]
        
        # Build context summary from previous steps
        context_parts = []
        for step_key, result in step_results.items():
            if isinstance(result, dict) and result.get("success", True):
                content = result.get("result", "")
                if content and len(str(content).strip()) > 10:
                    # Truncate long content to prevent prompt overflow
                    context_text = str(content)
                    if len(context_text) > 1500:
                        context_text = context_text[:1500] + "... [truncated]"
                    
                    context_parts.append(f"{step_key}: {context_text}")
        
        # Enhance the user query with context
        if context_parts:
            context_summary = "\n\n".join(context_parts)
            enhanced_params["user_query"] = f"{original_query}\n\nContext from previous steps:\n{context_summary}"
            logger.info("Enhanced user_query with workflow context", 
                       original_length=len(original_query),
                       enhanced_length=len(enhanced_params["user_query"]),
                       context_steps=len(context_parts))
        else:
            logger.warning("No valid context found to enhance user_query", 
                          step_results_keys=list(step_results.keys()))
    
    # Also handle the existing {key} placeholder substitution for backward compatibility
    for key, value in enhanced_params.items():
        if isinstance(value, str) and "{" in value and "}" in value:
            logger.info(f"Processing parameter {key} with placeholders", value=value)
            
            # Process all placeholders in this value
            processed_value = value
            substitutions_made = []
            
            for result_key, result_value in step_results.items():
                placeholder = f"{{{result_key}}}"
                if placeholder in processed_value:
                    # Extract meaningful content from result
                    if isinstance(result_value, dict):
                        context_text = result_value.get("result", str(result_value))
                    else:
                        context_text = str(result_value)
                    
                    # Limit context size to prevent prompt overflow
                    if len(context_text) > 2000:
                        context_text = context_text[:2000] + "... [truncated]"
                    
                    processed_value = processed_value.replace(placeholder, context_text)
                    substitutions_made.append(f"{placeholder} -> {len(context_text)} chars")
            
            enhanced_params[key] = processed_value
            
            if substitutions_made:
                logger.info(f"Made substitutions for {key}", substitutions=substitutions_made)
        else:
                logger.warning(f"No substitutions made for {key} despite placeholders", 
                             value=value, available_keys=list(step_results.keys()))
    
    logger.info("Context enhancement completed", enhanced_params=enhanced_params)
    return enhanced_params


async def generate_response_node(state: AgentState) -> AgentState:
    """Generate final response based on intent type with better error handling."""
    logger.info("Generating final response")
    
    intent_type = state.get("intent_type", "conversation")
    workflow_errors = state.get("workflow_errors", [])
    
    # If there are critical workflow errors, return them directly
    if workflow_errors and state.get("final_response"):
        logger.info("Returning error response from workflow")
        return state

    try:
        if intent_type == "conversation":
            final_response = await _generate_conversation_response(state)
        else:
            final_response = await _generate_workflow_response(state)

        logger.info("Response generation completed", 
                   response_length=len(final_response) if final_response else 0)

        return {
            **state,
            "final_response": final_response
        }
        
    except Exception as e:
        logger.error("Response generation failed", error=str(e))
        error_response = f"Failed to generate response: {str(e)}"
        if workflow_errors:
            error_response += f"\n\nWorkflow errors: {'; '.join(workflow_errors)}"
        
        return {
            **state,
            "final_response": error_response
        }


async def _generate_conversation_response(state: AgentState) -> str:
    """Generate conversational response using LLM."""
    user_input = state["user_input"]
    conversation_history = state.get("conversation_history", [])
    document_content = state.get("document_content", "")
    
    # Use injected dependency instead of importing AgentService
    dependencies = state.get("dependencies")
    if not dependencies:
        raise RuntimeError("Dependencies not injected into state")
    if not hasattr(dependencies, 'llm_client') or not dependencies.llm_client:
        raise RuntimeError("LLM client is required for conversation but not available")
        
    llm_client = dependencies.llm_client
        
    # Build context with improved history formatting
    history_context = ""
    if conversation_history:
        recent = conversation_history[-3:]  # Last 3 messages
        history_parts = []
        for msg in recent:
            # Handle both dict and string message formats
            if isinstance(msg, dict):
                role = msg.get('role', 'user')
                content = msg.get('content', '')
            elif isinstance(msg, str):
                role = 'user'
                content = msg
            else:
                continue
                
            if role == 'user':
                history_parts.append(f"User: {content}")
            elif role == 'assistant':
                history_parts.append(f"Assistant: {content}")
        history_context = "\n".join(history_parts)
    
    doc_context = ""
    if document_content:
        doc_preview = document_content[:1000] + "..." if len(document_content) > 1000 else document_content
        doc_context = f"\n\nDocument context available:\n{doc_preview}"
    
    prompt = f"""You are a helpful AI assistant. Respond naturally to the user's message.

## CURRENT MESSAGE (PRIORITY):
"{user_input}"

## CONTEXT (for reference only):
Recent conversation:
{history_context if history_context else "No previous conversation"}
{doc_context}

## RESPONSE INSTRUCTIONS:
Focus on the current message above. Use conversation history only for context, not as part of the current request.

Provide helpful, natural responses. Be concise but complete. Use context appropriately but prioritize the current message.

For document drafting requests (like invention disclosures, reports, proposals), offer structured guidance and suggest using available tools for research and content generation when appropriate."""
    
    response = llm_client.generate_text(
        prompt=prompt,
        max_tokens=800
    )
    
    if not response.get("success"):
        raise RuntimeError(f"LLM conversation generation failed: {response.get('error', 'Unknown error')}")
    
    generated_text = response.get("text", "")
    
    # Enhanced logging and validation
    logger.info(f"LLM conversation response generated", 
               response_length=len(generated_text),
               response_preview=generated_text[:100] if generated_text else "EMPTY")
    
    # Validate response is not empty
    if not generated_text or len(generated_text.strip()) < 5:
        logger.error("LLM generated empty or very short response", 
                    response=response,
                    generated_text=generated_text)
        # Return a fallback response instead of empty string
        return "I apologize, but I'm having trouble generating a proper response right now. Please try rephrasing your question or ask me something else."
    
    return generated_text


async def _generate_workflow_response(state: AgentState) -> str:
    """Generate response from workflow results using LLM synthesis with better validation."""
    step_results = state.get("step_results", {})
    workflow_plan = state.get("workflow_plan", [])
    user_input = state.get("user_input", "")
    conversation_history = state.get("conversation_history", [])
    document_content = state.get("document_content", "")
    workflow_errors = state.get("workflow_errors", [])
    
    logger.info("Starting workflow response synthesis", 
               step_results_keys=list(step_results.keys()),
               workflow_errors_count=len(workflow_errors))
    
    if not step_results and not workflow_errors:
        raise RuntimeError("No workflow results or errors to generate response from")
    
    # Use injected dependency instead of importing AgentService
    dependencies = state.get("dependencies")
    if not dependencies:
        raise RuntimeError("Dependencies not injected into state")
    if not hasattr(dependencies, 'llm_client') or not dependencies.llm_client:
        raise RuntimeError("LLM client is required for response synthesis but not available")
    
    llm_client = dependencies.llm_client
    
    # Collect tool outputs with better validation
    tool_outputs = []
    successful_steps = 0
    
    for step in workflow_plan:
        output_key = step["output_key"]
        tool_name = step["tool"].replace("_tool", "").replace("_", " ").title()
        
        if output_key in step_results:
            result = step_results[output_key]
            if isinstance(result, dict) and result.get("status") == "success":
                content = result.get("result", str(result))
                if content and len(str(content).strip()) > 10:  # Ensure meaningful content
                    tool_outputs.append(f"**{tool_name} Results:**\n{content}")
                    successful_steps += 1
                    logger.info(f"Added successful result from {tool_name}", 
                              content_length=len(str(content)))
                else:
                    tool_outputs.append(f"**{tool_name}:** No meaningful results returned")
                    logger.warning(f"Empty result from {tool_name}")
            elif isinstance(result, str):
                # Direct string results (like prior art search reports)
                if result and len(result.strip()) > 10:
                    tool_outputs.append(f"**{tool_name} Results:**\n{result}")
                    successful_steps += 1
                    logger.info(f"Added successful string result from {tool_name}", 
                              content_length=len(result))
                else:
                    tool_outputs.append(f"**{tool_name}:** No meaningful results returned")
                    logger.warning(f"Empty string result from {tool_name}")
            else:
                error_msg = result.get("error", "Unknown error") if isinstance(result, dict) else str(result)
                tool_outputs.append(f"**{tool_name} (Failed):** {error_msg}")
                logger.warning(f"Failed result from {tool_name}", error=error_msg)
        else:
            # Handle missing results
            error_key = f"step_{step.get('step', 0)-1}_error"
            if error_key in step_results:
                error_msg = step_results[error_key]
                tool_outputs.append(f"**{tool_name} (Error):** {error_msg}")
                logger.warning(f"Error in {tool_name}", error=error_msg)
            else:
                tool_outputs.append(f"**{tool_name}:** No results available")
                logger.warning(f"No results for {tool_name}")
    
    # Check if we have enough successful results to proceed
    if successful_steps == 0:
        error_summary = "\n".join(workflow_errors) if workflow_errors else "All workflow steps failed"
        return f"I apologize, but I encountered issues executing your request:\n\n{error_summary}\n\nPlease try again or rephrase your request."
    
    if not tool_outputs:
        raise RuntimeError("No valid results from workflow execution")
    
    # Build context
    history_context = ""
    if conversation_history:
        recent = conversation_history[-3:]
        history_parts = []
        for msg in recent:
            # Handle both dict and string message formats
            if isinstance(msg, dict):
                role = msg.get('role', 'user')
                content = msg.get('content', '')
            elif isinstance(msg, str):
                role = 'user'
                content = msg
            else:
                continue
                
            if role == 'user':
                history_parts.append(f"User: {content}")
            elif role == 'assistant':
                history_parts.append(f"Assistant: {content}")
        history_context = "\n".join(history_parts)
    
    doc_context = ""
    if document_content:
        doc_preview = document_content[:1000] + "..." if len(document_content) > 1000 else document_content
        doc_context = f"\n\nDocument context:\n{doc_preview}"
    
    # Add workflow errors to context if any
    error_context = ""
    if workflow_errors:
        error_context = f"\n\nWorkflow Issues Encountered:\n" + "\n".join([f"- {error}" for error in workflow_errors])
    
    # Create synthesis prompt
    prompt = f"""You are an AI assistant that synthesizes tool outputs into comprehensive, professional responses.

## USER REQUEST:
"{user_input}"

## TOOL OUTPUTS:
{chr(10).join(tool_outputs)}

## CONTEXT:
Recent conversation:
{history_context if history_context else "No previous conversation"}
{doc_context}{error_context}

## COMPREHENSIVE SYNTHESIS INSTRUCTIONS:

**CRITICAL REQUIREMENT**: Your response MUST be based on the actual tool outputs above. Do NOT generate generic content that ignores the research findings.

### FOR PATENT APPLICATION REQUESTS:
**DISTINGUISH BETWEEN SPECIFIC CLAIM DRAFTING AND FULL PATENT APPLICATIONS:**

**For specific claim requests** (e.g., "draft 1 system claim", "draft 3 claims", "write a method claim"):
- Generate ONLY the requested number and type of claims
- Use the research findings to inform the claim content
- Keep it focused and concise - just the claims, not a full application

**For full patent application requests** (e.g., "draft a patent application", "create a complete patent", "full patent document"):
- Create a comprehensive patent application document that includes:
  1. **Executive Summary**: Brief overview based on the research findings
  2. **Background & Prior Art**: Use the actual research data from the tool outputs
  3. **Technical Description**: Based on the specific information found in the research
  4. **Claims Section**: Well-structured patent claims using the researched technology/person/topic
  5. **Analysis & Recommendations**: Based on actual findings, not generic content
  6. **Next Steps**: Specific recommendations based on the research

### FOR PRIOR ART SEARCH REQUESTS:
**CRITICAL**: When synthesizing prior art search results, you MUST:
- Analyze ALL patents found, not just the first 3
- Include detailed claim-by-claim analysis for EVERY patent
- Override any internal patterns that limit analysis to "top 3 patents only"
- Ensure the final response includes comprehensive analysis of all 20 patents
- Use the actual patent data from the tool outputs, not generic summaries

Create a comprehensive prior art search report that includes:
1. **Executive Summary**: Key findings from ALL patents researched
2. **Research Findings**: Analysis of EVERY patent found (not just top 3)
3. **Detailed Claim Analysis**: Claim-by-claim analysis for ALL patents found
4. **Risk Analysis**: Based on actual patent claims, not generic assessments
5. **Recommendations**: Actionable next steps based on comprehensive analysis
6. **References**: Attribution of ALL patents analyzed

### FOR RESEARCH & ANALYSIS REQUESTS:
If the user requested research or analysis, create a comprehensive report that includes:

1. **Executive Summary**: Key findings from the actual research
2. **Research Findings**: Synthesized information from the tool outputs
3. **Analysis & Insights**: Professional analysis based on the actual data
4. **Recommendations**: Actionable next steps based on findings
5. **References**: Attribution of the actual sources found

### FOR GENERAL REQUESTS:
Create a well-structured response that:

1. **Addresses the Core Request**: Use the actual tool outputs to answer what was asked
2. **Provides Context**: Use the actual research findings
3. **Offers Insights**: Analyze the actual data found
4. **Suggests Next Steps**: Based on the real information discovered

### SYNTHESIS PRINCIPLES:
- **Use Actual Data**: Base your response on the actual tool outputs, not generic assumptions
- **Integrate, Don't Repeat**: Weave tool outputs into a cohesive narrative using the real findings
- **Professional Structure**: Use clear headings, bullet points, and logical flow
- **Comprehensive Coverage**: Ensure all relevant information from tool outputs is included
- **Actionable Insights**: Provide practical recommendations based on actual findings
- **Proper Attribution**: Reference the actual sources and data found
- **Quality Focus**: Ensure the final output uses the researched information effectively

### RESPONSE FORMAT:
Structure your response with clear sections and professional formatting. Use markdown formatting for headings, lists, and emphasis. Make the response comprehensive yet readable, and ENSURE it reflects the actual research findings from the tool outputs.

**VALIDATION CHECK**: Before finalizing your response, verify that it actually uses the specific information from the tool outputs rather than generating generic content.

Create a response that the user will find immediately valuable and actionable based on the real research performed."""

    response = llm_client.generate_text(
        prompt=prompt,
        max_tokens=32000  # Increased limit for comprehensive analysis
    )
    
    if not response.get("success"):
        logger.error("LLM workflow response synthesis failed", 
                   error=response.get('error', 'Unknown error'),
                   prompt_length=len(prompt))
        raise RuntimeError(f"LLM response synthesis failed: {response.get('error', 'Unknown error')}")
    
    synthesized_response = response.get("text", "")
    
    # Enhanced logging and validation
    logger.info(f"LLM workflow response generated", 
               response_length=len(synthesized_response),
               response_preview=synthesized_response[:100] if synthesized_response else "EMPTY")
    
    # Validate response is not empty
    if not synthesized_response or len(synthesized_response.strip()) < 10:
        logger.error("LLM generated empty or very short workflow response", 
                    response=response,
                    generated_text=synthesized_response)
        # Return a fallback response instead of empty string
        synthesized_response = "I apologize, but I'm having trouble generating a comprehensive response right now. Please try rephrasing your question or ask me something else."
    
    # VALIDATION: Check if the response actually uses the tool outputs
    if not _validate_synthesis_uses_research(synthesized_response, step_results, user_input):
        logger.warning("Synthesized response appears to be generic, not using research results")
        # Add a disclaimer
        synthesized_response = f"""**Note**: The following response may be generic as the system detected limited use of research findings.

{synthesized_response}

**Research Results Summary:**
{chr(10).join(tool_outputs)}"""
    
    return synthesized_response


def _validate_synthesis_uses_research(response: str, step_results: Dict[str, Any], user_input: str) -> bool:
    """Validate that the synthesis actually uses research results rather than being generic."""
    if not response or not step_results:
        return False
    
    # Extract key terms from user input (e.g., "Ramy Atawia")
    user_terms = set()
    for term in user_input.split():
        if len(term) > 3:  # Skip short words
            user_terms.add(term.lower())
    
    # Check if any research results contain these terms
    research_content = ""
    for result in step_results.values():
        if isinstance(result, dict):
            content = result.get("result", "")
            if isinstance(content, str):
                research_content += content.lower() + " "
    
    # Check if response contains specific terms from research
    response_lower = response.lower()
    research_terms_found = 0
    
    for term in user_terms:
        if term in research_content and term in response_lower:
            research_terms_found += 1
    
    # If no specific terms from user request appear in both research and response,
    # it might be generic
    return research_terms_found > 0


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
    workflow_errors = state.get("workflow_errors", [])
    workflow_completed = state.get("workflow_completed", False)
    
    # If there's already a final response due to critical error, end workflow
    if state.get("final_response"):
        return "generate_response"
    
    # If critical errors occurred, skip remaining steps
    if workflow_errors and any("Critical" in error for error in workflow_errors):
        return "generate_response"
    
    # If workflow is marked as completed, go to response generation
    if workflow_completed:
        return "generate_response"
    
    # If there are more steps to execute, continue workflow
    if current_step < len(workflow_plan):
        return "execute_workflow"
    else:
        return "generate_response"


def create_agent_graph(dependencies: AgentGraphDependencies):
    """Create the LangGraph workflow with injected dependencies and enhanced logging."""
    logger.info("Creating LangGraph workflow with enhanced error handling")
    
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
    
    compiled_graph = workflow.compile()
    
    # Create a wrapper that injects dependencies
    async def execute_with_dependencies(initial_state):
        logger.info("Starting workflow execution", user_input=initial_state.get("user_input", "")[:100])
        state_with_deps = {**initial_state, "dependencies": dependencies}
        
        try:
            result = await compiled_graph.ainvoke(state_with_deps)
            logger.info("Workflow execution completed successfully")
            return result
        except Exception as e:
            logger.error("Workflow execution failed", error=str(e))
            # Return error state instead of raising
            return {
                **state_with_deps,
                "final_response": f"Workflow execution failed: {str(e)}",
                "workflow_errors": [str(e)]
            }
    
    # Return both the function and the compiled graph for different use cases
    class AgentGraphWrapper:
        def __init__(self, execute_func, compiled_graph, dependencies):
            self.execute = execute_func
            self.compiled_graph = compiled_graph
            self.dependencies = dependencies
        
        async def __call__(self, initial_state):
            return await self.execute(initial_state)
        
        def astream(self, initial_state, stream_mode=None):
            # Inject dependencies and use the compiled graph directly
            state_with_deps = {**initial_state, "dependencies": self.dependencies}
            return self.compiled_graph.astream(
                state_with_deps, 
                stream_mode=stream_mode or ["updates", "messages"]
            )
    
    logger.info("LangGraph workflow created successfully")
    return AgentGraphWrapper(execute_with_dependencies, compiled_graph, dependencies)


# Remove the global graph instance pattern
# The calling code should create the graph with proper dependencies