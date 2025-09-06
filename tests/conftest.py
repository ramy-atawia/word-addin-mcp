"""
Test configuration and fixtures for Word Add-in MCP System
"""
import pytest
import pytest_asyncio
import asyncio
import httpx
import json
import time
from typing import Dict, Any, List
import os
import sys
from fastapi.testclient import TestClient

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Test configuration
BASE_URL = "https://localhost:9000"
API_BASE = f"{BASE_URL}/api/v1"
HEALTH_URL = f"{BASE_URL}/health"
TEST_TIMEOUT = 30

# SSL configuration for localhost testing
SSL_VERIFY = False  # For localhost with self-signed certs

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_client():
    """Create a test client for the FastAPI application."""
    try:
        from backend.app.main import app
        return TestClient(app)
    except ImportError as e:
        pytest.skip(f"Could not import app: {e}")

@pytest_asyncio.fixture(scope="function")
async def http_client():
    """Create an HTTP client for testing."""
    async with httpx.AsyncClient(
        verify=SSL_VERIFY,
        timeout=TEST_TIMEOUT,
        follow_redirects=True
    ) as client:
        yield client

@pytest.fixture
def sample_document():
    """Sample document content for testing."""
    return """
    This is a comprehensive business report covering Q3 2025 financial results.
    
    Executive Summary:
    - Revenue increased by 15% compared to the previous quarter
    - Net profit margin improved to 12.5%
    - Customer acquisition cost decreased by 8%
    
    Key Highlights:
    1. New product launches in the AI/ML space
    2. Market expansion into European markets
    3. Strategic partnerships with major technology companies
    4. Investment in research and development increased by 25%
    
    Financial Performance:
    - Total Revenue: $2.5M (Q3 2025)
    - Operating Expenses: $1.8M
    - Net Income: $312K
    - Cash Flow: $450K positive
    
    Future Outlook:
    The company is well-positioned for continued growth in Q4 2025 and beyond.
    Key focus areas include product innovation, market expansion, and operational efficiency.
    """

@pytest.fixture
def sample_conversation():
    """Sample conversation history for testing."""
    return [
        {
            "role": "user",
            "content": "Hello, I need help analyzing a business report.",
            "timestamp": time.time() - 300
        },
        {
            "role": "assistant", 
            "content": "I'd be happy to help you analyze your business report. Please share the document content and let me know what specific analysis you'd like me to perform.",
            "timestamp": time.time() - 240
        },
        {
            "role": "user",
            "content": "Can you summarize the key financial metrics?",
            "timestamp": time.time() - 180
        }
    ]

@pytest.fixture
def test_tools():
    """Available tools for testing."""
    return [
        "web_search_tool",
        "text_analysis_tool", 
        "document_analysis_tool",
        "file_reader_tool"
    ]

class TestResult:
    """Helper class to track test results."""
    def __init__(self):
        self.results = []
        self.start_time = time.time()
    
    def add_result(self, test_id: str, status: str, details: Dict[str, Any]):
        """Add a test result."""
        self.results.append({
            "test_id": test_id,
            "status": status,
            "details": details,
            "timestamp": time.time()
        })
    
    def get_summary(self):
        """Get test summary."""
        total = len(self.results)
        passed = len([r for r in self.results if r["status"] == "PASS"])
        failed = len([r for r in self.results if r["status"] == "FAIL"])
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
            "execution_time": time.time() - self.start_time
        }

@pytest.fixture
def test_result():
    """Test result tracker."""
    return TestResult()