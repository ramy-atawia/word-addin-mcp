# End-to-End Logic Flow with LangGraph

## Complete System Architecture and Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    FRONTEND (Word Add-in)                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                    │
                                                    │ User Input
                                                    │ "hello" or "prior art search 5g ai, draft 2 claims"
                                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    API GATEWAY (Azure APIM)                                    │
│  • Authentication (Auth0 JWT)                                                                  │
│  • Rate Limiting                                                                               │
│  • Request Routing                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                    │
                                                    │ Authenticated Request
                                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND API ENDPOINT (/api/v1/mcp/agent/chat)                     │
│                                                                                                 │
│  1. Parse Request:                                                                              │
│     • Extract message, document_content, chat_history, available_tools                         │
│     • Parse JSON chat history from frontend                                                     │
│                                                                                                 │
│  2. Get Available Tools:                                                                        │
│     • Query MCP Orchestrator for available tools                                               │
│     • Build tools list dynamically                                                             │
│                                                                                                 │
│  3. Route to Agent Service:                                                                    │
│     • Check USE_LANGGRAPH environment variable                                                 │
│     • If true: → LangGraph Agent (NEW)                                                         │
│     • If false: → Original Agent (LEGACY)                                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                    │
                                                    │ Route Decision
                                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    LANGGRAPH AGENT FLOW                                        │
│                                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                          1. INTENT DETECTION NODE                                       │   │
│  │                                                                                         │   │
│  │  Input: user_input, conversation_history, document_content, available_tools            │   │
│  │                                                                                         │   │
│  │  Process:                                                                               │   │
│  │  • Get LLM client                                                                      │   │
│  │  • Create tool descriptions for LLM                                                    │   │
│  │  • Prepare conversation context (last 5 messages)                                      │   │
│  │  • Prepare document context (up to 10k chars)                                          │   │
│  │  • Send to LLM with structured prompt                                                  │   │
│  │                                                                                         │   │
│  │  LLM Prompt:                                                                           │   │
│  │  "Analyze user query and determine workflow type:                                      │   │
│  │   - SINGLE_TOOL: One tool execution                                                    │   │
│  │   - MULTI_STEP: Multiple sequential tool executions                                    │   │
│  │   - CONVERSATION: General conversation"                                                │   │
│  │                                                                                         │   │
│  │  Output:                                                                                │   │
│  │  • workflow_type: CONVERSATION/MULTI_STEP/SINGLE_TOOL                                  │   │
│  │  • selected_tool: tool_name or empty                                                   │   │
│  │  • intent_type: greeting/conversation/tool_execution/multi_step                        │   │
│  │  • tool_parameters: extracted parameters                                               │   │
│  │  • workflow_plan: [] for MULTI_STEP, None otherwise                                    │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                    │                                           │
│                                                    │ State Update                             │
│                                                    ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                          2. WORKFLOW PLANNING NODE                                      │   │
│  │                                                                                         │   │
│  │  Input: Updated state from intent detection                                            │   │
│  │                                                                                         │   │
│  │  Process:                                                                               │   │
│  │  • If workflow_plan is None → Skip (conversation or single tool)                      │   │
│  │  • If workflow_plan is [] → Plan multi-step workflow                                   │   │
│  │                                                                                         │   │
│  │  For Multi-Step Planning:                                                              │   │
│  │  • Get LLM client                                                                      │   │
│  │  • Prepare conversation and document context                                           │   │
│  │  • Send to LLM with workflow planning prompt                                          │   │
│  │                                                                                         │   │
│  │  LLM Prompt:                                                                           │   │
│  │  "Create step-by-step execution plan. Each step specifies:                            │   │
│  │   - step: step number                                                                  │   │
│  │   - tool: tool name to execute                                                        │   │
│  │   - params: parameters for the tool                                                   │   │
│  │   - output_key: key to store results"                                                 │   │
│  │                                                                                         │   │
│  │  Example Output:                                                                       │   │
│  │  [                                                                                     │   │
│  │    {"step": 1, "tool": "prior_art_search_tool", "params": {"query": "5g ai"},         │   │
│  │     "output_key": "prior_art_results"},                                               │   │
│  │    {"step": 2, "tool": "claim_drafting_tool", "params": {"user_query": "draft 2 claims", │   │
│  │     "prior_art_context": "{{prior_art_results}}"}, "output_key": "draft_results"}     │   │
│  │  ]                                                                                     │   │
│  │                                                                                         │   │
│  │  Output:                                                                                │   │
│  │  • workflow_plan: Array of step objects                                                │   │
│  │  • total_steps: Number of steps                                                        │   │
│  │  • current_step: 0 (starting step)                                                    │   │
│  │  • step_results: {} (empty results dict)                                              │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                    │                                           │
│                                                    │ State Update                             │
│                                                    ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                          3. ROUTING DECISION                                           │   │
│  │                                                                                         │   │
│  │  _route_workflow() function:                                                           │   │
│  │                                                                                         │   │
│  │  if intent_type in ["conversation", "greeting", "chat"]:                              │   │
│  │    → "response_generation" (Skip tool execution)                                       │   │
│  │  elif workflow_plan is not None and len(workflow_plan) > 0:                           │   │
│  │    → "tool_execution" (Multi-step workflow)                                           │   │
│  │  else:                                                                                 │   │
│  │    → "response_generation" (Single tool or conversation)                              │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                    │                                           │
│                                                    │ Route Decision                           │
│                                                    ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                          4. TOOL EXECUTION NODE                                        │   │
│  │                                                                                         │   │
│  │  Input: State with workflow_plan and current_step                                      │   │
│  │                                                                                         │   │
│  │  Process:                                                                               │   │
│  │  • Check if workflow_plan exists (multi-step)                                          │   │
│  │  • If yes: → _execute_multi_step_workflow()                                           │   │
│  │  • If no: → _execute_single_tool()                                                    │   │
│  │                                                                                         │   │
│  │  Multi-Step Execution:                                                                 │   │
│  │  • Get current step from workflow_plan[current_step]                                   │   │
│  │  • Prepare parameters with context substitution                                        │   │
│  │  • Call MCP Orchestrator to execute tool                                              │   │
│  │  • Store result in step_results[output_key]                                           │   │
│  │  • Increment current_step                                                              │   │
│  │                                                                                         │   │
│  │  Single Tool Execution:                                                                │   │
│  │  • Get MCP Orchestrator                                                               │   │
│  │  • Execute tool with parameters                                                        │   │
│  │  • Store result in tool_result                                                         │   │
│  │                                                                                         │   │
│  │  MCP Orchestrator:                                                                     │   │
│  │  • Routes to appropriate MCP server                                                    │   │
│  │  • Executes tool via MCP protocol                                                      │   │
│  │  • Returns formatted result                                                            │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                    │                                           │
│                                                    │ Tool Results                             │
│                                                    ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                          5. ROUTING DECISION (Multi-step)                              │   │
│  │                                                                                         │   │
│  │  _route_multi_step() function:                                                         │   │
│  │                                                                                         │   │
│  │  if current_step < total_steps:                                                        │   │
│  │    → "tool_execution" (Continue with next step)                                        │   │
│  │  else:                                                                                 │   │
│  │    → "response_generation" (All steps completed)                                       │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                    │                                           │
│                                                    │ Continue or Finish                      │
│                                                    ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │                          6. RESPONSE GENERATION NODE                                   │   │
│  │                                                                                         │   │
│  │  Input: State with tool results and workflow metadata                                  │   │
│  │                                                                                         │   │
│  │  Process:                                                                               │   │
│  │  • Check if multi-step workflow (workflow_plan + step_results)                         │   │
│  │  • If yes: → _generate_multi_step_response()                                          │   │
│  │  • If no: → _generate_single_tool_response()                                          │   │
│  │                                                                                         │   │
│  │  Multi-Step Response:                                                                  │   │
│  │  • Check for failed steps                                                              │   │
│  │  • Format each step result with proper headers                                         │   │
│  │  • Combine all results into comprehensive response                                     │   │
│  │                                                                                         │   │
│  │  Single Tool Response:                                                                 │   │
│  │  • If intent_type in ["conversation", "greeting", "chat"]:                            │   │
│  │    → _generate_conversational_response() (LLM-generated friendly response)            │   │
│  │  • If tool_result exists:                                                              │   │
│  │    → Extract and format tool result                                                    │   │
│  │  • If no tool_result:                                                                  │   │
│  │    → "I'm not sure how to help with that request."                                     │   │
│  │                                                                                         │   │
│  │  Conversational Response Generation:                                                   │   │
│  │  • Get LLM client                                                                      │   │
│  │  • Prepare conversation context                                                         │   │
│  │  • Send to LLM with conversational prompt                                              │   │
│  │  • Return friendly, helpful response                                                    │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                    │
                                                    │ Final Response
                                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND API RESPONSE FORMATTING                                   │
│                                                                                                 │
│  • Convert to AgentChatResponse format                                                         │
│  • Add execution metadata                                                                      │
│  • Include workflow information                                                                │
│  • Return structured JSON response                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                    │
                                                    │ JSON Response
                                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    API GATEWAY (Azure APIM)                                    │
│  • Response formatting                                                                         │
│  • CORS headers                                                                                │
│  • Response routing                                                                            │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                    │
                                                    │ Formatted Response
                                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    FRONTEND (Word Add-in)                                      │
│  • Display response in chat interface                                                          │
│  • Update conversation history                                                                 │
│  • Handle markdown formatting                                                                  │
│  • Show tool execution status                                                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

## Key Decision Points

### 1. Agent Selection
```
USE_LANGGRAPH=true  → LangGraph Agent (Unified, Multi-step capable)
USE_LANGGRAPH=false → Original Agent (Legacy, Single-tool only)
```

### 2. Intent Classification
```
"hello" → CONVERSATION → Skip tools → Generate friendly response
"search for AI patents" → SINGLE_TOOL → Execute tool → Format result
"search AI patents then draft claims" → MULTI_STEP → Plan workflow → Execute steps → Combine results
```

### 3. Workflow Routing
```
Conversation Intent → response_generation (Skip tool execution)
Multi-step Intent → tool_execution → response_generation
Single Tool Intent → tool_execution → response_generation
```

### 4. Multi-step Loop
```
For each step in workflow_plan:
  Execute tool → Store result → Increment step
  If more steps → Continue loop
  If all done → Generate combined response
```

## State Management

The LangGraph system maintains a unified `AgentState` that includes:

```typescript
interface AgentState {
  // Input
  user_input: string
  document_content: string
  conversation_history: Array<Message>
  available_tools: Array<Tool>
  
  // Tool Execution
  selected_tool: string
  tool_parameters: Record<string, any>
  tool_result: any
  
  // Response
  final_response: string
  intent_type: string
  
  // Multi-step Workflow
  workflow_plan: Array<WorkflowStep> | null
  current_step: number
  total_steps: number
  step_results: Record<string, any>
}
```

## Error Handling

- **LLM Failures**: Fallback to simple heuristics
- **Tool Execution Failures**: Continue with next step or return error
- **MCP Orchestrator Failures**: Return error response
- **Network Failures**: Retry with exponential backoff

## Performance Optimizations

- **Lazy Loading**: LLM client and MCP orchestrator initialized on demand
- **Context Truncation**: Conversation history limited to last 5 messages
- **Document Truncation**: Document content limited to 10k characters
- **Parallel Execution**: Future enhancement for independent tools

## Security Considerations

- **Authentication**: JWT validation at API Gateway
- **Input Validation**: Sanitize user input and parameters
- **Tool Authorization**: MCP orchestrator handles tool access control
- **Rate Limiting**: Applied at API Gateway level
