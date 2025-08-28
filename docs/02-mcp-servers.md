# MCP Server and Tool Documentation

## Overview

The Word Add-in MCP system implements the Model Context Protocol (MCP) specification, providing a standardized interface for tool discovery, execution, and management. This document describes each MCP server and tool in detail.

## MCP Protocol Implementation

### Protocol Version
- **MCP Version**: 2024-11-05
- **Transport**: HTTP/HTTPS over JSON-RPC 2.0
- **Encoding**: UTF-8 JSON
- **Authentication**: JWT-based token authentication

### Core MCP Methods

#### 1. `tools/list`
- **Purpose**: Discover available tools and their capabilities
- **Request Format**: JSON-RPC 2.0 with method "tools/list"
- **Response**: List of tool definitions with schemas
- **Usage**: Called by clients to discover available functionality

#### 2. `tools/call`
- **Purpose**: Execute a specific tool with parameters
- **Request Format**: JSON-RPC 2.0 with method "tools/call"
- **Response**: Tool execution results or error information
- **Usage**: Called by clients to perform specific operations

#### 3. `tools/get`
- **Purpose**: Retrieve detailed information about a specific tool
- **Request Format**: JSON-RPC 2.0 with method "tools/get"
- **Response**: Detailed tool definition and metadata
- **Usage**: Called by clients to get tool-specific information

## MCP Tools Overview

### Tool Categories

#### 1. Text Processing Tools
- **Text Processor**: AI-powered text analysis and manipulation
- **Document Analyzer**: Document content analysis and insights

#### 2. Content Retrieval Tools
- **Web Content Fetcher**: Web search and content retrieval
- **File Reader**: Local file system access and reading

#### 3. Data Management Tools
- **Data Formatter**: Data structure and format conversion

## Detailed Tool Documentation

### 1. Text Processor Tool

#### Tool Definition
```json
{
  "name": "text_processor",
  "description": "Process text using various operations including summarization, translation, and analysis",
  "version": "1.0.0",
  "author": "Word Add-in MCP Project",
  "tags": ["text", "ai", "openai", "processing", "nlp"],
  "category": "text_processing"
}
```

#### Input Schema
```json
{
  "type": "object",
  "properties": {
    "text": {
      "type": "string",
      "description": "Text to process",
      "minLength": 1,
      "maxLength": 10000
    },
    "operation": {
      "type": "string",
      "description": "Processing operation to perform",
      "enum": [
        "summarize",
        "translate", 
        "analyze",
        "improve",
        "extract_keywords",
        "sentiment_analysis",
        "draft"
      ],
      "default": "summarize"
    },
    "language": {
      "type": "string",
      "description": "Target language for translation (ISO 639-1 code)",
      "pattern": "^[a-z]{2}$",
      "default": "en"
    },
    "max_length": {
      "type": "integer",
      "description": "Maximum length of output (for summarization)",
      "minimum": 10,
      "maximum": 1000,
      "default": 200
    },
    "style": {
      "type": "string",
      "description": "Writing style for improvement",
      "enum": ["formal", "casual", "academic", "creative", "technical"],
      "default": "formal"
    }
  },
  "required": ["text", "operation"]
}
```

#### Supported Operations

##### 1. Summarize
- **Purpose**: Create concise summaries of text content
- **AI Integration**: Uses Azure OpenAI GPT-4 for intelligent summarization
- **Parameters**: `max_length` controls output length
- **Use Cases**: Document summarization, content condensation, key point extraction

##### 2. Translate
- **Purpose**: Translate text between different languages
- **AI Integration**: Azure OpenAI GPT-4 for high-quality translation
- **Parameters**: `language` specifies target language (ISO 639-1 format)
- **Use Cases**: Multilingual document processing, content localization

##### 3. Analyze
- **Purpose**: Comprehensive text analysis and insights
- **AI Integration**: Multi-faceted analysis using GPT-4
- **Output**: Structure, tone, complexity, and content insights
- **Use Cases**: Document analysis, content quality assessment

##### 4. Improve
- **Purpose**: Enhance text quality and readability
- **AI Integration**: Style-aware text improvement using GPT-4
- **Parameters**: `style` controls improvement approach
- **Use Cases**: Writing enhancement, content refinement, style adjustment

##### 5. Extract Keywords
- **Purpose**: Identify key terms and concepts in text
- **AI Integration**: Intelligent keyword extraction using GPT-4
- **Parameters**: `max_keywords` controls number of extracted terms
- **Use Cases**: Content indexing, topic identification, search optimization

##### 6. Sentiment Analysis
- **Purpose**: Analyze emotional tone and sentiment of text
- **AI Integration**: Advanced sentiment analysis using GPT-4
- **Output**: Sentiment score and emotional classification
- **Use Cases**: Content tone analysis, audience response assessment

##### 7. Draft
- **Purpose**: Generate new content based on user requests
- **AI Integration**: Creative content generation using GPT-4
- **Use Cases**: Patent claim drafting, content creation, document generation

#### Output Schema
```json
{
  "type": "object",
  "properties": {
    "processed_text": {"type": "string"},
    "operation": {"type": "string"},
    "original_length": {"type": "integer"},
    "processed_length": {"type": "integer"},
    "processing_time": {"type": "number"},
    "confidence_score": {"type": "number"},
    "metadata": {"type": "object"}
  }
}
```

#### Example Usage
```bash
curl -X POST "http://localhost:9000/api/v1/mcp/tools/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "text_processor",
    "parameters": {
      "text": "Long text content here...",
      "operation": "summarize",
      "max_length": 100
    },
    "session_id": "test-123"
  }'
```

### 2. Web Content Fetcher Tool

#### Tool Definition
```json
{
  "name": "web_content_fetcher",
  "description": "Fetch and process web content",
  "version": "1.0.0",
  "author": "Word Add-in MCP Project",
  "tags": ["web", "content", "search", "fetching"],
  "category": "content_retrieval"
}
```

#### Input Schema
```json
{
  "type": "object",
  "properties": {
    "url": {
      "type": "string",
      "description": "URL to fetch content from",
      "format": "uri"
    },
    "extract_text": {
      "type": "boolean",
      "description": "Whether to extract text content",
      "default": true
    },
    "max_size": {
      "type": "integer",
      "description": "Maximum content size to fetch",
      "minimum": 1,
      "maximum": 10485760,
      "default": 1048576
    }
  },
  "required": ["url"]
}
```

#### Features

##### 1. Google Search Integration
- **API**: Google Custom Search Engine API
- **Capabilities**: Web search, result ranking, content discovery
- **Configuration**: Requires `GOOGLE_API_KEY` and `GOOGLE_CSE_ID`

##### 2. Content Extraction
- **HTML Processing**: Intelligent HTML parsing and text extraction
- **Content Cleaning**: Removal of ads, navigation, and irrelevant content
- **Encoding Support**: Multiple character encoding handling

##### 3. AI Enhancement
- **Content Summarization**: LLM-powered content summarization
- **Key Point Extraction**: Important information identification
- **Content Analysis**: Structure and relevance assessment

#### Output Schema
```json
{
  "type": "object",
  "properties": {
    "url": {"type": "string"},
    "query": {"type": "string"},
    "content": {"type": "string"},
    "content_type": {"type": "string"},
    "extraction_time": {"type": "number"},
    "ai_enhanced": {"type": "boolean"},
    "source_type": {"type": "string"}
  }
}
```

#### Example Usage
```bash
curl -X POST "http://localhost:9000/api/v1/mcp/tools/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "web_content_fetcher",
    "parameters": {
      "query": "Ramy Atawia",
      "extract_type": "summary",
      "max_length": 500
    },
    "session_id": "test-123"
  }'
```

### 3. Document Analyzer Tool

#### Tool Definition
```json
{
  "name": "document_analyzer",
  "description": "Analyze document content for insights",
  "version": "1.0.0",
  "author": "Word Add-in MCP Project",
  "tags": ["document", "analysis", "insights", "ai"],
  "category": "document_processing"
}
```

#### Input Schema
```json
{
  "type": "object",
  "properties": {
    "content": {
      "type": "string",
      "description": "Document content to analyze",
      "minLength": 1
    },
    "analysis_type": {
      "type": "string",
      "description": "Type of analysis",
      "enum": [
        "readability",
        "structure",
        "tone",
        "summary",
        "keyword_extraction"
      ]
    }
  },
  "required": ["content", "analysis_type"]
}
```

#### Analysis Types

##### 1. Readability Analysis
- **Purpose**: Assess document readability and complexity
- **Metrics**: Flesch-Kincaid scores, sentence complexity, vocabulary level
- **Use Cases**: Content accessibility, audience targeting, writing improvement

##### 2. Structure Analysis
- **Purpose**: Analyze document organization and flow
- **Features**: Section identification, logical flow, content hierarchy
- **Use Cases**: Document organization, content planning, structure optimization

##### 3. Tone Analysis
- **Purpose**: Identify document emotional tone and style
- **Features**: Formality level, emotional content, audience appropriateness
- **Use Cases**: Brand voice consistency, audience engagement, content strategy

##### 4. Summary Generation
- **Purpose**: Create comprehensive document summaries
- **AI Integration**: GPT-4 powered intelligent summarization
- **Features**: Key point extraction, main idea identification, content condensation

##### 5. Keyword Extraction
- **Purpose**: Identify important terms and concepts
- **AI Integration**: Intelligent keyword identification using GPT-4
- **Features**: Relevance scoring, concept clustering, topic identification

#### Output Schema
```json
{
  "type": "object",
  "properties": {
    "analysis": {"type": "string"},
    "analysis_type": {"type": "string"},
    "metrics": {"type": "object"},
    "confidence_score": {"type": "number"},
    "processing_time": {"type": "number"}
  }
}
```

### 4. File Reader Tool

#### Tool Definition
```json
{
  "name": "file_reader",
  "description": "Read file contents from the local filesystem",
  "version": "1.0.0",
  "author": "Word Add-in MCP Project",
  "tags": ["file", "reading", "filesystem", "access"],
  "category": "file_operations"
}
```

#### Input Schema
```json
{
  "type": "object",
  "properties": {
    "path": {
      "type": "string",
      "description": "File path to read",
      "minLength": 1,
      "maxLength": 500
    },
    "encoding": {
      "type": "string",
      "description": "File encoding",
      "enum": ["utf-8", "ascii", "latin-1", "utf-16"],
      "default": "utf-8"
    },
    "max_size": {
      "type": "integer",
      "description": "Maximum file size to read in bytes",
      "minimum": 1,
      "maximum": 10485760,
      "default": 1048576
    }
  },
  "required": ["path"]
}
```

#### Features

##### 1. File Access
- **Path Validation**: Secure path validation and sanitization
- **Size Limits**: Configurable file size restrictions
- **Encoding Support**: Multiple character encoding handling

##### 2. Security
- **Path Sanitization**: Prevents directory traversal attacks
- **Access Control**: File permission validation
- **Size Restrictions**: Prevents memory exhaustion attacks

##### 3. Error Handling
- **File Not Found**: Graceful handling of missing files
- **Permission Errors**: Clear error messages for access issues
- **Encoding Errors**: Fallback encoding strategies

#### Output Schema
```json
{
  "type": "object",
  "properties": {
    "file_path": {"type": "string"},
    "content": {"type": "string"},
    "encoding": {"type": "string"},
    "file_size": {"type": "integer"},
    "read_time": {"type": "number"}
  }
}
```

### 5. Data Formatter Tool

#### Tool Definition
```json
{
  "name": "data_formatter",
  "description": "Format and structure data for document presentation",
  "version": "1.0.0",
  "author": "Word Add-in MCP Project",
  "tags": ["data", "formatting", "conversion", "presentation"],
  "category": "data_management"
}
```

#### Input Schema
```json
{
  "type": "object",
  "properties": {
    "data": {
      "type": "string",
      "description": "Data to format",
      "minLength": 1
    },
    "format": {
      "type": "string",
      "description": "Output format",
      "enum": [
        "table",
        "list",
        "summary",
        "json",
        "csv",
        "markdown"
      ]
    }
  },
  "required": ["data", "format"]
}
```

#### Supported Formats

##### 1. Table Format
- **Purpose**: Convert data to structured table format
- **Features**: Column alignment, header formatting, data organization
- **Use Cases**: Report generation, data presentation, document formatting

##### 2. List Format
- **Purpose**: Convert data to bulleted or numbered lists
- **Features**: Hierarchical organization, indentation, list styling
- **Use Cases**: Content organization, key point presentation, summary creation

##### 3. Summary Format
- **Purpose**: Create concise data summaries
- **AI Integration**: GPT-4 powered intelligent summarization
- **Features**: Key point extraction, main idea identification, content condensation

##### 4. JSON Format
- **Purpose**: Structure data in JSON format
- **Features**: Schema validation, nested structure support, data integrity
- **Use Cases**: API responses, data exchange, configuration files

##### 5. CSV Format
- **Purpose**: Convert data to CSV format
- **Features**: Column separation, header row, data export
- **Use Cases**: Data analysis, spreadsheet integration, data migration

##### 6. Markdown Format
- **Purpose**: Convert data to Markdown format
- **Features**: Rich text formatting, link support, code blocks
- **Use Cases**: Documentation, content creation, web publishing

#### Output Schema
```json
{
  "type": "object",
  "properties": {
    "formatted_data": {"type": "string"},
    "format": {"type": "string"},
    "original_length": {"type": "integer"},
    "formatted_length": {"type": "integer"},
    "processing_time": {"type": "number"}
  }
}
```

## Tool Execution Flow

### 1. Tool Discovery
```
Client → tools/list → Tool Registry → Available Tools List
```

### 2. Tool Execution
```
Client → tools/call → Parameter Validation → Tool Execution → Result Processing → Response
```

### 3. Error Handling
```
Error Occurrence → Error Classification → Error Response → Client Notification
```

## Tool Registry Management

### Dynamic Tool Registration
- **Tool Discovery**: Automatic tool detection and registration
- **Schema Validation**: Input/output schema validation
- **Version Management**: Tool version tracking and compatibility

### Tool Lifecycle
- **Initialization**: Tool setup and configuration
- **Execution**: Parameter validation and processing
- **Cleanup**: Resource cleanup and memory management

## Performance Characteristics

### Execution Times
- **Text Processing**: 0.1-2.0 seconds (AI operations)
- **Web Content Fetching**: 2.0-10.0 seconds (network operations)
- **Document Analysis**: 0.5-3.0 seconds (AI analysis)
- **File Reading**: 0.01-0.1 seconds (local operations)
- **Data Formatting**: 0.01-0.5 seconds (format conversion)

### Resource Usage
- **Memory**: 50-200 MB per tool execution
- **CPU**: 10-30% during AI operations
- **Network**: 1-10 MB per web content fetch
- **Storage**: Minimal local storage usage

## Security Considerations

### Input Validation
- **Parameter Sanitization**: All input parameters are validated and sanitized
- **Type Checking**: Strict parameter type validation
- **Size Limits**: Configurable size restrictions for all inputs

### Access Control
- **Authentication**: JWT-based user authentication
- **Authorization**: Role-based access control
- **Session Management**: Secure session handling and validation

### Data Protection
- **Content Encryption**: Sensitive data encryption in transit
- **Access Logging**: Comprehensive access and operation logging
- **Audit Trail**: Complete audit trail for all operations

## Error Handling

### Error Types
- **Validation Errors**: Parameter validation failures
- **Execution Errors**: Tool execution failures
- **Configuration Errors**: Missing or invalid configuration
- **Network Errors**: External service communication failures

### Error Responses
```json
{
  "status": "error",
  "error_message": "Detailed error description",
  "error_type": "error_category",
  "error_details": {
    "additional_info": "context_specific_details"
  }
}
```

### Fallback Strategies
- **Graceful Degradation**: Fallback to simpler operations
- **Error Recovery**: Automatic retry with different parameters
- **User Notification**: Clear error messages and suggestions

## Monitoring and Observability

### Metrics Collection
- **Execution Times**: Performance monitoring for all tools
- **Success Rates**: Success/failure rate tracking
- **Resource Usage**: Memory, CPU, and network usage monitoring
- **Error Rates**: Error frequency and type tracking

### Logging
- **Structured Logging**: JSON-formatted log entries
- **Request Tracking**: Request ID correlation across services
- **Performance Logging**: Detailed performance metrics
- **Error Logging**: Comprehensive error capture and context

### Health Checks
- **Tool Health**: Individual tool availability monitoring
- **Service Health**: Overall service health assessment
- **Dependency Health**: External service availability monitoring
- **Performance Health**: Response time and throughput monitoring
