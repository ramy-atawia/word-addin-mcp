"""
Pytest configuration for backend tests.

This file provides shared fixtures and configuration for all backend tests,
including the new patent search integration tests.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.main import app


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
def mock_llm_response():
    """Mock LLM response for testing."""
    return {
        "success": True,
        "text": "Mock LLM response for testing purposes.",
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        }
    }


@pytest.fixture
def mock_patentsview_response():
    """Mock PatentsView API response for testing."""
    return {
        "patents": [
            {
                "patent_id": "12345678",
                "patent_title": "Test Patent for 5G Handover",
                "patent_abstract": "A method for performing handover in 5G networks using artificial intelligence to optimize handover decisions and improve network performance.",
                "patent_date": "2024-01-15",
                "inventors": [
                    {
                        "inventor_name_first": "John",
                        "inventor_name_last": "Doe"
                    }
                ],
                "assignees": [
                    {
                        "assignee_organization": "Test Company Inc."
                    }
                ]
            }
        ]
    }


@pytest.fixture
def mock_claims_response():
    """Mock PatentsView claims API response for testing."""
    return {
        "patents": [
            {
                "patent_id": "12345678",
                "claims": [
                    {
                        "claim_sequence": 1,
                        "claim_number": "1",
                        "claim_text": "A method for performing handover in a wireless communication system comprising: receiving measurement reports from user equipment; analyzing the measurement reports using artificial intelligence; and determining handover parameters based on the analysis.",
                        "claim_dependent": False
                    },
                    {
                        "claim_sequence": 2,
                        "claim_number": "2",
                        "claim_text": "The method of claim 1, wherein the artificial intelligence comprises a neural network configured to predict optimal handover timing.",
                        "claim_dependent": True
                    }
                ]
            }
        ]
    }


@pytest.fixture
def patent_search_test_queries():
    """Validated test queries for patent search integration tests."""
    return [
        {
            "query": "5G handover using AI",
            "description": "Tests AI-based handover technology in 5G networks",
            "expected_keywords": ["5G", "handover", "AI", "artificial intelligence", "neural network"],
            "min_patents": 5,
            "max_patents": 50
        },
        {
            "query": "5G dynamic spectrum sharing",
            "description": "Tests dynamic spectrum sharing technology in 5G",
            "expected_keywords": ["5G", "dynamic", "spectrum", "sharing", "DSS"],
            "min_patents": 5,
            "max_patents": 50
        },
        {
            "query": "Financial AI auditing",
            "description": "Tests AI applications in financial auditing",
            "expected_keywords": ["financial", "AI", "auditing", "artificial intelligence", "fraud detection"],
            "min_patents": 5,
            "max_patents": 50
        }
    ]


@pytest.fixture
def mock_azure_openai():
    """Mock Azure OpenAI client for testing."""
    with patch('app.services.llm_client.AzureOpenAI') as mock:
        mock_instance = Mock()
        mock_instance.chat.completions.create.return_value = Mock(
            choices=[
                Mock(
                    message=Mock(
                        content="Mock LLM response for testing"
                    )
                )
            ],
            usage=Mock(
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150
            )
        )
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for API testing."""
    with patch('httpx.AsyncClient') as mock:
        mock_instance = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"patents": []}
        mock_response.text = "Mock response text"
        mock_instance.post.return_value = mock_response
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        mock.return_value = mock_instance
        yield mock_instance


# Pytest markers for different test categories
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "patent_search: marks tests as patent search specific"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
    config.addinivalue_line(
        "markers", "api: marks tests that require external API calls"
    )
