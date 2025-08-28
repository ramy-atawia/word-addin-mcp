# Phase 1 API Requirements - Word Add-in MCP Project (MCP-Compliant)

## Overview
MCP-compliant API requirements for Phase 1 (POC) focusing on core functionality with single MCP tool integration, real LLM input/output, and basic Word Add-in capabilities.

## MCP Protocol Compliance

### MCP Protocol Version
- **Supported Version**: MCP v1.0 (2024-11-05)
- **Protocol Base**: JSON-RPC 2.0
- **Required Capabilities**: `tools.listChanged: true`

### MCP Initialization Sequence
All MCP operations require proper initialization:
1. **Initialize handshake** with protocol version negotiation
2. **Capability negotiation** to validate server support
3. **Tool discovery** after successful initialization
4. **Tool execution** using MCP protocol format

## API Endpoints

### 1. Chat API

#### 1.1 Send Message
```
POST /api/v1/chat/send
```

**Request Body:**
```json
{
  "message": "string",
  "session_id": "string",
  "document_context": {
    "document_id": "string",
    "selection_text": "string",
    "cursor_position": {
      "paragraph": "number",
      "character": "number"
    }
  },
  "mcp_tool_request": {
    "tool_name": "string",
    "parameters": "object",
    "protocol_version": "2024-11-05"
  }
}
```

**Response:**
```json
{
  "response_id": "string",
  "message": "string",
  "llm_response": "string",
  "tool_execution": {
    "tool_name": "string",
    "status": "success|error",
    "result": "object",
    "execution_time": "number",
    "mcp_protocol_version": "2024-11-05"
  },
  "session_id": "string",
  "timestamp": "ISO 8601 string"
}
```

#### 1.2 Get Chat History
```
GET /api/v1/chat/history/{session_id}
```

**Response:**
```json
{
  "session_id": "string",
  "messages": [
    {
      "message_id": "string",
      "user_message": "string",
      "llm_response": "string",
      "tool_execution": "object",
      "timestamp": "ISO 8601 string"
    }
  ]
}
```

#### 1.3 Stream Chat Response
```
GET /api/v1/chat/stream/{response_id}
```

**Response:** Server-Sent Events (SSE) stream
```
data: {"chunk": "partial response", "is_complete": false}
data: {"chunk": "final chunk", "is_complete": true}
```

### 2. MCP Tools API

#### 2.1 List Available Tools (MCP-Compliant)
```
GET /api/v1/mcp/tools
```

**Response:**
```json
{
  "tools": [
    {
      "name": "string",
      "description": "string",
      "inputSchema": {
        "type": "object",
        "properties": {
          "param1": {
            "type": "string",
            "description": "Parameter description"
          }
        },
        "required": ["param1"]
      },
      "server_info": {
        "name": "string",
        "version": "string"
      }
    }
  ],
  "protocol_version": "2024-11-05",
  "server_capabilities": {
    "tools": {
      "listChanged": true
    }
  },
  "connection_status": "connected|disconnected"
}
```

#### 2.2 Execute MCP Tool (MCP-Compliant)
```
POST /api/v1/mcp/tools/execute
```

**Request Body:**
```json
{
  "tool_name": "string",
  "parameters": "object",
  "session_id": "string"
}
```

**Response:**
```json
{
  "execution_id": "string",
  "status": "running|completed|error",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Tool execution result"
      }
    ]
  },
  "error": {
    "code": -32603,
    "message": "Internal error",
    "data": {
      "details": "Tool execution failed"
    }
  },
  "execution_time": "number",
  "mcp_protocol_version": "2024-11-05"
}
```

#### 2.3 Get Tool Execution Status
```
GET /api/v1/mcp/tools/status/{execution_id}
```

**Response:**
```json
{
  "execution_id": "string",
  "status": "running|completed|error",
  "result": "object",
  "error": "object",
  "execution_time": "number",
  "mcp_protocol_version": "2024-11-05"
}
```

#### 2.4 MCP Connection Status
```
GET /api/v1/mcp/status
```

**Response:**
```json
{
  "connection_status": "connected|disconnected|initializing",
  "protocol_version": "2024-11-05",
  "server_capabilities": {
    "tools": {
      "listChanged": true
    }
  },
  "last_heartbeat": "ISO 8601 string",
  "server_info": {
    "name": "string",
    "version": "string"
  }
}
```

### 3. Document Operations API

#### 3.1 Get Document Context
```
GET /api/v1/document/context/{document_id}
```

**Response:**
```json
{
  "document_id": "string",
  "title": "string",
  "current_selection": "string",
  "cursor_position": "object",
  "document_stats": {
    "word_count": "number",
    "paragraph_count": "number"
  }
}
```

#### 3.2 Apply Document Changes
```
POST /api/v1/document/apply-changes
```

**Request Body:**
```json
{
  "document_id": "string",
  "changes": [
    {
      "type": "insert|replace|delete",
      "position": "object",
      "content": "string"
    }
  ],
  "session_id": "string"
}
```

### 4. Session Management API

#### 4.1 Create Session (MCP-Compliant)
```
POST /api/v1/session/create
```

**Request Body:**
```json
{
  "user_id": "string",
  "document_id": "string",
  "mcp_server_config": {
    "server_url": "string",
    "auth_token": "string",
    "protocol_version": "2024-11-05"
  }
}
```

**Response:**
```json
{
  "session_id": "string",
  "status": "active",
  "created_at": "ISO 8601 string",
  "mcp_server_status": "connected|disconnected",
  "mcp_protocol_version": "2024-11-05",
  "mcp_capabilities": {
    "tools": {
      "listChanged": true
    }
  },
  "server_info": {
    "name": "string",
    "version": "string"
  }
}
```

#### 4.2 Get Session Status
```
GET /api/v1/session/{session_id}/status
```

**Response:**
```json
{
  "session_id": "string",
  "status": "active|inactive|ended",
  "mcp_server_status": "connected|disconnected|initializing",
  "mcp_protocol_version": "2024-11-05",
  "mcp_capabilities": "object",
  "last_activity": "ISO 8601 string"
}
```

#### 4.3 End Session
```
DELETE /api/v1/session/{session_id}
```

**Response:**
```json
{
  "session_id": "string",
  "status": "ended",
  "ended_at": "ISO 8601 string",
  "mcp_connection_closed": true
}
```

### 5. Health Check API

#### 5.1 Service Health
```
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "services": {
    "langchain_agent": "healthy",
    "mcp_client": "healthy",
    "azure_openai": "healthy"
  },
  "mcp_protocol_version": "2024-11-05",
  "timestamp": "ISO 8601 string"
}
```

#### 5.2 MCP Server Health
```
GET /api/v1/health/mcp
```

**Response:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "connection_status": "connected|disconnected",
  "protocol_version": "2024-11-05",
  "server_capabilities": "object",
  "last_heartbeat": "ISO 8601 string",
  "response_time": "number"
}
```

## Data Models

### Chat Message
```typescript
interface ChatMessage {
  message_id: string;
  session_id: string;
  user_message: string;
  llm_response: string;
  tool_execution?: ToolExecution;
  timestamp: string;
  document_context?: DocumentContext;
}
```

### Tool Execution (MCP-Compliant)
```typescript
interface ToolExecution {
  tool_name: string;
  parameters: object;
  status: 'pending' | 'running' | 'completed' | 'error';
  result?: MCPToolResult;
  error?: MCPError;
  execution_time?: number;
  timestamp: string;
  mcp_protocol_version: string;
}

interface MCPToolResult {
  content: Array<{
    type: 'text' | 'image' | 'code';
    text?: string;
    image_url?: string;
    code?: string;
    language?: string;
  }>;
}

interface MCPError {
  code: number;  // MCP standard error codes
  message: string;
  data?: object;
}
```

### Document Context
```typescript
interface DocumentContext {
  document_id: string;
  selection_text?: string;
  cursor_position?: {
    paragraph: number;
    character: number;
  };
  document_stats?: {
    word_count: number;
    paragraph_count: number;
  };
}
```

### Session (MCP-Compliant)
```typescript
interface Session {
  session_id: string;
  user_id: string;
  document_id: string;
  mcp_server_config: MCPServerConfig;
  status: 'active' | 'inactive' | 'ended';
  created_at: string;
  last_activity: string;
  mcp_protocol_version: string;
  mcp_capabilities: object;
  server_info: MCPServerInfo;
}

interface MCPServerConfig {
  server_url: string;
  auth_token: string;
  protocol_version: string;
  connection_timeout: number;
  max_retries: number;
}

interface MCPServerInfo {
  name: string;
  version: string;
}
```

### MCP Protocol Models
```typescript
interface MCPInitializeRequest {
  jsonrpc: "2.0";
  id: string;
  method: "initialize";
  params: {
    protocolVersion: string;
    capabilities: {
      tools: object;
    };
    clientInfo: {
      name: string;
      version: string;
    };
  };
}

interface MCPToolCallRequest {
  jsonrpc: "2.0";
  id: string;
  method: "tools/call";
  params: {
    name: string;
    arguments: object;
  };
}

interface MCPToolListRequest {
  jsonrpc: "2.0";
  id: string;
  method: "tools/list";
}
```

## Error Handling (MCP-Compliant)

### Error Response Format
```json
{
  "error": {
    "code": -32603,
    "message": "Internal error",
    "data": {
      "details": "Detailed error information",
      "mcp_protocol": true,
      "mcp_error_code": -32603
    },
    "timestamp": "ISO 8601 string"
  }
}
```

### MCP Standard Error Codes
- `-32700`: Parse error - Invalid JSON received
- `-32600`: Invalid request - JSON-RPC request is invalid
- `-32601`: Method not found - Method does not exist
- `-32602`: Invalid params - Invalid method parameters
- `-32603`: Internal error - Internal JSON-RPC error
- `-32000` to `-32099`: Server error - Reserved for server errors

### Custom Error Codes (MCP-Enhanced)
- `MCP_CONNECTION_ERROR`: MCP server connection failed
- `MCP_INITIALIZATION_ERROR`: MCP protocol initialization failed
- `MCP_CAPABILITY_ERROR`: MCP server capability mismatch
- `MCP_PROTOCOL_ERROR`: MCP protocol violation
- `TOOL_EXECUTION_ERROR`: Tool execution failed
- `LLM_ERROR`: Azure OpenAI API error
- `SESSION_EXPIRED`: Session has expired
- `INVALID_REQUEST`: Invalid request parameters
- `INTERNAL_ERROR`: Internal server error

## Rate Limiting

### Limits
- Chat API: 10 requests per minute per session
- Tool Execution: 5 requests per minute per session
- Document Operations: 20 requests per minute per session
- MCP Operations: 15 requests per minute per session

### Headers
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1640995200
```

## Authentication & Security

### Session-based Authentication
- Session tokens required for all API calls
- Session expiration: 24 hours of inactivity
- Secure session storage with encryption
- MCP server authentication token validation

### CORS Configuration
```
Access-Control-Allow-Origin: [Word Add-in domain]
Access-Control-Allow-Methods: GET, POST, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
```

### MCP Security
- TLS encryption for MCP connections
- Token-based MCP server authentication
- Connection validation and health monitoring
- Secure capability negotiation

## Streaming Support

### Server-Sent Events (SSE)
- Real-time chat response streaming
- Tool execution progress updates
- MCP connection status updates
- Connection keep-alive with heartbeat

### WebSocket (Future Enhancement)
- Real-time bidirectional communication
- Document change notifications
- MCP server status updates
- Tool execution progress streaming

## Performance Requirements

### Response Times
- Chat API: < 2 seconds for 95% of requests
- Tool Execution: < 5 seconds for 95% of requests
- Document Operations: < 1 second for 95% of requests
- MCP Operations: < 3 seconds for 95% of requests

### Throughput
- Support up to 100 concurrent sessions
- Handle up to 1000 requests per minute
- MCP tool execution timeout: 30 seconds
- MCP connection timeout: 10 seconds

## Monitoring & Logging

### Metrics
- Request count and response times
- Error rates by endpoint
- MCP tool execution success rates
- Session creation and duration
- MCP protocol compliance metrics

### Logging
- Structured JSON logging
- Request/response logging for debugging
- Error logging with stack traces
- Performance metrics logging
- MCP protocol message logging

### MCP-Specific Monitoring
- MCP connection health
- Protocol version compatibility
- Capability negotiation success rates
- Tool discovery performance
- MCP error code distribution
