# Immediate Fixes Plan - Critical Issues

## 🚨 Priority 1: Fix Intent Detection (Immediate)

### Issue: Claim drafting queries treated as conversation
**Current Behavior:** `"draft 1 system claim"` → `conversation`
**Expected Behavior:** `"draft 1 system claim"` → `tool_workflow`

### Fix 1: Add Pattern-Based Fallback
**File:** `backend/app/services/langgraph_agent_unified.py`

```python
def _simple_intent_detection(user_input: str) -> str:
    """Simple pattern-based intent detection as fallback."""
    user_lower = user_input.lower()
    
    # Tool workflow patterns
    if any(pattern in user_lower for pattern in [
        "draft", "write claims", "generate claims", "create claims",
        "prior art search", "search patents", "patent search",
        "analyze claims", "analyze patents", "claim analysis",
        "web search", "search for", "find information"
    ]):
        return "tool_workflow"
    
    return "conversation"

# Modify detect_intent_node to use fallback
async def detect_intent_node(state: AgentState) -> AgentState:
    user_input = state["user_input"]
    
    # Try simple pattern detection first
    simple_intent = _simple_intent_detection(user_input)
    if simple_intent == "tool_workflow":
        # Use simple detection for basic tool queries
        return {
            **state,
            "intent_type": "tool_workflow",
            "workflow_plan": [{"step": 1, "tool": "claim_drafting_tool", "params": {"user_query": user_input}, "output_key": "draft_claims"}],
            "current_step": 0,
            "step_results": {}
        }
    
    # Fall back to LLM detection for complex queries
    # ... existing LLM detection code
```

### Fix 2: Enhance LLM Prompt
**File:** `backend/app/services/langgraph_agent_unified.py`

```python
# Add to _llm_intent_detection prompt
PATTERN_RECOGNITION = """
## CRITICAL PATTERN RECOGNITION:
- "draft X system claim" → ALWAYS TOOL_WORKFLOW
- "prior art search X" → ALWAYS TOOL_WORKFLOW  
- "analyze X" → ALWAYS TOOL_WORKFLOW
- "web search X" → ALWAYS TOOL_WORKFLOW
- "web search X and draft Y" → ALWAYS TOOL_WORKFLOW

## EXAMPLES:
- "draft 1 system claim" → TOOL_WORKFLOW
- "draft 2 system claims" → TOOL_WORKFLOW
- "prior art search AI" → TOOL_WORKFLOW
- "analyze patent claims" → TOOL_WORKFLOW
- "web search 5G and draft claims" → TOOL_WORKFLOW
"""
```

## 🚨 Priority 2: Fix Conversation History Propagation (Immediate)

### Issue: Context not passed between queries
**Current Behavior:** `"web search Ramy Atawia"` → `"draft 1 system claim"` (no context)
**Expected Behavior:** `"web search Ramy Atawia"` → `"draft 1 system claim"` (with Ramy Atawia context)

### Fix 1: Improve Context Extraction
**File:** `backend/app/services/langgraph_agent_unified.py`

```python
def _extract_recent_tool_results(conversation_history: List[Dict[str, Any]]) -> str:
    """Extract recent tool results from conversation history for context."""
    if not conversation_history:
        return ""
    
    # Look for recent assistant messages that contain tool results
    recent_tool_results = []
    for msg in conversation_history[-5:]:  # Check last 5 messages
        if msg.get('role') == 'assistant':
            content = msg.get('content', '')
            # Check if this looks like a tool result (contains research, analysis, etc.)
            if any(keyword in content.lower() for keyword in [
                'research', 'analysis', 'search results', 'findings', 'data', 
                'information', 'comprehensive', 'executive summary', 'overview'
            ]):
                # Truncate long content
                if len(content) > 1000:
                    content = content[:1000] + "... [truncated]"
                recent_tool_results.append(content)
    
    if recent_tool_results:
        return "\n\n".join(recent_tool_results)
    return ""
```

### Fix 2: Enhance Context Injection
**File:** `backend/app/services/langgraph_agent_unified.py`

```python
def _add_context_to_params(params: Dict[str, Any], step_results: Dict[str, Any]) -> Dict[str, Any]:
    """Add context from previous steps by enhancing the user_query string."""
    enhanced_params = params.copy()
    
    # First, handle the enhanced user_query approach
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
    
    return enhanced_params
```

## 🚨 Priority 3: Fix Timeout Issues (Immediate)

### Issue: Queries timing out after 60 seconds
**Current Behavior:** Complex queries timeout
**Expected Behavior:** All queries complete successfully

### Fix 1: Increase Timeout
**File:** `backend/app/services/agent.py`

```python
# In make_request method
response = requests.post(
    f"{BASE_URL}/api/v1/mcp/agent/chat",
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {self.token}"
    },
    json={
        "message": message,
        "session_id": session_id or f"test-{int(time.time())}"
    },
    timeout=120  # Increase from 60 to 120 seconds
)
```

### Fix 2: Add Query Complexity Detection
**File:** `backend/app/services/langgraph_agent_unified.py`

```python
def _is_complex_query(user_input: str) -> bool:
    """Detect if query is complex and needs more time."""
    complex_indicators = [
        "comprehensive", "detailed", "analysis", "research", "patent application",
        "multi-step", "workflow", "and draft", "and analyze", "and create"
    ]
    return any(indicator in user_input.lower() for indicator in complex_indicators)

# Use in detect_intent_node
if _is_complex_query(user_input):
    # Allocate more time for complex queries
    # Add progress indicators
    pass
```

## 🚨 Priority 4: Fix Workflow Response Generation (Immediate)

### Issue: "Failed to generate response: No workflow results or errors"
**Current Behavior:** Tool executes but response generation fails
**Expected Behavior:** Proper response generation from tool results

### Fix 1: Debug Response Generation
**File:** `backend/app/services/langgraph_agent_unified.py`

```python
async def _generate_workflow_response(state: AgentState) -> str:
    """Generate response from workflow results using LLM synthesis."""
    step_results = state.get("step_results", {})
    workflow_plan = state.get("workflow_plan", [])
    user_input = state.get("user_input", "")
    
    # Debug logging
    logger.info("Generating workflow response", 
               step_results_keys=list(step_results.keys()),
               workflow_plan_length=len(workflow_plan))
    
    if not step_results:
        logger.warning("No step results available for response generation")
        return "I apologize, but I couldn't generate a response from the workflow results. Please try again."
    
    # Ensure we have at least one successful step
    successful_steps = [k for k, v in step_results.items() if isinstance(v, dict) and v.get("success", True)]
    if not successful_steps:
        logger.warning("No successful steps found in workflow results")
        return "I apologize, but the workflow execution didn't produce any successful results. Please try again."
    
    # ... rest of the function
```

## 🧪 Testing Plan

### Immediate Testing (After each fix):
1. **Test Intent Detection:**
   ```bash
   python3 -c "
   from comprehensive_working_test import WorkingTestRunner
   runner = WorkingTestRunner()
   runner.run_test_case('Intent Test', ['draft 1 system claim'], ['tool_workflow'])
   "
   ```

2. **Test Conversation History:**
   ```bash
   python3 -c "
   from comprehensive_working_test import WorkingTestRunner
   runner = WorkingTestRunner()
   runner.run_test_case('History Test', ['web search Ramy Atawia', 'draft 1 system claim'], ['tool_workflow', 'tool_workflow'])
   "
   ```

3. **Test Timeout Fix:**
   ```bash
   python3 -c "
   from comprehensive_working_test import WorkingTestRunner
   runner = WorkingTestRunner()
   runner.run_test_case('Timeout Test', ['web search blockchain patents'], ['tool_workflow'])
   "
   ```

### Full Regression Testing:
```bash
python3 final_e2e_summary.py
```

## 📊 Success Criteria

After implementing these fixes:
- **Intent Detection:** 95%+ accuracy for claim drafting queries
- **Conversation History:** Context properly passed between queries
- **Timeout Issues:** <5% timeout rate
- **Response Generation:** 95%+ success rate
- **Overall Success Rate:** 90%+ across all test cases

## 🚀 Implementation Order

1. **Day 1:** Fix intent detection (Pattern-based fallback + LLM prompt)
2. **Day 2:** Fix conversation history propagation
3. **Day 3:** Fix timeout issues
4. **Day 4:** Fix workflow response generation
5. **Day 5:** Full testing and validation

Each fix should be tested immediately after implementation to ensure it works correctly.
