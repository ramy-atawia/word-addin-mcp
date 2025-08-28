"""
Pytest configuration and fixtures for Word Add-in MCP Project.
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

# Import the FastAPI app
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.main import app
from app.core.config import settings

# Configure pytest-asyncio
pytest_plugins = ['pytest_asyncio']

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch('app.core.config.settings') as mock:
        mock.APP_NAME = "Word Add-in MCP API Test"
        mock.APP_VERSION = "1.0.0"
        mock.ENVIRONMENT = "testing"
        mock.DEBUG = True
        mock.FASTAPI_HOST = "127.0.0.1"
        mock.FASTAPI_PORT = 9000
        mock.FASTAPI_RELOAD = False
        mock.FASTAPI_LOG_LEVEL = "DEBUG"
        mock.ENABLE_SWAGGER = True
        mock.ENABLE_RELOAD = False
        mock.SECRET_KEY = "test-secret-key-32-characters-minimum"
        mock.ALGORITHM = "HS256"
        mock.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock.REFRESH_TOKEN_EXPIRE_DAYS = 7
        mock.ALLOWED_ORIGINS = ["http://localhost:3001"]
        mock.ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        mock.ALLOWED_HEADERS = ["*"]
        mock.RATE_LIMIT_PER_MINUTE = 1000
        mock.RATE_LIMIT_PER_HOUR = 10000
        mock.DATABASE_URL = "sqlite:///./test.db"
        mock.REDIS_URL = "redis://localhost:6379"
        mock.CACHE_TTL = 3600
        mock.AZURE_OPENAI_API_KEY = "test-api-key"
        mock.AZURE_OPENAI_ENDPOINT = "https://test.openai.azure.com/"
        mock.AZURE_OPENAI_API_VERSION = "2024-02-15-preview"
        mock.AZURE_OPENAI_DEPLOYMENT_NAME = "test-deployment"
        mock.AZURE_OPENAI_MODEL_NAME = "gpt-4"
        mock.MCP_SERVER_URL = "http://localhost:9001"
        mock.MCP_SERVER_TOKEN = "test-token"
        mock.MCP_SERVER_TIMEOUT = 30
        mock.MCP_SERVER_MAX_RETRIES = 3
        mock.MAX_FILE_SIZE = 1048576
        mock.ALLOWED_FILE_TYPES = ["txt", "json", "csv", "xml", "md"]
        mock.UPLOAD_DIR = "./test_uploads"
        mock.LOG_LEVEL = "DEBUG"
        mock.LOG_FORMAT = "json"
        mock.LOG_FILE = "./test_logs/app.log"
        mock.LOG_MAX_SIZE = 1048576
        mock.LOG_BACKUP_COUNT = 1
        mock.PROMETHEUS_ENABLED = False
        mock.HEALTH_CHECK_INTERVAL = 30
        mock.OFFICE_JS_VERSION = "1.1.0"
        mock.OFFICE_JS_CDN = "https://appsforoffice.microsoft.com/lib/1.1/hosted/"
        mock.FRONTEND_URL = "http://localhost:3001"
        mock.FRONTEND_BUILD_DIR = "./test_dist"
        mock.FRONTEND_PUBLIC_PATH = "/"
        mock.TESTING = True
        mock.TEST_DATABASE_URL = "sqlite:///./test.db"
        yield mock


@pytest.fixture
def sample_mcp_tool_request():
    """Sample MCP tool execution request for testing."""
    return {
        "tool_name": "file_reader",
        "parameters": {
            "path": "./test_files/sample.txt",
            "encoding": "utf-8"
        },
        "session_id": "test-session-123",
        "request_id": "test-request-456",
        "timeout": 30,
        "priority": "normal"
    }


@pytest.fixture
def sample_chat_request():
    """Sample chat request for testing."""
    return {
        "message": "Hello, how can you help me with my document?",
        "session_id": "test-session-123",
        "user_id": "test-user-456",
        "context": {
            "document_title": "Test Document",
            "current_section": "Introduction"
        },
        "options": {
            "model": "gpt-4",
            "temperature": 0.7
        }
    }


@pytest.fixture
def sample_document_info():
    """Sample document information for testing."""
    return {
        "title": "Test Document.docx",
        "author": "Test Author",
        "created_date": 1640995200.0,  # 2022-01-01
        "modified_date": 1640995200.0,
        "word_count": 100,
        "character_count": 500,
        "page_count": 1,
        "language": "en-US",
        "template": "Normal.dotm",
        "path": "C:\\Test\\Test Document.docx"
    }


@pytest.fixture
def mock_mcp_server():
    """Mock MCP server for testing."""
    mock_server = Mock()
    mock_server.url = "http://localhost:9001"
    mock_server.token = "test-token"
    mock_server.is_connected.return_value = True
    mock_server.get_tools.return_value = [
        {
            "name": "file_reader",
            "description": "Read file contents",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "encoding": {"type": "string"}
                },
                "required": ["path"]
            }
        }
    ]
    mock_server.execute_tool.return_value = {
        "success": True,
        "result": "File content here",
        "execution_time": 0.1
    }
    return mock_server


@pytest.fixture
def mock_azure_openai():
    """Mock Azure OpenAI client for testing."""
    mock_client = Mock()
    mock_client.chat.completions.create.return_value = Mock(
        choices=[
            Mock(
                message=Mock(
                    content="This is a test response from Azure OpenAI"
                )
            )
        ],
        usage=Mock(
            total_tokens=50,
            prompt_tokens=20,
            completion_tokens=30
        )
    )
    return mock_client


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment before each test."""
    # Create test directories
    os.makedirs("./test_logs", exist_ok=True)
    os.makedirs("./test_uploads", exist_ok=True)
    os.makedirs("./test_dist", exist_ok=True)
    os.makedirs("./test_files", exist_ok=True)
    
    # Create test files
    with open("./test_files/sample.txt", "w") as f:
        f.write("This is a test file for unit testing.")
    
    yield
    
    # Cleanup test files
    import shutil
    if os.path.exists("./test_logs"):
        shutil.rmtree("./test_logs")
    if os.path.exists("./test_uploads"):
        shutil.rmtree("./test_uploads")
    if os.path.exists("./test_dist"):
        shutil.rmtree("./test_dist")
    if os.path.exists("./test_files"):
        shutil.rmtree("./test_files")
