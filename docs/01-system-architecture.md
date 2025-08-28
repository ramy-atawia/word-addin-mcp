# Word Add-in MCP System Architecture

## Overview

The Word Add-in MCP (Model Context Protocol) system is a comprehensive document analysis and AI-powered content processing platform that integrates with Microsoft Word through Office.js APIs. The system provides intelligent text processing, web content fetching, document analysis, and AI-enhanced content generation capabilities.

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                FRONTEND LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │   ChatInterface │  │  DocumentViewer │  │  ToolSelector   │                │
│  │   (React/TS)    │  │   (React/TS)    │  │   (React/TS)    │                │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                │
│           │                       │                       │                    │
│           └───────────────────────┼───────────────────────┘                    │
│                                   │                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                    Office.js Integration Layer                         │    │
│  │              (Document Access, UI Integration)                         │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP/HTTPS
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                        FastAPI Application                             │    │
│  │                           (Port 9000)                                  │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                   │                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                           API Gateway                                  │    │
│  │                    (MCP Protocol Endpoints)                            │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                   │                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         Service Layer                                  │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │    │
│  │  │   Agent     │ │   LLM       │ │   Tool      │ │  Validation │      │    │
│  │  │  Service    │ │  Client     │ │ Execution   │ │  Service    │      │    │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                   │                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                          Tool Layer                                     │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │    │
│  │  │   Text      │ │   Document │ │   Web       │ │   File      │      │    │
│  │  │ Processor   │ │  Analyzer  │ │  Content    │ │  Reader     │      │    │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘      │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL SERVICES                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │   Azure OpenAI  │  │   Google Search │  │   File System   │                │
│  │   (GPT-4)       │  │   API           │  │   Access        │                │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Frontend Layer

### Technology Stack
- **Framework**: React 18 with TypeScript
- **UI Library**: Office.js for Word integration
- **State Management**: React Hooks (useState, useEffect, useCallback)
- **Styling**: CSS Modules with responsive design
- **Build Tool**: Webpack with Office.js integration

### Key Components

#### 1. ChatInterface.tsx
- **Purpose**: Main chat interface for user interaction
- **Features**:
  - Real-time message exchange
  - Tool result formatting and display
  - Conversation history management
  - Response parsing and rendering
- **Key Methods**:
  - `sendMessage()`: Sends user input to backend
  - `formatToolResult()`: Formats tool execution results
  - `handleToolExecution()`: Manages tool execution flow

#### 2. DocumentViewer.tsx
- **Purpose**: Displays Word document content and analysis
- **Features**:
  - Document content rendering
  - Analysis results display
  - Interactive document navigation
- **Integration**: Office.js document access APIs

#### 3. ToolSelector.tsx
- **Purpose**: Provides interface for selecting and configuring MCP tools
- **Features**:
  - Tool availability display
  - Parameter configuration
  - Execution status monitoring

### Frontend-Backend Communication

#### API Endpoints
```typescript
// Intent Detection
POST /api/v1/mcp/agent/intent
{
  "message": "user input",
  "conversation_history": [],
  "document_content": "",
  "available_tools": []
}

// Tool Execution
POST /api/v1/mcp/tools/execute
{
  "tool_name": "tool_name",
  "parameters": {},
  "session_id": "session_id"
}

// Chat Interface
POST /api/v1/mcp/chat
{
  "message": "user message",
  "session_id": "session_id"
}
```

#### Data Flow
1. **User Input**: User types message in chat interface
2. **Intent Detection**: Frontend calls `/agent/intent` to determine routing
3. **Tool Selection**: Based on intent, appropriate tool is selected
4. **Tool Execution**: Frontend calls `/tools/execute` with tool parameters
5. **Result Display**: Tool results are formatted and displayed to user

## Backend Layer

### Technology Stack
- **Framework**: FastAPI (Python 3.9+)
- **Server**: Uvicorn with ASGI
- **API Protocol**: MCP (Model Context Protocol) over HTTP
- **Authentication**: JWT-based security
- **Logging**: Structured logging with structlog

### Core Architecture

#### 1. FastAPI Application (`main.py`)
- **Entry Point**: Application initialization and configuration
- **Middleware Stack**: CORS, security, logging, rate limiting
- **API Router Registration**: Mounts all API endpoints
- **Startup/Shutdown Events**: Resource management

#### 2. API Gateway (`mcp.py`)
- **MCP Protocol Implementation**: JSON-RPC 2.0 over HTTP
- **Tool Registry**: Manages available MCP tools
- **Request Routing**: Routes requests to appropriate services
- **Response Formatting**: Standardizes API responses

#### 3. Service Layer

##### Agent Service (`agent.py`)
- **Purpose**: Intelligent intent detection and routing
- **Features**:
  - LLM-powered intent analysis
  - Context-aware routing decisions
  - Conversation history integration
- **Key Methods**:
  - `detect_intent_and_route()`: Main intent detection logic
  - `_llm_intent_detection()`: LLM-based intent analysis
  - `_fallback_intent_detection()`: Fallback routing logic

##### LLM Client (`llm_client.py`)
- **Purpose**: Azure OpenAI integration
- **Features**:
  - GPT-4 model access
  - Text generation and analysis
  - Error handling and retry logic
- **Key Methods**:
  - `generate_text()`: Text generation
  - `summarize_text()`: Text summarization
  - `analyze_sentiment()`: Sentiment analysis

##### Tool Execution Service (`tool_execution_service.py`)
- **Purpose**: Centralized tool execution management
- **Features**:
  - Parameter validation
  - Tool lifecycle management
  - Error handling and logging
- **Key Methods**:
  - `execute_text_processor()`: Text processing tool execution
  - `execute_web_content_fetcher()`: Web content fetching
  - `execute_document_analyzer()`: Document analysis

##### Validation Service (`validation_service.py`)
- **Purpose**: Input parameter validation and sanitization
- **Features**:
  - Parameter type checking
  - Value range validation
  - Security validation
- **Supported Tools**: All MCP tools with specific validation rules

#### 4. Tool Layer

##### Text Processor (`text_processor.py`)
- **Purpose**: AI-powered text processing
- **Operations**: summarize, translate, analyze, improve, extract_keywords, sentiment_analysis, draft
- **Integration**: Azure OpenAI for AI operations

##### Web Content Fetcher (`web_content_fetcher.py`)
- **Purpose**: Web content retrieval and processing
- **Features**: Google Search API, content extraction, AI summarization
- **Capabilities**: Search queries, URL fetching, content processing

##### Document Analyzer (`document_analyzer.py`)
- **Purpose**: Document content analysis
- **Analysis Types**: readability, structure, keyword extraction, summary
- **Integration**: LLM-powered insights

##### File Reader (`file_reader.py`)
- **Purpose**: Local file system access
- **Features**: File reading, encoding support, size limits
- **Security**: Path validation and access control

##### Data Formatter (`data_formatter.py`)
- **Purpose**: Data structure and format conversion
- **Formats**: JSON, CSV, XML, YAML, Markdown, tables
- **Integration**: LLM-powered formatting

## Middleware Layer

### Security Middleware (`security.py`)
- **JWT Authentication**: Token-based user authentication
- **Rate Limiting**: Request throttling and abuse prevention
- **CORS Management**: Cross-origin request handling
- **Input Validation**: Request sanitization and validation

### Logging Middleware (`logging.py`)
- **Structured Logging**: JSON-formatted log entries
- **Request Tracking**: Request ID generation and correlation
- **Performance Monitoring**: Execution time tracking
- **Error Logging**: Comprehensive error capture and reporting

### CORS Middleware
- **Origin Control**: Allowed origin configuration
- **Method Control**: HTTP method restrictions
- **Header Control**: Custom header handling
- **Credential Support**: Authentication header support

## Data Flow and Interactions

### 1. User Request Flow
```
User Input → Frontend → Intent Detection → Tool Selection → Tool Execution → Result Display
```

### 2. Intent Detection Flow
```
User Message → Agent Service → LLM Analysis → Intent Classification → Routing Decision
```

### 3. Tool Execution Flow
```
Tool Request → Validation → Tool Execution → Result Processing → Response Formatting
```

### 4. Error Handling Flow
```
Error Occurrence → Error Capture → Logging → User Notification → Fallback Response
```

## Configuration Management

### Environment Variables
```bash
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment

# Google Search API
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_custom_search_engine_id

# Server Configuration
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=9000
SECRET_KEY=your_secret_key
```

### Configuration Classes
- **BaseSettings**: Pydantic-based configuration management
- **Environment File**: `.env` file support
- **Validation**: Configuration value validation
- **Defaults**: Sensible default values

## Security Features

### Authentication & Authorization
- **JWT Tokens**: Secure user authentication
- **Role-Based Access**: User permission management
- **Session Management**: Secure session handling

### Input Validation
- **Parameter Sanitization**: Input cleaning and validation
- **Type Checking**: Strict parameter type validation
- **Size Limits**: Request and content size restrictions

### Rate Limiting
- **Request Throttling**: Per-user request limits
- **Abuse Prevention**: DDoS protection
- **Resource Protection**: Server resource management

## Performance Considerations

### Caching Strategy
- **LLM Response Caching**: Cache frequent AI responses
- **Tool Result Caching**: Cache tool execution results
- **Session Caching**: User session data caching

### Async Processing
- **Non-blocking Operations**: Async/await pattern usage
- **Concurrent Requests**: Multiple request handling
- **Resource Management**: Efficient resource utilization

### Monitoring & Metrics
- **Performance Tracking**: Response time monitoring
- **Error Rate Monitoring**: Error frequency tracking
- **Resource Usage**: Memory and CPU monitoring

## Deployment Architecture

### Development Environment
- **Local Development**: Uvicorn with auto-reload
- **Virtual Environment**: Python venv isolation
- **Hot Reloading**: File change detection

### Production Considerations
- **Load Balancing**: Multiple server instances
- **Database Integration**: Persistent data storage
- **Monitoring**: Application performance monitoring
- **Scaling**: Horizontal and vertical scaling strategies

## Integration Points

### Office.js Integration
- **Document Access**: Word document content reading
- **UI Integration**: Office ribbon and task pane
- **Event Handling**: Document change events

### External API Integration
- **Azure OpenAI**: GPT-4 model access
- **Google Search**: Web content retrieval
- **File System**: Local file access

### MCP Protocol
- **Standard Compliance**: MCP specification adherence
- **Tool Registration**: Dynamic tool discovery
- **Protocol Versioning**: MCP version management

## Future Enhancements

### Planned Features
- **Multi-language Support**: Internationalization
- **Advanced Analytics**: Usage analytics and insights
- **Plugin System**: Extensible tool architecture
- **Cloud Integration**: Multi-cloud deployment support

### Scalability Improvements
- **Microservices**: Service decomposition
- **Message Queues**: Asynchronous processing
- **Distributed Caching**: Redis integration
- **Container Orchestration**: Kubernetes deployment
