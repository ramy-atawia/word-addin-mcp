# Invention Disclosure Prompting Analysis

## Current Issue

The prompt "draft an invention disclosure" is ambiguous and may not be handled optimally by the current system.

## Current Prompt Analysis

### Intent Detection Prompt
```
For CONVERSATION: Simple responses, greetings, general writing help, explanations
For TOOL_WORKFLOW: Patent searches, claim drafting, technical analysis, data processing
```

**Problem**: "Invention disclosure" falls between categories - it's writing help but also patent-related.

### Available Tools
- `web_search_tool` - Search the web for information
- `prior_art_search_tool` - Search for prior art and patents  
- `claim_drafting_tool` - Draft patent claims based on input
- `claim_analysis_tool` - Analyze patent claims for quality and structure

**Problem**: No specific tool for invention disclosure drafting.

## Expected Behavior

For "draft an invention disclosure", the system should:

1. **Recognize** this as a patent-related document drafting request
2. **Suggest** using available tools to gather information
3. **Provide** structured guidance on invention disclosure format
4. **Offer** to help with specific sections

## Recommended Prompt Improvements

### 1. Enhanced Intent Classification

```
For CONVERSATION: Simple responses, greetings, general writing help, explanations
For TOOL_WORKFLOW: Patent searches, claim drafting, technical analysis, data processing, 
                   invention disclosure drafting, patent document preparation
```

### 2. Better Tool Routing

For invention disclosure requests, suggest:
- `web_search_tool` - Research invention disclosure templates and requirements
- `prior_art_search_tool` - Find related patents for background
- `claim_drafting_tool` - Draft preliminary claims based on disclosure

### 3. Enhanced Conversation Response

For invention disclosure requests in conversation mode, provide:
- Structured guidance on invention disclosure sections
- Template suggestions
- Offer to help with specific sections using available tools

## Test Scenarios

1. **Simple request**: "draft an invention disclosure"
   - Should: Provide general guidance + offer to help with specific sections
   
2. **Detailed request**: "draft an invention disclosure for AI patent search system"
   - Should: Suggest using tools to research and draft specific content
   
3. **Contextual request**: "I need help with the technical description section"
   - Should: Provide specific guidance for that section

## Implementation Strategy

1. **Update intent detection** to better classify invention disclosure requests
2. **Enhance conversation responses** for patent document drafting
3. **Add tool suggestions** for complex patent-related requests
4. **Create structured templates** for common patent documents
