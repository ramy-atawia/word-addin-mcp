"""
Tests for internal MCP server.
"""

import pytest
import aiohttp
from fastapi.testclient import TestClient

from app.internal_mcp_app import app

@pytest.fixture
def client():
    return TestClient(app)

def test_internal_mcp_server_health(client):
    """Test internal MCP server health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["tools_count"] == 4
    assert "web_search" in data["tools"]

def test_internal_mcp_server_tools(client):
    """Test internal MCP server tools endpoint."""
    response = client.get("/mcp/tools")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4
    tool_names = [tool["name"] for tool in data]
    assert "web_search_tool" in tool_names
    assert "prior_art_search_tool" in tool_names
    assert "claim_drafting_tool" in tool_names
    assert "claim_analysis_tool" in tool_names

@pytest.mark.asyncio
async def test_internal_mcp_server_tool_execution(client):
    """Test internal MCP server tool execution."""
    # Test web search tool
    response = client.post("/mcp/tools/web_search_tool", json={
        "query": "test query",
        "max_results": 5
    })
    assert response.status_code == 200
    data = response.json()
    assert "results" in data

@pytest.mark.asyncio
async def test_internal_mcp_server_connection():
    """Test connection to internal MCP server."""
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8001/health") as response:
            assert response.status == 200
            data = await response.json()
            assert data["status"] == "healthy"
