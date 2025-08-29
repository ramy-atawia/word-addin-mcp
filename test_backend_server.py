#!/usr/bin/env python3
"""
Simple test backend server for Word Add-in MCP integration testing.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn

app = FastAPI(title="Test MCP Backend", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock MCP tools data
MOCK_TOOLS = [
    {
        "name": "web_content_fetcher",
        "description": "Fetch and analyze web content from URLs",
        "parameters": {
            "url": {"type": "string", "description": "URL to fetch content from"},
            "extract_type": {"type": "string", "enum": ["text", "html", "summary"], "description": "Type of content to extract"},
            "max_length": {"type": "integer", "description": "Maximum length of extracted content"}
        }
    },
    {
        "name": "text_processor",
        "description": "Process and analyze text content using AI",
        "parameters": {
            "text": {"type": "string", "description": "Text content to process"},
            "operation": {"type": "string", "enum": ["summarize", "analyze", "enhance"], "description": "Type of processing operation"}
        }
    },
    {
        "name": "web_search",
        "description": "Search the web for information",
        "parameters": {
            "query": {"type": "string", "description": "Search query"},
            "max_results": {"type": "integer", "description": "Maximum number of results to return"}
        }
    }
]

class MCPToolExecutionRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    session_id: str = None
    user_id: str = None

class MCPToolExecutionResult(BaseModel):
    success: bool
    data: Any = None
    error: str = None
    status: str = "completed"

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Test MCP Backend is running"}

@app.get("/mcp/tools")
async def get_mcp_tools():
    """Get available MCP tools."""
    return {"tools": MOCK_TOOLS}

@app.post("/mcp/tools/execute")
async def execute_mcp_tool(request: MCPToolExecutionRequest):
    """Execute an MCP tool."""
    try:
        # Find the requested tool
        tool = next((t for t in MOCK_TOOLS if t["name"] == request.tool_name), None)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{request.tool_name}' not found")
        
        # Mock execution based on tool type
        if request.tool_name == "web_content_fetcher":
            url = request.parameters.get("url", "")
            extract_type = request.parameters.get("extract_type", "text")
            result = f"Mock web content fetched from {url} with {extract_type} extraction. This is a simulated response for testing the Word Add-in integration."
            
        elif request.tool_name == "text_processor":
            text = request.parameters.get("text", "")
            operation = request.parameters.get("operation", "summarize")
            result = f"Mock {operation} operation performed on text: '{text[:50]}...'. This is a simulated AI processing result for testing."
            
        elif request.tool_name == "web_search":
            query = request.parameters.get("query", "")
            max_results = request.parameters.get("max_results", 5)
            result = f"Mock web search for '{query}' returned {max_results} simulated results. This is a test response for the Word Add-in integration."
            
        else:
            result = f"Mock execution of {request.tool_name} with parameters: {request.parameters}"
        
        return MCPToolExecutionResult(
            success=True,
            data=result,
            status="completed"
        )
        
    except Exception as e:
        return MCPToolExecutionResult(
            success=False,
            error=str(e),
            status="error"
        )

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Test MCP Backend for Word Add-in",
        "endpoints": {
            "health": "/health",
            "mcp_tools": "/mcp/tools",
            "execute_tool": "/mcp/tools/execute"
        }
    }

if __name__ == "__main__":
    print("Starting Test MCP Backend Server...")
    print("This server will be used to test the Word Add-in integration.")
    print("Available endpoints:")
    print("  - GET  /health")
    print("  - GET  /mcp/tools")
    print("  - POST /mcp/tools/execute")
    print("\nServer will start on http://localhost:8000")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
