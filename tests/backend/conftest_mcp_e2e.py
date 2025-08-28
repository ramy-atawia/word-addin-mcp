"""
MCP E2E Test Configuration and Fixtures

This file provides test configuration and fixtures specifically for
MCP end-to-end testing scenarios.
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.mcp_client import MCPClient, MCPConnectionConfig
from backend.app.core.mcp_server import MCPServer
from backend.app.services.mcp_service import MCPService


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mcp_server_instance():
    """Create an MCP server instance for testing."""
    return MCPServer()


@pytest.fixture
def mcp_client_config():
    """Create MCP client configuration for testing."""
    return MCPConnectionConfig(
        server_url="http://localhost:8000",
        timeout=5,
        max_retries=2,
        retry_delay=0.1,
        health_check_interval=5.0,
        connection_pool_size=3
    )


@pytest.fixture
def mcp_service_instance():
    """Create an MCP service instance for testing."""
    return MCPService()


@pytest.fixture
def sample_text_content():
    """Provide sample text content for testing."""
    return {
        "short": "This is a short text for testing.",
        "medium": "This is a medium length text that contains multiple sentences and should be sufficient for testing various text processing operations including summarization and analysis.",
        "long": """
        This is a longer text document that contains multiple paragraphs and should be used for testing 
        document analysis capabilities. It includes various types of content such as technical information,
        descriptive text, and structured content that can be processed by different MCP tools.
        
        The document contains multiple sentences with varying complexity and should provide a good test
        case for tools like text summarization, keyword extraction, and readability analysis.
        
        We can also test how the tools handle different formatting, punctuation, and content types
        to ensure robust processing capabilities across various input scenarios.
        """,
        "technical": """
        Machine learning algorithms require careful consideration of several factors including:
        1. Data quality and preprocessing
        2. Feature engineering and selection
        3. Model selection and hyperparameter tuning
        4. Evaluation metrics and validation strategies
        
        The choice of algorithm depends on the specific problem domain, available data, and
        performance requirements. Common approaches include supervised learning, unsupervised
        learning, and reinforcement learning techniques.
        """
    }


@pytest.fixture
def sample_document_content():
    """Provide sample document content for testing."""
    return {
        "simple": {
            "content": "This is a simple document for basic analysis.",
            "analysis_type": "readability",
            "expected_operations": ["readability"]
        },
        "complex": {
            "content": """
            Complex document with multiple sections:
            
            Introduction:
            This document provides a comprehensive overview of the system architecture.
            
            Technical Details:
            The system consists of multiple components including the frontend interface,
            backend API services, and database layer.
            
            Conclusion:
            This architecture provides scalability and maintainability.
            """,
            "analysis_type": "structure",
            "expected_operations": ["structure", "summary"]
        },
        "technical": {
            "content": """
            API Documentation:
            
            Endpoints:
            - GET /api/v1/health
            - POST /api/v1/mcp/initialize
            - GET /api/v1/mcp/tools
            - POST /api/v1/mcp/tools/call
            
            Authentication:
            JWT tokens required for protected endpoints.
            
            Rate Limiting:
            Maximum 100 requests per minute per IP address.
            """,
            "analysis_type": "keyword_extraction",
            "expected_operations": ["keyword_extraction", "summary"]
        }
    }


@pytest.fixture
def sample_file_paths():
    """Provide sample file paths for testing file operations."""
    # Create temporary test files
    temp_dir = tempfile.mkdtemp()
    
    # Create a simple text file
    simple_file = os.path.join(temp_dir, "simple.txt")
    with open(simple_file, "w") as f:
        f.write("This is a simple test file for MCP testing.")
    
    # Create a JSON file
    json_file = os.path.join(temp_dir, "data.json")
    with open(json_file, "w") as f:
        f.write('{"name": "test", "value": 42, "items": ["a", "b", "c"]}')
    
    # Create a markdown file
    markdown_file = os.path.join(temp_dir, "document.md")
    with open(markdown_file, "w") as f:
        f.write("""
        # Test Document
        
        This is a markdown document for testing.
        
        ## Section 1
        Content for section 1.
        
        ## Section 2
        Content for section 2.
        """)
    
    yield {
        "simple": simple_file,
        "json": json_file,
        "markdown": markdown_file,
        "directory": temp_dir
    }
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


@pytest.fixture
def mcp_test_scenarios():
    """Provide predefined MCP test scenarios."""
    return {
        "initialization": {
            "name": "MCP Initialization",
            "description": "Test complete MCP protocol initialization",
            "steps": [
                "Send initialize request",
                "Receive server capabilities",
                "Verify protocol version",
                "Validate server info"
            ],
            "expected_result": "Successful connection establishment"
        },
        "tool_discovery": {
            "name": "Tool Discovery",
            "description": "Test MCP tool discovery and listing",
            "steps": [
                "Request tools list",
                "Receive tool definitions",
                "Validate tool schemas",
                "Verify tool capabilities"
            ],
            "expected_result": "Complete tool catalog with schemas"
        },
        "text_processing": {
            "name": "Text Processing",
            "description": "Test text processing tool operations",
            "steps": [
                "Execute summarize operation",
                "Execute translate operation",
                "Execute keyword extraction",
                "Validate operation results"
            ],
            "expected_result": "Accurate text processing results"
        },
        "document_analysis": {
            "name": "Document Analysis",
            "description": "Test document analysis capabilities",
            "steps": [
                "Analyze simple documents",
                "Analyze complex documents",
                "Analyze technical documents",
                "Validate analysis results"
            ],
            "expected_result": "Comprehensive document insights"
        },
        "error_handling": {
            "name": "Error Handling",
            "description": "Test MCP error handling and recovery",
            "steps": [
                "Send invalid requests",
                "Handle method not found",
                "Handle parameter validation errors",
                "Verify error recovery"
            ],
            "expected_result": "Graceful error handling and recovery"
        },
        "performance": {
            "name": "Performance Testing",
            "description": "Test MCP performance under load",
            "steps": [
                "Execute concurrent requests",
                "Measure response times",
                "Test request ID uniqueness",
                "Validate throughput"
            ],
            "expected_result": "Consistent performance under load"
        }
    }


@pytest.fixture
def mcp_error_codes():
    """Provide MCP standard error codes for testing."""
    return {
        "PARSE_ERROR": -32700,
        "INVALID_REQUEST": -32600,
        "METHOD_NOT_FOUND": -32601,
        "INVALID_PARAMS": -32602,
        "INTERNAL_ERROR": -32603,
        "SERVER_ERROR_START": -32000,
        "SERVER_ERROR_END": -32099
    }


@pytest.fixture
def mcp_protocol_versions():
    """Provide MCP protocol versions for testing."""
    return {
        "current": "2024-11-05",
        "supported": ["2024-11-05", "2024-10-01"],
        "deprecated": ["2024-09-01"],
        "future": "2025-01-01"
    }


@pytest.fixture
def mcp_capability_sets():
    """Provide different MCP capability sets for testing."""
    return {
        "minimal": {
            "tools": {}
        },
        "basic": {
            "tools": {
                "listChanged": True
            }
        },
        "extended": {
            "tools": {
                "listChanged": True
            },
            "chat": {
                "completions": True
            },
            "files": {
                "list": True,
                "upload": True
            }
        },
        "full": {
            "tools": {
                "listChanged": True
            },
            "chat": {
                "completions": True,
                "streaming": True
            },
            "files": {
                "list": True,
                "upload": True,
                "delete": True
            },
            "memory": {
                "conversation": True,
                "search": True
            }
        }
    }


@pytest.fixture
def mcp_test_data():
    """Provide comprehensive test data for MCP testing."""
    return {
        "client_info": {
            "minimal": {
                "name": "minimal-client",
                "version": "0.1.0"
            },
            "standard": {
                "name": "word-addin-mcp-client",
                "version": "1.0.0"
            },
            "advanced": {
                "name": "enterprise-mcp-client",
                "version": "2.0.0",
                "capabilities": ["advanced_tools", "streaming", "memory"]
            }
        },
        "tool_arguments": {
            "file_reader": {
                "valid": {
                    "path": "/tmp/test.txt",
                    "encoding": "utf-8",
                    "max_size": 1024
                },
                "invalid": {
                    "path": "",
                    "max_size": -1
                },
                "missing_required": {
                    "encoding": "utf-8"
                }
            },
            "text_processor": {
                "valid": {
                    "text": "Sample text for processing",
                    "operation": "summarize"
                },
                "invalid": {
                    "text": "",
                    "operation": "invalid_operation"
                }
            },
            "document_analyzer": {
                "valid": {
                    "content": "Document content for analysis",
                    "analysis_type": "readability"
                },
                "invalid": {
                    "content": "",
                    "analysis_type": "invalid_type"
                }
            }
        },
        "expected_responses": {
            "success": {
                "jsonrpc": "2.0",
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": "Expected result content"
                        }
                    ]
                }
            },
            "error": {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32602,
                    "message": "Invalid params",
                    "data": {
                        "details": "Parameter validation failed"
                    }
                }
            }
        }
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test."""
    # Set test environment variables
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    # Setup any test-specific configurations
    yield
    
    # Cleanup after each test
    pass


@pytest.fixture
def mock_mcp_server():
    """Create a mock MCP server for testing."""
    mock_server = Mock()
    mock_server.status = "running"
    mock_server.capabilities = {
        "tools": {"listChanged": True},
        "chat": {"completions": True}
    }
    mock_server.tool_count = 5
    return mock_server


@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client for testing."""
    mock_client = Mock()
    mock_client.server_url = "http://localhost:8000"
    mock_client.connected = True
    mock_client.capabilities = {"tools": {"listChanged": True}}
    return mock_client
