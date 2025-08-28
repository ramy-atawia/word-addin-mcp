# 🔄 User Request Flow Schematic - Document Summarization

## 📱 **Complete Flow: UI → MCP Server → LLM → Response**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   📱 Word UI    │    │   🚀 FastAPI    │    │   🔧 MCP Server │    │   🤖 Azure      │
│   (Office.js)   │    │   Backend       │    │   (Tool Router) │    │   OpenAI        │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         │ 1. User uploads      │                       │                       │
         │    document &        │                       │                       │
         │    clicks "Summarize"│                       │                       │
         │                       │                       │                       │
         ▼                       │                       │                       │
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 2. Office.js makes HTTP request to FastAPI endpoint                                │
│    POST /api/v1/document/analyze                                                  │
│    Body: { file: document, analysis_type: "summary" }                            │
└─────────────────────────────────────────────────────────────────────────────────────┘
         │                       │                       │                       │
         │                       │                       │                       │
         │                       │ 3. Service calls      │                       │
         │                       │    MCP Server         │                       │
         │                       │                       │                       │
         │                       ▼                       │                       │
         │              ┌─────────────────────────────────────────────────────────┐
         │              │ 4. MCP Protocol: tools/call                            │
         │              │ {                                                      │
         │              │   "jsonrpc": "2.0",                                    │
         │              │   "method": "tools/call",                              │
         │              │   "params": {                                          │
         │              │     "name": "document_analyzer",                       │
         │              │     "arguments": {                                     │
         │              │       "file_path": "/path/to/doc",                     │
         │              │       "analysis_type": "summary"                       │
         │              │     }                                                  │
         │              │   }                                                    │
         │              │ }                                                      │
         │              └─────────────────────────────────────────────────────────┘
         │                       │                       │                       │
         │                       │                       │                       │
         │                       │                       ▼                       │
         │                       │              ┌─────────────────────────────────┐
         │                       │              │ 5. MCP Server routes to        │
         │                       │              │    Document Analyzer Tool      │
         │                       │              │    - Parses document           │
         │                       │              │    - Extracts text content     │
         │                       │              │    - Prepares for LLM          │
         │                       │              └─────────────────────────────────┘
         │                       │                       │                       │
         │                       │                       │                       │
         │                       │                       ▼                       │
         │                       │              ┌─────────────────────────────────┐
         │                       │              │ 6. LLM Client Service          │
         │                       │              │    - Creates prompt            │
         │                       │              │    - Calls Azure OpenAI        │
         │                       │              │    - Gets AI summary           │
         │                       │              └─────────────────────────────────┘
         │                       │                       │                       │
         │                       │                       │                       │
         │                       │                       ▼                       │
         │                       │              ┌─────────────────────────────────┐
         │                       │              │ 7. Azure OpenAI Response       │
         │                       │              │    - Generated summary         │
         │                       │              │    - Keywords extracted        │
         │                       │              │    - Sentiment analysis        │
         │                       │              └─────────────────────────────────┘
         │                       │                       │                       │
         │                       │                       │                       │
         │                       │                       │                       │
         │                       │              ┌─────────────────────────────────┐
         │                       │              │ 8. MCP Response Format         │
         │                       │              │ {                              │
         │                       │              │   "jsonrpc": "2.0",            │
         │                       │              │   "result": {                  │
         │                       │              │     "status": "success",       │
         │                       │              │     "summary": "AI summary...",│
         │                       │              │     "keywords": ["key1", ...], │
         │                       │              │     "sentiment": {...}         │
         │                       │              │   }                            │
         │                       │              │ }                              │
         │                       │              └─────────────────────────────────┘
         │                       │                       │                       │
         │                       ▼                       │                       │
         │              ┌─────────────────────────────────────────────────────────┐
         │              │ 9. FastAPI returns HTTP response to UI                  │
         │              │    Status: 200 OK                                      │
         │              │    Body: { summary, keywords, sentiment, ... }         │
         │              └─────────────────────────────────────────────────────────┘
         │                       │                       │                       │
         ▼                       │                       │                       │
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 10. Word UI displays results:                                                     │
│     - AI-generated summary                                                        │
│     - Extracted keywords                                                          │
│     - Sentiment analysis                                                          │
│     - Readability metrics                                                         │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## 🔧 **Key Components in the Flow:**

### **1. 📱 Word UI (Office.js)**
- User uploads document
- Clicks "Summarize" button
- Makes HTTP request to backend
- Displays results

### **2. 🚀 FastAPI Backend**
- Receives HTTP request
- Routes to appropriate service
- Handles authentication/validation
- Returns HTTP response

### **3. 🔧 MCP Server (Tool Router)**
- Implements MCP protocol (JSON-RPC 2.0)
- Routes tool calls to appropriate services
- Manages tool execution
- Returns standardized responses

### **4. 📄 Document Analyzer Service**
- Parses different document formats (PDF, DOCX, TXT)
- Extracts text content
- Prepares content for LLM analysis
- Manages file handling

### **5. 🤖 LLM Client Service**
- Creates prompts for different analysis types
- Calls Azure OpenAI API
- Processes AI responses
- Handles errors and retries

### **6. 🌐 Azure OpenAI**
- Provides AI models (GPT-4, etc.)
- Generates summaries, keywords, sentiment
- Returns structured analysis results

## 📊 **Data Flow Summary:**

```
User Request → HTTP → FastAPI → MCP Protocol → Tool Service → LLM → AI Response → MCP Response → HTTP Response → UI Display
```

## 🎯 **Key Benefits of This Architecture:**

✅ **Separation of Concerns** - Each component has a specific role  
✅ **Scalability** - Easy to add new tools and services  
✅ **Standards Compliance** - Uses MCP protocol for tool communication  
✅ **Flexibility** - Can easily swap LLM providers or add new analysis types  
✅ **Error Handling** - Robust error handling at each layer  
✅ **Performance** - Asynchronous processing where possible  

## 🔄 **Alternative Flows:**

- **Web Content Analysis**: UI → FastAPI → MCP → Web Content Fetcher → Web Scraping → LLM → Response
- **File Processing**: UI → FastAPI → MCP → File System Service → File Reading → LLM → Response
- **Data Formatting**: UI → FastAPI → MCP → Data Formatter Service → Processing → Response

This architecture ensures clean separation between UI, backend logic, tool execution, and AI services while maintaining the MCP protocol standards for tool communication.
