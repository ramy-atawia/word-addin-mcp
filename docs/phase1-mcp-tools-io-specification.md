# Phase 1 MCP Tools Input/Output Specification - Word Add-in MCP Project

## Overview
Detailed specification of input and output formats for all Phase 1 MCP tools, including JSON schemas, examples, error handling, and data transformations.

## MCP Protocol Message Format

### Base MCP Message Structure
All tool calls follow the MCP v1.0 protocol using JSON-RPC 2.0:

```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "method": "tools/call",
  "params": {
    "name": "tool_name",
    "arguments": {
      // Tool-specific parameters
    }
  }
}
```

### Base MCP Response Structure
```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Tool execution result"
      }
    ]
  }
}
```

## Tool 1: File Reader Tool

### Input Schema
```json
{
  "name": "file_reader",
  "description": "Read file contents from the local filesystem",
  "inputSchema": {
    "type": "object",
    "properties": {
      "path": {
        "type": "string",
        "description": "Absolute or relative file path to read",
        "examples": ["/path/to/file.txt", "./data/config.json", "C:\\Users\\user\\file.txt"],
        "minLength": 1,
        "maxLength": 500
      },
      "encoding": {
        "type": "string",
        "description": "File encoding (default: utf-8)",
        "enum": ["utf-8", "ascii", "latin-1", "utf-16"],
        "default": "utf-8"
      },
      "max_size": {
        "type": "integer",
        "description": "Maximum file size to read in bytes (default: 1048576 = 1MB)",
        "minimum": 1,
        "maximum": 10485760,
        "default": 1048576
      },
      "include_metadata": {
        "type": "boolean",
        "description": "Include file metadata in response (default: false)",
        "default": false
      }
    },
    "required": ["path"]
  }
}
```

### Input Examples

#### Basic File Read
```json
{
  "jsonrpc": "2.0",
  "id": "file-read-001",
  "method": "tools/call",
  "params": {
    "name": "file_reader",
    "arguments": {
      "path": "./config/settings.json"
    }
  }
}
```

#### File Read with Custom Encoding
```json
{
  "jsonrpc": "2.0",
  "id": "file-read-002",
  "method": "tools/call",
  "params": {
    "name": "file_reader",
    "arguments": {
      "path": "/data/legacy.txt",
      "encoding": "latin-1",
      "max_size": 2048
    }
  }
}
```

#### File Read with Metadata
```json
{
  "jsonrpc": "2.0",
  "id": "file-read-003",
  "method": "tools/call",
  "params": {
    "name": "file_reader",
    "arguments": {
      "path": "./reports/data.csv",
      "include_metadata": true
    }
  }
}
```

### Output Schema

#### Success Response
```json
{
  "jsonrpc": "2.0",
  "id": "file-read-001",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "File content successfully read"
      },
      {
        "type": "file_content",
        "file_path": "./config/settings.json",
        "content": "{\n  \"api_key\": \"abc123\",\n  \"timeout\": 30,\n  \"debug\": false\n}",
        "encoding": "utf-8",
        "size_bytes": 67,
        "last_modified": "2024-01-15T10:30:00Z",
        "metadata": {
          "file_type": "json",
          "is_valid_json": true,
          "line_count": 4
        }
      }
    ]
  }
}
```

#### Success Response with Metadata
```json
{
  "jsonrpc": "2.0",
  "id": "file-read-003",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "File content successfully read with metadata"
      },
      {
        "type": "file_content",
        "file_path": "./reports/data.csv",
        "content": "Name,Age,Department\nJohn,30,Engineering\nJane,25,Marketing",
        "encoding": "utf-8",
        "size_bytes": 89,
        "last_modified": "2024-01-15T14:45:00Z",
        "metadata": {
          "file_type": "csv",
          "is_valid_csv": true,
          "line_count": 3,
          "column_count": 3,
          "columns": ["Name", "Age", "Department"]
        }
      }
    ]
  }
}
```

#### Error Response - File Not Found
```json
{
  "jsonrpc": "2.0",
  "id": "file-read-001",
  "error": {
    "code": -32603,
    "message": "File not found",
    "data": {
      "error_type": "file_not_found",
      "file_path": "./config/settings.json",
      "suggestions": [
        "Check if the file path is correct",
        "Verify file exists in the specified location",
        "Ensure you have read permissions"
      ]
    }
  }
}
```

#### Error Response - Permission Denied
```json
{
  "jsonrpc": "2.0",
  "id": "file-read-002",
  "error": {
    "code": -32603,
    "message": "Permission denied",
    "data": {
      "error_type": "permission_denied",
      "file_path": "/system/config.txt",
      "suggestions": [
        "Check file permissions",
        "Verify user has read access",
        "Contact system administrator"
      ]
    }
  }
}
```

#### Error Response - File Too Large
```json
{
  "jsonrpc": "2.0",
  "id": "file-read-003",
  "error": {
    "code": -32603,
    "message": "File size exceeds limit",
    "data": {
      "error_type": "file_too_large",
      "file_path": "./large_data.txt",
      "file_size": 2097152,
      "max_size": 1048576,
      "suggestions": [
        "Use a smaller file",
        "Increase max_size parameter",
        "Process file in chunks"
      ]
    }
  }
}
```

## Tool 2: Text Processor Tool

### Input Schema
```json
{
  "name": "text_processor",
  "description": "Process and manipulate text content with various operations",
  "inputSchema": {
    "type": "object",
    "properties": {
      "text": {
        "type": "string",
        "description": "Text content to process",
        "minLength": 1,
        "maxLength": 10000
      },
      "operation": {
        "type": "string",
        "description": "Text processing operation to perform",
        "enum": [
          "summarize",
          "translate",
          "format",
          "analyze",
          "correct",
          "enhance"
        ]
      },
      "language": {
        "type": "string",
        "description": "Language for translation or analysis (ISO 639-1)",
        "examples": ["en", "es", "fr", "de", "zh", "ja"],
        "default": "en"
      },
      "style": {
        "type": "string",
        "description": "Style for formatting or enhancement",
        "enum": ["formal", "casual", "academic", "business", "creative"],
        "default": "formal"
      },
      "max_length": {
        "type": "integer",
        "description": "Maximum length of output (for summarize operation)",
        "minimum": 50,
        "maximum": 2000,
        "default": 500
      },
      "tone": {
        "type": "string",
        "description": "Tone for text enhancement",
        "enum": ["professional", "friendly", "authoritative", "conversational"],
        "default": "professional"
      }
    },
    "required": ["text", "operation"]
  }
}
```

### Input Examples

#### Text Summarization
```json
{
  "jsonrpc": "2.0",
  "id": "text-process-001",
  "method": "tools/call",
  "params": {
    "name": "text_processor",
    "arguments": {
      "text": "This is a very long document that contains many paragraphs of information about various topics including technology, business, and innovation. The document discusses the impact of artificial intelligence on modern business practices and how companies are adapting to these changes.",
      "operation": "summarize",
      "style": "business",
      "max_length": 200
    }
  }
}
```

#### Text Translation
```json
{
  "jsonrpc": "2.0",
  "id": "text-process-002",
  "method": "tools/call",
  "params": {
    "name": "text_processor",
    "arguments": {
      "text": "Hello, how are you today?",
      "operation": "translate",
      "language": "es",
      "style": "casual"
    }
  }
}
```

#### Text Enhancement
```json
{
  "jsonrpc": "2.0",
  "id": "text-process-003",
  "method": "tools/call",
  "params": {
    "name": "text_processor",
    "arguments": {
      "text": "The product is good. It works well.",
      "operation": "enhance",
      "style": "business",
      "tone": "professional"
    }
  }
}
```

### Output Schema

#### Success Response - Summarization
```json
{
  "jsonrpc": "2.0",
  "id": "text-process-001",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Text successfully summarized"
      },
      {
        "type": "processed_text",
        "original_text": "This is a very long document...",
        "processed_text": "The document discusses AI's impact on modern business practices and company adaptation strategies.",
        "operation": "summarize",
        "style": "business",
        "original_length": 245,
        "processed_length": 108,
        "compression_ratio": 0.56,
        "processing_time_ms": 1250
      }
    ]
  }
}
```

#### Success Response - Translation
```json
{
  "jsonrpc": "2.0",
  "id": "text-process-002",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Text successfully translated"
      },
      {
        "type": "processed_text",
        "original_text": "Hello, how are you today?",
        "processed_text": "Hola, ¿cómo estás hoy?",
        "operation": "translate",
        "source_language": "en",
        "target_language": "es",
        "style": "casual",
        "confidence_score": 0.95,
        "processing_time_ms": 890
      }
    ]
  }
}
```

#### Success Response - Enhancement
```json
{
  "jsonrpc": "2.0",
  "id": "text-process-003",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Text successfully enhanced"
      },
      {
        "type": "processed_text",
        "original_text": "The product is good. It works well.",
        "processed_text": "The product demonstrates excellent quality and functionality, delivering reliable performance that meets user expectations.",
        "operation": "enhance",
        "style": "business",
        "tone": "professional",
        "improvements": [
          "Enhanced vocabulary",
          "Improved sentence structure",
          "Added professional tone"
        ],
        "processing_time_ms": 650
      }
    ]
  }
}
```

#### Error Response - Invalid Operation
```json
{
  "jsonrpc": "2.0",
  "id": "text-process-004",
  "error": {
    "code": -32602,
    "message": "Invalid operation specified",
    "data": {
      "error_type": "invalid_operation",
      "provided_operation": "invalid_op",
      "valid_operations": ["summarize", "translate", "format", "analyze", "correct", "enhance"],
      "suggestions": [
        "Use one of the valid operation types",
        "Check operation spelling and case"
      ]
    }
  }
}
```

#### Error Response - Text Too Long
```json
{
  "jsonrpc": "2.0",
  "id": "text-process-005",
  "error": {
    "code": -32602,
    "message": "Text length exceeds maximum limit",
    "data": {
      "error_type": "text_too_long",
      "text_length": 15000,
      "max_length": 10000,
      "suggestions": [
        "Reduce text length to 10,000 characters or less",
        "Split text into smaller chunks",
        "Use summarize operation first"
      ]
    }
  }
}
```

## Tool 3: Document Analyzer Tool

### Input Schema
```json
{
  "name": "document_analyzer",
  "description": "Analyze Word document content for insights and improvements",
  "inputSchema": {
    "type": "object",
    "properties": {
      "content": {
        "type": "string",
        "description": "Document content to analyze",
        "minLength": 1,
        "maxLength": 50000
      },
      "analysis_type": {
        "type": "string",
        "description": "Type of analysis to perform",
        "enum": [
          "readability",
          "structure",
          "tone",
          "clarity",
          "completeness",
          "comprehensive"
        ]
      },
      "target_audience": {
        "type": "string",
        "description": "Target audience for the document",
        "enum": ["general", "academic", "business", "technical", "creative"],
        "default": "general"
      },
      "document_type": {
        "type": "string",
        "description": "Type of document being analyzed",
        "enum": ["report", "proposal", "email", "article", "manual", "other"],
        "default": "other"
      },
      "include_suggestions": {
        "type": "boolean",
        "description": "Include improvement suggestions in analysis",
        "default": true
      },
      "detailed_metrics": {
        "type": "boolean",
        "description": "Include detailed metrics and scores",
        "default": false
      }
    },
    "required": ["content", "analysis_type"]
  }
}
```

### Input Examples

#### Readability Analysis
```json
{
  "jsonrpc": "2.0",
  "id": "doc-analyze-001",
  "method": "tools/call",
  "params": {
    "name": "document_analyzer",
    "arguments": {
      "content": "This document contains various sections with different levels of complexity...",
      "analysis_type": "readability",
      "target_audience": "business",
      "include_suggestions": true
    }
  }
}
```

#### Comprehensive Analysis
```json
{
  "jsonrpc": "2.0",
  "id": "doc-analyze-002",
  "method": "tools/call",
  "params": {
    "name": "document_analyzer",
    "arguments": {
      "content": "Complete document content here...",
      "analysis_type": "comprehensive",
      "target_audience": "academic",
      "document_type": "report",
      "include_suggestions": true,
      "detailed_metrics": true
    }
  }
}
```

### Output Schema

#### Success Response - Readability Analysis
```json
{
  "jsonrpc": "2.0",
  "id": "doc-analyze-001",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Document analysis completed successfully"
      },
      {
        "type": "document_analysis",
        "analysis_type": "readability",
        "target_audience": "business",
        "document_type": "other",
        "summary": "Document has moderate readability suitable for business audience",
        "metrics": {
          "flesch_reading_ease": 65.2,
          "flesch_kincaid_grade": 8.1,
          "gunning_fog_index": 10.5,
          "coleman_liau_index": 9.8,
          "smog_index": 8.9,
          "automated_readability_index": 8.2
        },
        "readability_level": "moderate",
        "suggestions": [
          "Consider simplifying sentences longer than 20 words",
          "Reduce use of complex vocabulary in sections 2 and 4",
          "Add more paragraph breaks for better readability"
        ],
        "processing_time_ms": 2100
      }
    ]
  }
}
```

#### Success Response - Comprehensive Analysis
```json
{
  "jsonrpc": "2.0",
  "id": "doc-analyze-002",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Comprehensive document analysis completed"
      },
      {
        "type": "document_analysis",
        "analysis_type": "comprehensive",
        "target_audience": "academic",
        "document_type": "report",
        "summary": "Well-structured academic report with good clarity and appropriate tone",
        "structure_analysis": {
          "has_introduction": true,
          "has_conclusion": true,
          "section_count": 6,
          "paragraph_count": 24,
          "average_paragraph_length": 4.2,
          "structure_score": 8.5
        },
        "tone_analysis": {
          "primary_tone": "academic",
          "tone_consistency": 0.85,
          "formality_level": "high",
          "tone_score": 8.8
        },
        "clarity_analysis": {
          "sentence_complexity": "moderate",
          "vocabulary_level": "advanced",
          "ambiguity_score": 0.12,
          "clarity_score": 8.2
        },
        "completeness_analysis": {
          "has_executive_summary": true,
          "has_references": true,
          "has_appendix": false,
          "completeness_score": 7.8
        },
        "overall_score": 8.3,
        "suggestions": [
          "Add an executive summary for better overview",
          "Consider adding visual elements to complex sections",
          "Include more specific examples in section 3"
        ],
        "processing_time_ms": 4500
      }
    ]
  }
}
```

#### Error Response - Content Too Long
```json
{
  "jsonrpc": "2.0",
  "id": "doc-analyze-003",
  "error": {
    "code": -32602,
    "message": "Document content exceeds maximum length",
    "data": {
      "error_type": "content_too_long",
      "content_length": 75000,
      "max_length": 50000,
      "suggestions": [
        "Reduce content to 50,000 characters or less",
        "Analyze document in sections",
        "Use summarize operation first"
      ]
    }
  }
}
```

## Tool 4: Web Content Fetcher Tool

### Input Schema
```json
{
  "name": "web_content_fetcher",
  "description": "Fetch and process web content from specified URLs",
  "inputSchema": {
    "type": "object",
    "properties": {
      "url": {
        "type": "string",
        "description": "URL to fetch content from",
        "format": "uri",
        "examples": ["https://example.com/article", "https://news.site.com/story"]
      },
      "content_type": {
        "type": "string",
        "description": "Type of content to extract",
        "enum": ["full", "text", "summary", "headlines", "metadata"],
        "default": "text"
      },
      "max_length": {
        "type": "integer",
        "description": "Maximum content length to return",
        "minimum": 100,
        "maximum": 10000,
        "default": 2000
      },
      "include_links": {
        "type": "boolean",
        "description": "Include hyperlinks in extracted content",
        "default": false
      },
      "timeout": {
        "type": "integer",
        "description": "Request timeout in seconds",
        "minimum": 5,
        "maximum": 60,
        "default": 30
      },
      "user_agent": {
        "type": "string",
        "description": "Custom user agent string",
        "default": "Word-Addin-MCP/1.0"
      }
    },
    "required": ["url"]
  }
}
```

### Input Examples

#### Basic Web Content Fetch
```json
{
  "jsonrpc": "2.0",
  "id": "web-fetch-001",
  "method": "tools/call",
  "params": {
    "name": "web_content_fetcher",
    "arguments": {
      "url": "https://techcrunch.com/2024/01/15/ai-news"
    }
  }
}
```

#### Web Content with Summary
```json
{
  "jsonrpc": "2.0",
  "id": "web-fetch-002",
  "method": "tools/call",
  "params": {
    "name": "web_content_fetcher",
    "arguments": {
      "url": "https://example.com/article",
      "content_type": "summary",
      "max_length": 1000,
      "include_links": true
    }
  }
}
```

### Output Schema

#### Success Response - Text Content
```json
{
  "jsonrpc": "2.0",
  "id": "web-fetch-001",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Web content successfully fetched"
      },
      {
        "type": "web_content",
        "url": "https://techcrunch.com/2024/01/15/ai-news",
        "title": "Latest Developments in AI Technology",
        "content": "Artificial intelligence continues to evolve rapidly...",
        "content_type": "text",
        "content_length": 1850,
        "extraction_time_ms": 1200,
        "metadata": {
          "author": "Tech Reporter",
          "publish_date": "2024-01-15T09:00:00Z",
          "word_count": 450,
          "language": "en"
        },
        "status": "success"
      }
    ]
  }
}
```

#### Success Response - Summary Content
```json
{
  "jsonrpc": "2.0",
  "id": "web-fetch-002",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Web content summary generated successfully"
      },
      {
        "type": "web_content",
        "url": "https://example.com/article",
        "title": "Sample Article Title",
        "content": "This is a concise summary of the article content...",
        "content_type": "summary",
        "content_length": 850,
        "extraction_time_ms": 950,
        "metadata": {
          "author": "Unknown",
          "publish_date": null,
          "word_count": 120,
          "language": "en"
        },
        "links": [
          {
            "text": "Read more",
            "url": "https://example.com/full-article"
          }
        ],
        "status": "success"
      }
    ]
  }
}
```

#### Error Response - Network Error
```json
{
  "jsonrpc": "2.0",
  "id": "web-fetch-003",
  "error": {
    "code": -32603,
    "message": "Failed to fetch web content",
    "data": {
      "error_type": "network_error",
      "url": "https://example.com/article",
      "error_details": "Connection timeout",
      "suggestions": [
        "Check internet connection",
        "Verify URL is accessible",
        "Try again later"
      ]
    }
  }
}
```

#### Error Response - Invalid URL
```json
{
  "jsonrpc": "2.0",
  "id": "web-fetch-004",
  "error": {
    "code": -32602,
    "message": "Invalid URL format",
    "data": {
      "error_type": "invalid_url",
      "provided_url": "not-a-valid-url",
      "suggestions": [
        "Use valid HTTP/HTTPS URL format",
        "Include protocol (http:// or https://)",
        "Check URL spelling"
      ]
    }
  }
}
```

## Tool 5: Data Formatter Tool

### Input Schema
```json
{
  "name": "data_formatter",
  "description": "Format and structure data for document presentation",
  "inputSchema": {
    "type": "object",
    "properties": {
      "data": {
        "type": "string",
        "description": "Data to format (JSON, CSV, or plain text)",
        "minLength": 1,
        "maxLength": 20000
      },
      "input_format": {
        "type": "string",
        "description": "Format of input data",
        "enum": ["json", "csv", "text", "auto"],
        "default": "auto"
      },
      "output_format": {
        "type": "string",
        "description": "Desired output format",
        "enum": ["table", "list", "chart", "summary", "structured"],
        "default": "table"
      },
      "style": {
        "type": "string",
        "description": "Visual style for the output",
        "enum": ["simple", "professional", "academic", "creative"],
        "default": "professional"
      },
      "max_items": {
        "type": "integer",
        "description": "Maximum number of items to include",
        "minimum": 1,
        "maximum": 1000,
        "default": 100
      },
      "include_headers": {
        "type": "boolean",
        "description": "Include column headers in table output",
        "default": true
      },
      "sort_by": {
        "type": "string",
        "description": "Column to sort by (for table output)",
        "default": null
      },
      "sort_order": {
        "type": "string",
        "description": "Sort order (ascending or descending)",
        "enum": ["asc", "desc"],
        "default": "asc"
      }
    },
    "required": ["data", "output_format"]
  }
}
```

### Input Examples

#### JSON to Table Format
```json
{
  "jsonrpc": "2.0",
  "id": "data-format-001",
  "method": "tools/call",
  "params": {
    "name": "data_formatter",
    "arguments": {
      "data": "[{\"name\":\"John\",\"age\":30,\"department\":\"Engineering\"},{\"name\":\"Jane\",\"age\":25,\"department\":\"Marketing\"}]",
      "input_format": "json",
      "output_format": "table",
      "style": "professional",
      "include_headers": true
    }
  }
}
```

#### CSV to List Format
```json
{
  "jsonrpc": "2.0",
  "id": "data-format-002",
  "method": "tools/call",
  "params": {
    "name": "data_formatter",
    "arguments": {
      "data": "Product,Price,Category\nLaptop,1200,Electronics\nDesk,300,Furniture\nBook,25,Education",
      "input_format": "csv",
      "output_format": "list",
      "style": "simple",
      "max_items": 10
    }
  }
}
```

### Output Schema

#### Success Response - Table Format
```json
{
  "jsonrpc": "2.0",
  "id": "data-format-001",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Data successfully formatted as table"
      },
      {
        "type": "formatted_data",
        "input_format": "json",
        "output_format": "table",
        "style": "professional",
        "formatted_content": {
          "type": "table",
          "headers": ["Name", "Age", "Department"],
          "rows": [
            ["John", "30", "Engineering"],
            ["Jane", "25", "Marketing"]
          ],
          "row_count": 2,
          "column_count": 3
        },
        "word_table_format": {
          "table_style": "Table Grid",
          "header_row": true,
          "alternating_rows": false,
          "borders": true
        },
        "processing_time_ms": 450
      }
    ]
  }
}
```

#### Success Response - List Format
```json
{
  "jsonrpc": "2.0",
  "id": "data-format-002",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Data successfully formatted as list"
      },
      {
        "type": "formatted_data",
        "input_format": "csv",
        "output_format": "list",
        "style": "simple",
        "formatted_content": {
          "type": "list",
          "items": [
            "Product: Laptop, Price: $1200, Category: Electronics",
            "Product: Desk, Price: $300, Category: Furniture",
            "Product: Book, Price: $25, Category: Education"
          ],
          "item_count": 3
        },
        "word_list_format": {
          "list_type": "bulleted",
          "bullet_style": "•",
          "indentation": "standard"
        },
        "processing_time_ms": 320
      }
    ]
  }
}
```

#### Error Response - Invalid Data Format
```json
{
  "jsonrpc": "2.0",
  "id": "data-format-003",
  "error": {
    "code": -32603,
    "message": "Failed to parse input data",
    "data": {
      "error_type": "parse_error",
      "input_format": "json",
      "error_details": "Invalid JSON syntax at position 15",
      "suggestions": [
        "Check JSON syntax and formatting",
        "Validate JSON using online tools",
        "Ensure proper quote escaping"
      ]
    }
  }
}
```

## Common Error Patterns

### MCP Protocol Errors
```json
{
  "jsonrpc": "2.0",
  "id": "request-id",
  "error": {
    "code": -32700,
    "message": "Parse error",
    "data": {
      "error_type": "json_parse_error",
      "position": 25,
      "line": 3
    }
  }
}
```

### Tool Execution Errors
```json
{
  "jsonrpc": "2.0",
  "id": "request-id",
  "error": {
    "code": -32603,
    "message": "Internal error",
    "data": {
      "error_type": "tool_execution_failed",
      "tool_name": "tool_name",
      "error_details": "Tool-specific error message",
      "suggestions": [
        "Check input parameters",
        "Verify tool availability",
        "Contact support if issue persists"
      ]
    }
  }
}
```

### Rate Limiting Errors
```json
{
  "jsonrpc": "2.0",
  "id": "request-id",
  "error": {
    "code": -32603,
    "message": "Rate limit exceeded",
    "data": {
      "error_type": "rate_limit_exceeded",
      "tool_name": "tool_name",
      "retry_after": 60,
      "suggestions": [
        "Wait 60 seconds before retrying",
        "Reduce request frequency",
        "Contact administrator for quota increase"
      ]
    }
  }
}
```

## Data Transformation Flow

### Input Validation
1. **Schema Validation**: Validate input against tool schema
2. **Type Checking**: Ensure data types match expected format
3. **Range Validation**: Check numeric values within acceptable ranges
4. **Format Validation**: Verify URL, file path, and data format validity

### Processing Pipeline
1. **Input Sanitization**: Clean and normalize input data
2. **Tool Execution**: Execute tool-specific logic
3. **Result Processing**: Format and structure tool output
4. **Response Generation**: Create MCP-compliant response

### Output Formatting
1. **Content Structure**: Organize content into appropriate MCP format
2. **Metadata Addition**: Include processing metadata and timing
3. **Error Handling**: Provide detailed error information when needed
4. **Response Validation**: Ensure response follows MCP protocol

## Performance Considerations

### Response Time Targets
- **Simple Tools** (Data Formatter): < 500ms
- **Medium Tools** (Text Processor): < 2 seconds
- **Complex Tools** (Document Analyzer): < 5 seconds
- **External Tools** (Web Fetcher): < 10 seconds

### Memory Usage Limits
- **Input Processing**: Max 50MB per request
- **Tool Execution**: Max 100MB per tool
- **Response Generation**: Max 25MB per response
- **Total Request**: Max 150MB per complete request

### Caching Strategy
- **Tool Schemas**: Cache for 1 hour
- **Frequently Used Data**: Cache for 15 minutes
- **Web Content**: Cache for 30 minutes
- **Analysis Results**: Cache for 10 minutes

This comprehensive I/O specification ensures consistent, predictable behavior across all MCP tools while providing detailed error handling and performance optimization for the Word Add-in integration.
