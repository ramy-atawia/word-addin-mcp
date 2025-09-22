"""
Clean LangGraph Agent Service

Pure LLM-driven agent with no keyword logic, no fallbacks, no mock data.
Fails fast with clear errors when dependencies are missing.

Features:
- Pure LLM intent detection and planning
- Clean unified state management
- Clear workflow routing
- No hardcoded patterns or fallbacks
"""

import structlog
import json
from typing import TypedDict, List, Dict, Any, Optional

logger = structlog.get_logger()

# LangGraph import - fail clearly if not available
try:
    from langgraph.graph import StateGraph, END
except ImportError:
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
    """Detect whether this is a conversation or tool workflow using LLM."""
    logger.debug("Detecting intent with LLM")
    
    # Always use LLM for intent detection - no keyword logic
    intent_type, workflow_plan = await _llm_intent_detection(state)
    
    return {
        **state,
        "intent_type": intent_type,
        "workflow_plan": workflow_plan,
            "current_step": 0,
            "step_results": {}
        }
    

async def _llm_intent_detection(state: AgentState) -> tuple[str, List[Dict]]:
    """Use LLM for intent detection and workflow planning."""
    user_input = state["user_input"]
    available_tools = state.get("available_tools", [])
    conversation_history = state.get("conversation_history", [])
    document_content = state.get("document_content", "")
    
    from app.services.agent import AgentService
    agent_service = AgentService()
    
    llm_client = agent_service._get_llm_client()
    if not llm_client:
        raise RuntimeError("LLM client is required for intent detection but not available")
    
    # Build context
    tool_list = "\n".join([f"- {tool['name']}: {tool.get('description', '')}" 
                          for tool in available_tools]) if available_tools else "No tools available"
    
    # Format conversation history more clearly
    history_context = ""
    if conversation_history:
        recent = conversation_history[-3:]  # Last 3 messages
        history_parts = []
        for msg in recent:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'user':
                history_parts.append(f"User: {content}")
            elif role == 'assistant':
                history_parts.append(f"Assistant: {content}")
        history_context = "\n".join(history_parts)
    
    doc_context = ""
    if document_content:
        doc_preview = document_content[:2000] + "..." if len(document_content) > 2000 else document_content
        doc_context = f"\n\nDocument content available:\n{doc_preview}"
    
    prompt = f"""You are an AI assistant that analyzes user requests and creates comprehensive execution plans using available tools.

## CURRENT USER MESSAGE (PRIORITY):
"{user_input}"

## CONTEXT (for reference only):
Available tools:
{tool_list}

Recent conversation:
{history_context if history_context else "No previous conversation"}
{doc_context}

## COMPREHENSIVE ANALYSIS INSTRUCTIONS:

### STEP 1: UNDERSTAND THE REQUEST
Analyze the user's request to understand:
- What is the ultimate goal? (e.g., patent application, research report, technical analysis)
- What information is needed to achieve this goal?
- What tools can provide this information?
- How should the tools be chained together for maximum effectiveness?

### STEP 2: TOOL CAPABILITIES UNDERSTANDING
Available tools and their purposes:
- **web_search_tool**: General web research, current information, technical details
- **prior_art_search_tool**: Patent landscape analysis, existing patents, prior art research
- **claim_drafting_tool**: Draft patent claims based on invention description
- **claim_analysis_tool**: Analyze and improve existing patent claims

### STEP 3: WORKFLOW DESIGN PRINCIPLES
For complex requests (especially patent-related), think in terms of comprehensive workflows:

**Patent Application Workflow:**
1. **Research Phase**: Use web_search_tool and prior_art_search_tool to gather comprehensive information
2. **Analysis Phase**: Use claim_analysis_tool to analyze existing patents and identify gaps
3. **Drafting Phase**: Use claim_drafting_tool to create new claims based on research
4. **Final Synthesis**: LLM will synthesize all outputs into a complete patent application

**Research & Analysis Workflow:**
1. **Broad Research**: web_search_tool for general information
2. **Specialized Research**: prior_art_search_tool for domain-specific patents
3. **Content Generation**: claim_drafting_tool for structured output
4. **Quality Analysis**: claim_analysis_tool for validation and improvement

### STEP 4: DECISION CRITERIA
- **CONVERSATION**: Simple greetings, general questions, basic assistance, templates
- **TOOL_WORKFLOW**: Any request requiring research, analysis, content generation, or multi-step processes

### STEP 5: WORKFLOW PLANNING
When creating TOOL_WORKFLOW plans:
- Start with research tools (web_search, prior_art_search) to gather information
- Use analysis tools (claim_analysis) to process and understand the information
- Use generation tools (claim_drafting) to create new content
- Chain tools so each step builds on previous results using {{previous_step_key}} syntax
- Plan for comprehensive coverage of the topic

CRITICAL: Analyze ONLY the current user message, not the conversation history.

You MUST respond in this EXACT format with no additional text:

TYPE: CONVERSATION
PLAN: 

OR

TYPE: TOOL_WORKFLOW  
PLAN: [{{"step": 1, "tool": "tool_name", "params": {{"key": "value"}}, "output_key": "result_key"}}]

CRITICAL: 
- PLAN must be valid JSON array or empty
- Use double quotes in JSON
- No trailing commas
- No comments in JSON
- Extract actual parameters from user request
- Use {{previous_step_key}} syntax to reference earlier results

## COMPREHENSIVE EXAMPLES:

**Patent Application Request:**
TYPE: TOOL_WORKFLOW
PLAN: [{{"step": 1, "tool": "web_search_tool", "params": {{"query": "5G network optimization techniques"}}, "output_key": "web_research"}}, {{"step": 2, "tool": "prior_art_search_tool", "params": {{"query": "5G network optimization patents"}}, "output_key": "prior_art"}}, {{"step": 3, "tool": "claim_drafting_tool", "params": {{"user_query": "draft patent claims for 5G optimization", "conversation_context": "{{web_research}}", "document_reference": "{{prior_art}}"}}, "output_key": "draft_claims"}}, {{"step": 4, "tool": "claim_analysis_tool", "params": {{"claims": "{{draft_claims}}", "analysis_type": "comprehensive"}}, "output_key": "analysis"}}]

**Research & Analysis Request:**
TYPE: TOOL_WORKFLOW
PLAN: [{{"step": 1, "tool": "web_search_tool", "params": {{"query": "AI trends 2024"}}, "output_key": "web_data"}}, {{"step": 2, "tool": "prior_art_search_tool", "params": {{"query": "artificial intelligence patents"}}, "output_key": "patent_data"}}, {{"step": 3, "tool": "claim_drafting_tool", "params": {{"user_query": "draft comprehensive report", "conversation_context": "{{web_data}}", "document_reference": "{{patent_data}}"}}, "output_key": "final_report"}}]

**Simple Search Request:**
TYPE: TOOL_WORKFLOW
PLAN: [{{"step": 1, "tool": "web_search_tool", "params": {{"query": "test"}}, "output_key": "search_results"}}]

**Conversation Request:**
TYPE: CONVERSATION
PLAN: 

## PATTERN RECOGNITION:
- "draft a patent on X" → TOOL_WORKFLOW (comprehensive patent workflow)
- "research X and create Y" → TOOL_WORKFLOW (research + generation workflow)
- "analyze X" → TOOL_WORKFLOW (analysis workflow)
- "search for X" → TOOL_WORKFLOW (search workflow)
- "hi", "hello", "help" → CONVERSATION
- "explain X" → CONVERSATION (unless it needs research)"""
    
    response = llm_client.generate_text(
        prompt=prompt,
        max_tokens=1500,
        temperature=0.1
    )
    
    if not response.get("success"):
        raise RuntimeError(f"LLM intent detection failed: {response.get('error', 'Unknown error')}")
    
    return _parse_llm_intent(response.get("text", ""))


def _parse_llm_intent(response_text: str) -> tuple[str, List[Dict]]:
    """Parse LLM intent detection response with strict validation."""
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
                except json.JSONDecodeError as e:
                    raise RuntimeError(f"Invalid JSON in workflow plan: {e}")
            # For conversation, plan should be empty
    
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
        # Store error but continue to next step
        step_results[f"step_{current_step}_error"] = str(e)
        return {
            **state,
            "current_step": current_step + 1,
            "step_results": step_results
        }


def _add_context_to_params(params: Dict[str, Any], step_results: Dict[str, Any]) -> Dict[str, Any]:
    """Add context from previous steps to parameters."""
    enhanced_params = params.copy()
    
    # Simple context injection using {{key}} syntax
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
    """Generate conversational response using LLM."""
    user_input = state["user_input"]
    conversation_history = state.get("conversation_history", [])
    document_content = state.get("document_content", "")
    
    from app.services.agent import AgentService
    agent_service = AgentService()
    
    llm_client = agent_service._get_llm_client()
    if not llm_client:
        raise RuntimeError("LLM client is required for conversation but not available")
        
    # Build context with improved history formatting
    history_context = ""
    if conversation_history:
        recent = conversation_history[-3:]  # Last 3 messages
        history_parts = []
        for msg in recent:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
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
        max_tokens=800,
        temperature=0.7
    )
    
    if not response.get("success"):
        raise RuntimeError(f"LLM conversation generation failed: {response.get('error', 'Unknown error')}")
    
    return response.get("text", "")


async def _generate_workflow_response(state: AgentState) -> str:
    """Generate response from workflow results using LLM synthesis."""
    step_results = state.get("step_results", {})
    workflow_plan = state.get("workflow_plan", [])
    user_input = state.get("user_input", "")
    conversation_history = state.get("conversation_history", [])
    document_content = state.get("document_content", "")
    
    if not step_results:
        raise RuntimeError("No workflow results to generate response from")
    
    from app.services.agent import AgentService
    agent_service = AgentService()
    
    llm_client = agent_service._get_llm_client()
    if not llm_client:
        raise RuntimeError("LLM client is required for response synthesis but not available")
    
    # Collect tool outputs
    tool_outputs = []
    for step in workflow_plan:
        output_key = step["output_key"]
        if output_key in step_results:
            result = step_results[output_key]
            if isinstance(result, dict) and result.get("success", True):
                content = result.get("result", str(result))
                tool_name = step["tool"].replace("_tool", "").replace("_", " ").title()
                tool_outputs.append(f"**{tool_name}:**\n{content}")
    else:
                # Handle failed steps
                error_key = f"step_{step['step']-1}_error"
                if error_key in step_results:
                    error_msg = step_results[error_key]
                    tool_outputs.append(f"**{step['tool']} (Failed):** {error_msg}")
    
    if not tool_outputs:
        raise RuntimeError("No valid results from workflow execution")
    
    # Build context
    history_context = ""
    if conversation_history:
        recent = conversation_history[-3:]
        history_parts = []
        for msg in recent:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'user':
                history_parts.append(f"User: {content}")
            elif role == 'assistant':
                history_parts.append(f"Assistant: {content}")
        history_context = "\n".join(history_parts)
    
    doc_context = ""
    if document_content:
        doc_preview = document_content[:1000] + "..." if len(document_content) > 1000 else document_content
        doc_context = f"\n\nDocument context:\n{doc_preview}"
    
    # Create synthesis prompt
    prompt = f"""You are an AI assistant that synthesizes tool outputs into comprehensive, professional responses.

## USER REQUEST:
"{user_input}"

## TOOL OUTPUTS:
{chr(10).join(tool_outputs)}

## CONTEXT:
Recent conversation:
{history_context if history_context else "No previous conversation"}
{doc_context}

## COMPREHENSIVE SYNTHESIS INSTRUCTIONS:

### FOR PATENT APPLICATION REQUESTS:
If the user requested patent-related work (drafting, analysis, research), create a comprehensive patent application document that includes:

1. **Executive Summary**: Brief overview of the invention and its novelty
2. **Background & Prior Art**: Synthesize research findings and prior art analysis
3. **Technical Description**: Detailed technical explanation of the invention
4. **Claims Section**: Well-structured patent claims (if claim drafting was performed)
5. **Analysis & Recommendations**: Quality analysis and improvement suggestions
6. **Next Steps**: Recommendations for further development or filing

### FOR RESEARCH & ANALYSIS REQUESTS:
If the user requested research or analysis, create a comprehensive report that includes:

1. **Executive Summary**: Key findings and insights
2. **Research Findings**: Synthesized information from all sources
3. **Analysis & Insights**: Professional analysis of the data
4. **Recommendations**: Actionable next steps
5. **References**: Proper attribution of sources

### FOR GENERAL REQUESTS:
Create a well-structured response that:

1. **Addresses the Core Request**: Directly answer what was asked
2. **Provides Context**: Use research findings to provide comprehensive context
3. **Offers Insights**: Go beyond just presenting data to provide analysis
4. **Suggests Next Steps**: Recommend logical follow-up actions

### SYNTHESIS PRINCIPLES:
- **Integrate, Don't Repeat**: Weave tool outputs into a cohesive narrative
- **Professional Structure**: Use clear headings, bullet points, and logical flow
- **Comprehensive Coverage**: Ensure all relevant information is included
- **Actionable Insights**: Provide practical recommendations and next steps
- **Proper Attribution**: Reference sources appropriately
- **Quality Focus**: Ensure the final output is publication-ready

### RESPONSE FORMAT:
Structure your response with clear sections and professional formatting. Use markdown formatting for headings, lists, and emphasis. Make the response comprehensive yet readable.

Create a response that the user will find immediately valuable and actionable."""
    
    response = llm_client.generate_text(
        prompt=prompt,
        max_tokens=2000,
        temperature=0.3
    )
    
    if not response.get("success"):
        raise RuntimeError(f"LLM response synthesis failed: {response.get('error', 'Unknown error')}")
    
    return response.get("text", "")


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
    """Create the LangGraph workflow."""
    logger.info("Creating LangGraph workflow")
    
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