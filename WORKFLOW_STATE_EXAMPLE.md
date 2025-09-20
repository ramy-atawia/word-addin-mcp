# LangGraph Workflow State Example

## 🎯 Your Query: "web search ramy atawia, and then draft 5 claims"

### Initial State
```json
{
  "user_input": "web search ramy atawia, and then draft 5 claims",
  "document_content": "Document content unavailable",
  "conversation_history": [],
  "available_tools": [
    "sequentialthinking", 
    "web_search_tool", 
    "prior_art_search_tool", 
    "claim_drafting_tool", 
    "claim_analysis_tool"
  ],
  "workflow_plan": [],
  "current_step": 0,
  "total_steps": 0,
  "step_results": {},
  "selected_tool": "",
  "tool_parameters": {},
  "final_response": "",
  "intent_type": "",
  "execution_metadata": {}
}
```

### After Intent Detection
```json
{
  "workflow_type": "multi_step",
  "intent": "research and draft",
  "tools": ["web_search_tool", "claim_drafting_tool"],
  "parameters": {
    "step1": {
      "tool": "web_search_tool", 
      "params": {"query": "ramy atawia"}
    },
    "step2": {
      "tool": "claim_drafting_tool", 
      "params": {
        "user_query": "draft 5 claims",
        "conversation_context": "{search_results}"
      }
    }
  },
  "execution_metadata": {
    "workflow_type": "multi_step",
    "complexity": "high",
    "estimated_steps": 2
  }
}
```

### After Workflow Planning
```json
{
  "workflow_plan": [
    {
      "step": 1,
      "tool": "web_search_tool",
      "parameters": {"query": "ramy atawia"},
      "depends_on": null,
      "output_key": "search_results"
    },
    {
      "step": 2,
      "tool": "claim_drafting_tool",
      "parameters": {
        "user_query": "draft 5 claims",
        "conversation_context": "{search_results}"
      },
      "depends_on": 1,
      "output_key": "draft_claims"
    }
  ],
  "total_steps": 2,
  "current_step": 0
}
```

### After Step 1 Execution (Web Search)
```json
{
  "step_results": {
    "search_results": {
      "status": "success",
      "result": "# Web Search Results for: ramy atawia\n\n## 1. Ramy Atawia - Thomson Reuters | LinkedIn\n**URL**: https://ca.linkedin.com/in/ramyatawia\n**Snippet**: I specialize in driving projects from ideation to launch, with a career spanning…\n\n## 2. Ramy Atawia - Google Scholar\n**URL**: https://scholar.google.com/citations?user=y5rme7cAAAAJ\n**Snippet**: Machine Learning, Artificial Intelligence, NLP, O-RAN, Network Management...\n\n[Additional search results...]"
    }
  },
  "current_step": 1
}
```

### After Step 2 Execution (Claim Drafting)
```json
{
  "step_results": {
    "search_results": "[Previous search results...]",
    "draft_claims": {
      "status": "success", 
      "result": "# Patent Claims\n\n## Claim 1 (Independent)\nA machine learning system configured to optimize network management in an Open Radio Access Network (O-RAN) environment, comprising:\n- a data acquisition module for collecting real-time network performance metrics;\n- a machine learning model trained on historical network data to predict network congestion and resource allocation needs;\n- a decision-making engine configured to dynamically adjust network parameters based on predictions from the machine learning model;\n- a user interface for displaying network status and recommendations for optimization.\n\n[Additional claims 2-5...]"
    }
  },
  "current_step": 2
}
```

### Final Response Generation
```json
{
  "final_response": "Here are the web search results for 'ramy atawia':\n\n[Search results about Ramy Atawia's expertise in AI, ML, O-RAN, network management, and semantic communications]\n\nBased on this research, here are 5 drafted patent claims:\n\n[5 professional patent claims that incorporate the search context and expertise areas]\n\n**Workflow Summary:**\n- Step 1: Web search completed successfully\n- Step 2: Patent claims drafted with context from search results\n- Total execution time: ~60 seconds\n- Context passing: ✅ Working",
  "intent_type": "multi_step_workflow",
  "workflow_metadata": {
    "total_steps": 2,
    "completed_steps": 2,
    "workflow_type": "research_and_draft"
  }
}
```

## 🔄 Flow Visualization

```
User Query
    ↓
┌─────────────────┐
│ Intent Detection│ ← LLM analyzes query
│                 │ ← Detects "web search" + "draft"
│                 │ ← Sets workflow_type: "multi_step"
└─────────────────┘
    ↓
┌─────────────────┐
│ Workflow        │ ← Creates execution plan
│ Planning        │ ← Maps tools to steps
│                 │ ← Sets context passing
└─────────────────┘
    ↓
┌─────────────────┐
│ Step 1:         │ ← Executes web_search_tool
│ Web Search      │ ← Query: "ramy atawia"
│                 │ ← Returns: Search results
└─────────────────┘
    ↓ (Context Passed)
┌─────────────────┐
│ Step 2:         │ ← Executes claim_drafting_tool
│ Claim Drafting  │ ← Uses search results as context
│                 │ ← Returns: 5 patent claims
└─────────────────┘
    ↓
┌─────────────────┐
│ Response        │ ← Combines all results
│ Generation      │ ← Formats final output
│                 │ ← Returns to frontend
└─────────────────┘
```

## 🚨 Error Scenarios

### Before Fix (What Was Happening)
```
Intent Detection → workflow_type: "multi_step"
    ↓
Routing Function → Returns "workflow_planning"
    ↓
Conditional Edges → Looks for "workflow_planning" key
    ↓
ERROR: 'workflow_planning' not found in mapping
    ↓
Workflow fails with routing error
```

### After Fix (What Happens Now)
```
Intent Detection → workflow_type: "multi_step"
    ↓
Routing Function → Returns "multi_step"
    ↓
Conditional Edges → Maps "multi_step" → "workflow_planning"
    ↓
Workflow Planning → Creates execution plan
    ↓
Multi-Step Execution → Runs tools in sequence
    ↓
Response Generation → Combines results
    ↓
SUCCESS: Complete workflow execution
```

## 🎯 Key Improvements

1. **Fixed Routing**: Proper mapping between workflow types and node names
2. **Context Passing**: Search results flow into claim drafting
3. **Error Handling**: Graceful fallbacks for unknown workflow types
4. **Multi-Step Logic**: Handles complex queries with multiple actions
5. **Tool Integration**: Seamless MCP tool execution
6. **LLM Enhancement**: AI-powered intent detection and response formatting

The system now properly handles your query "web search ramy atawia, and then draft 5 claims" by:
1. Detecting it as a multi-step workflow
2. Planning the execution sequence
3. Running web search first
4. Using search results as context for claim drafting
5. Combining everything into a comprehensive response
