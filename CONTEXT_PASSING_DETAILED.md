# LangGraph Context Passing - Complete Breakdown

## 🎯 Your Question: What Context Gets Passed Between Tools?

**Answer: YES! The context passing includes original history, document content, AND results from previous steps.**

## 📊 Complete Context Flow

### **Initial State (What Gets Passed to ALL Tools)**
```json
{
  "user_input": "web search ramy atawia, and then draft 5 claims",
  "document_content": "Document content from Word (if available)",
  "conversation_history": [
    {
      "role": "user", 
      "content": "Previous user messages"
    },
    {
      "role": "assistant", 
      "content": "Previous AI responses"
    }
  ],
  "available_tools": ["web_search_tool", "claim_drafting_tool", ...]
}
```

### **Step 1: Web Search Tool Execution**
```json
{
  "tool": "web_search_tool",
  "parameters": {
    "query": "ramy atawia"
  },
  "context_passed": {
    "document_content": "Document content from Word",
    "conversation_history": "Previous chat history",
    "user_input": "Original query"
  }
}
```

**Step 1 Output:**
```json
{
  "step_results": {
    "1": {
      "status": "success",
      "result": "# Web Search Results for: ramy atawia\n\n[10 search results...]",
      "tool_name": "web_search_tool"
    }
  }
}
```

### **Step 2: Claim Drafting Tool Execution**
```json
{
  "tool": "claim_drafting_tool",
  "parameters": {
    "user_query": "draft 5 claims",
    "conversation_context": "{web_search_results}",  // ← Context from Step 1
    "document_reference": "{document_content}"       // ← Original document
  },
  "context_passed": {
    "document_content": "Document content from Word",
    "conversation_history": "Previous chat history", 
    "user_input": "Original query",
    "web_search_results": "Results from Step 1"      // ← NEW: Step 1 results
  }
}
```

## 🔄 Context Substitution Mechanism

### **How Context Gets Injected:**

```python
def _prepare_parameters_with_context(parameters, step_results, state):
    """Prepare tool parameters with context substitution."""
    
    for key, value in parameters.items():
        if value.startswith("{") and value.endswith("}"):
            context_key = value[1:-1]  # Remove braces
            
            if context_key == "web_search_results":
                # Get web search results from step 1
                web_results = step_results.get(1, {})
                prepared_params[key] = web_results["result"]
            
            elif context_key == "document_content":
                # Get original document content
                prepared_params[key] = state["document_content"]
            
            elif context_key == "conversation_history":
                # Get chat history
                prepared_params[key] = state["conversation_history"]
            
            # ... more context substitutions
```

## 📋 Complete Context Inventory

### **What Each Tool Receives:**

#### **1. Web Search Tool (Step 1)**
```json
{
  "query": "ramy atawia",
  "document_content": "Word document content (if available)",
  "conversation_history": "Previous chat messages",
  "user_input": "Original query: 'web search ramy atawia, and then draft 5 claims'"
}
```

#### **2. Claim Drafting Tool (Step 2)**
```json
{
  "user_query": "draft 5 claims",
  "conversation_context": "{web_search_results}",  // ← Step 1 results
  "document_reference": "{document_content}",      // ← Original document
  "document_content": "Word document content",     // ← Direct access
  "conversation_history": "Previous chat messages", // ← Direct access
  "user_input": "Original query"                   // ← Direct access
}
```

## 🎯 Context Passing Patterns

### **Pattern 1: Web Search + Prior Art Search**
```json
Step 1: web_search_tool
├─ Input: {"query": "AI patents"}
└─ Output: Web search results

Step 2: prior_art_search_tool  
├─ Input: {
│   "query": "AI patents",
│   "web_context": "{web_search_results}"  // ← Step 1 results
│ }
└─ Output: Patent search results
```

### **Pattern 2: Claim Drafting + Analysis**
```json
Step 1: claim_drafting_tool
├─ Input: {"user_query": "draft 5 claims"}
└─ Output: Drafted claims

Step 2: claim_analysis_tool
├─ Input: {
│   "user_query": "analyze claims",
│   "claims_context": "{draft_claims}"     // ← Step 1 results
│ }
└─ Output: Claim analysis
```

### **Pattern 3: Web Search + Claim Drafting (Your Query)**
```json
Step 1: web_search_tool
├─ Input: {"query": "ramy atawia"}
└─ Output: Search results about Ramy Atawia

Step 2: claim_drafting_tool
├─ Input: {
│   "user_query": "draft 5 claims",
│   "conversation_context": "{web_search_results}",  // ← Step 1 results
│   "document_reference": "{document_content}"       // ← Original document
│ }
└─ Output: Claims incorporating search context
```

## 🔍 Context Substitution Keys

### **Available Context Variables:**
- `{web_search_results}` → Results from web search tool
- `{prior_art_results}` → Results from prior art search tool  
- `{draft_claims}` → Results from claim drafting tool
- `{claim_analysis}` → Results from claim analysis tool
- `{document_content}` → Original Word document content
- `{conversation_history}` → Previous chat messages
- `{user_input}` → Original user query

### **Context Flow Example:**
```
Original Query: "web search ramy atawia, and then draft 5 claims"
                    ↓
Step 1: web_search_tool
├─ Receives: document_content, conversation_history, user_input
├─ Executes: Search for "ramy atawia"  
└─ Returns: 10 search results about Ramy Atawia
                    ↓
Step 2: claim_drafting_tool
├─ Receives: 
│   ├─ document_content (original)
│   ├─ conversation_history (original)
│   ├─ user_input (original)
│   └─ web_search_results (from Step 1) ← NEW!
├─ Executes: Draft 5 claims using search context
└─ Returns: Claims incorporating Ramy Atawia's expertise
```

## 🎯 Key Benefits

1. **Complete Context**: Every tool gets full context (document + history + previous results)
2. **Progressive Enhancement**: Each step builds on previous results
3. **Flexible Substitution**: Tools can reference any previous step's output
4. **Original Preservation**: Original document and chat history always available
5. **Smart Routing**: Context flows automatically based on workflow dependencies

## 📊 Context Passing Summary

**YES, the context passing includes:**
- ✅ **Original document content** (from Word)
- ✅ **Conversation history** (previous chat messages)
- ✅ **User input** (original query)
- ✅ **Previous step results** (web search results → claim drafting)
- ✅ **Tool-specific context** (conversation_context, document_reference, etc.)

**The claim drafting tool receives:**
- The original Word document content
- The previous chat history
- The original user query
- **PLUS** the web search results from Step 1 as context for drafting relevant claims

This ensures that the drafted claims are not only based on the search results but also incorporate the full context of the conversation and document! 🎯
