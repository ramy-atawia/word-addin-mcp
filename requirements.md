# **📋 DETAILED REQUIREMENTS LIST**

## **🎯 CORE ARCHITECTURE REQUIREMENTS**

### **Requirement 1: Single Endpoint Design**
- **Endpoint**: `/api/v1/mcp/agent/chat`
- **Purpose**: Handle all user requests through one endpoint
- **Behavior**: Frontend sends message + context, backend returns complete response

---

## **📤 FRONTEND REQUIREMENTS**

### **Requirement 2: Request Format**
- **Field**: `message` (string)
  - **Content**: User's input text
  - **Type**: Simple string

- **Field**: `context` (object)
  - **Sub-field**: `document_content` (string)
    - **Content**: Word document text content
    - **Fallback**: "Document content unavailable" if failed
    - **Limit**: Truncated to 5000 characters if too long
  - **Sub-field**: `chat_history` (string)
    - **Format**: Multi-line string with "role: content" format
    - **Example**: 
      ```
      user: Hello
      assistant: Hi there! How can I help you?
      user: hi
      ```

### **Requirement 3: API Call Flow**
```
User types message
    ↓
Frontend gathers context (document content + chat history)
    ↓
Single API call to /api/v1/mcp/agent/chat
    ↓
Display response to user
```

---

## **📥 BACKEND RESPONSE REQUIREMENTS**

### **Requirement 4: Response Format**
- **Field**: `response` (string)
  - **Content**: Complete AI response or tool execution result

- **Field**: `intent_type` (string)
  - **Values**: "greeting", "help", "conversation", "document_analysis", "text_processing", "web_content", "file_operations", "unknown"

- **Field**: `routing_decision` (string)
  - **Values**: "conversational_ai", "text_processor", "document_analyzer", "web_content_fetcher", "file_reader", "data_formatter"

- **Field**: `tools_used` (array of strings)
  - **Content**: List of tool names that were executed

- **Field**: `execution_time` (float)
  - **Content**: Time taken to process the request in seconds

- **Field**: `success` (boolean)
  - **Content**: Whether the request was processed successfully

- **Field**: `error` (string, optional)
  - **Content**: Error message if something went wrong

---

## **�� BACKEND PROCESSING REQUIREMENTS**

### **Requirement 5: Agent Processing Flow**
1. **Receive** message + context from frontend
2. **Detect intent** using LLM
3. **Make routing decision** (conversational AI vs. tool execution)
4. **Execute tools** if needed
5. **Generate response** (either conversational or tool result)
6. **Return** complete response to frontend

### **Requirement 6: Tool Routing**
- **Web Content Requests** → Route to `web_search_tool`
- **Text Processing** → Route to `text_analysis_tool`
- **Document Analysis** → Route to `text_analysis_tool`
- **Conversational** → Use LLM for chat response

### **Requirement 7: Context Processing**
- **Document Content**: Pass to LLM for context-aware responses
- **Chat History**: Convert string format to structured format for LLM processing
- **Available Tools**: Provide tool list to LLM for routing decisions

---

## **✅ SUCCESS CRITERIA**

### **Requirement 8: Functional Requirements**
1. **User types "hi"** → Single API call → Get greeting response
2. **User types "search for AI"** → Single API call → Get web search results
3. **User types "analyze document"** → Single API call → Get document analysis
4. **All responses** include intent type, routing decision, and execution time

### **Requirement 9: Performance Requirements**
1. **Response time**: < 5 seconds for simple queries
2. **Response time**: < 10 seconds for tool-based queries
3. **API calls**: Maximum 1 per user request
4. **Error handling**: Graceful fallbacks with clear error messages

---

## **�� CONSTRAINTS**

### **Requirement 10: System Constraints**
1. **Single API call** per user request
2. **Backend handles all complexity** internally
3. **Frontend only sends and receives** data
4. **No frontend routing logic**
5. **No multiple endpoint calls** for single request

---

## **📝 IMPLEMENTATION REQUIREMENTS**

### **Requirement 11: Technical Requirements**
1. **Create** `/api/v1/mcp/agent/chat` endpoint
2. **Integrate** with existing AgentService
3. **Connect** to MCP hub for tool execution
4. **Handle** Azure OpenAI for conversational responses
5. **Provide** comprehensive error handling
6. **Include** detailed logging for debugging


## Agent --> MCP

# The agent after reoslving the intent and identifies the tool it shall call the what? mcp client or mc

# The mcp client will make