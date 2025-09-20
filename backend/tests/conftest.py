"""
Pytest configuration and fixtures for backend tests.
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Add backend to Python path
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

# Mock LangGraph if not available
try:
    import langgraph
except ImportError:
    # Create mock LangGraph modules
    langgraph_mock = Mock()
    langgraph_mock.graph = Mock()
    langgraph_mock.graph.StateGraph = Mock()
    langgraph_mock.graph.END = Mock()
    
    sys.modules['langgraph'] = langgraph_mock
    sys.modules['langgraph.graph'] = langgraph_mock.graph

# Mock FastMCP if not available
try:
    import fastmcp
except ImportError:
    fastmcp_mock = Mock()
    sys.modules['fastmcp'] = fastmcp_mock

@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    mock_client = Mock()
    mock_client.ainvoke = Mock(return_value=Mock(content="Mock LLM response"))
    return mock_client

@pytest.fixture
def mock_mcp_orchestrator():
    """Mock MCP orchestrator for testing."""
    mock_orchestrator = Mock()
    mock_orchestrator.execute_tool = Mock(return_value={
        "success": True,
        "result": "Mock tool result",
        "timestamp": 1234567890
    })
    mock_orchestrator.list_all_tools = Mock(return_value={
        "tools": [
            {"name": "web_search_tool", "description": "Search the web"},
            {"name": "prior_art_search_tool", "description": "Search prior art"},
            {"name": "claim_drafting_tool", "description": "Draft patent claims"},
            {"name": "claim_analysis_tool", "description": "Analyze patent claims"}
        ]
    })
    return mock_orchestrator

@pytest.fixture
def sample_agent_state():
    """Sample AgentState for testing."""
    return {
        "user_input": "test input",
        "document_content": "test document",
        "conversation_history": [],
        "available_tools": [
            {"name": "web_search_tool", "description": "Search the web"},
            {"name": "claim_drafting_tool", "description": "Draft patent claims"}
        ],
        "selected_tool": "",
        "tool_parameters": {},
        "tool_result": None,
        "final_response": "",
        "intent_type": ""
    }

@pytest.fixture
def sample_multi_step_state():
    """Sample MultiStepAgentState for testing."""
    return {
        "user_input": "draft 1 claim for 5G in AI, then perform prior art",
        "document_content": "test document",
        "conversation_history": [],
        "available_tools": [
            {"name": "prior_art_search_tool", "description": "Search prior art"},
            {"name": "claim_drafting_tool", "description": "Draft patent claims"}
        ],
        "workflow_plan": [],
        "current_step": 0,
        "total_steps": 0,
        "step_results": {},
        "selected_tool": "",
        "tool_parameters": {},
        "final_response": "",
        "intent_type": "",
        "execution_metadata": {}
    }

@pytest.fixture
def sample_workflow_plan():
    """Sample workflow plan for testing."""
    return [
        {
            "step": 1,
            "tool": "prior_art_search_tool",
            "parameters": {"query": "5G AI"},
            "depends_on": None,
            "output_key": "prior_art_results",
            "description": "Search for prior art related to 5G AI"
        },
        {
            "step": 2,
            "tool": "claim_drafting_tool",
            "parameters": {
                "user_query": "draft 1 claim for 5G in AI",
                "conversation_context": "{prior_art_results}"
            },
            "depends_on": 1,
            "output_key": "draft_claims",
            "description": "Draft patent claims based on prior art search"
        }
    ]

@pytest.fixture
def sample_step_results():
    """Sample step results for testing."""
    return {
        1: {
            "success": True,
            "result": "# Prior Art Search Report\n\nFound 5 relevant patents...",
            "timestamp": 1234567890
        },
        2: {
            "success": True,
            "result": "# Patent Claims\n\n## Claim 1\nA method for 5G AI...",
            "timestamp": 1234567891
        }
    }

# Skip tests that require LangGraph if not available
def pytest_configure(config):
    """Configure pytest with custom markers and skip conditions."""
    try:
        import langgraph
        config.addinivalue_line("markers", "langgraph: LangGraph-specific tests")
    except ImportError:
        config.addinivalue_line("markers", "langgraph: LangGraph-specific tests (skipped - not available)")
        
        # Skip LangGraph tests if not available
        def pytest_collection_modifyitems(config, items):
            for item in items:
                if "langgraph" in item.nodeid.lower():
                    skip_marker = pytest.mark.skip(reason="LangGraph not available")
                    item.add_marker(skip_marker)

# Auto-skip LangGraph tests if LangGraph is not available
def pytest_runtest_setup(item):
    """Skip LangGraph tests if LangGraph is not available."""
    if "langgraph" in item.nodeid.lower():
        try:
            import langgraph
        except ImportError:
            pytest.skip("LangGraph not available")
