"""
Internal MCP Server as separate FastAPI app.

Runs on port 8001, providing MCP protocol compliance for internal tools.
"""

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import structlog

from .mcp_servers.tools.web_search import WebSearchTool
from .mcp_servers.tools.prior_art_search import PriorArtSearchTool
from .mcp_servers.tools.claim_drafting import ClaimDraftingTool
from .mcp_servers.tools.claim_analysis import ClaimAnalysisTool
from .mcp_servers.tools.document_modification_tool import DocumentModificationTool

logger = structlog.get_logger()

# ============================================================================
# FastAPI App Configuration
# ============================================================================

app = FastAPI(
    title="Internal MCP Server",
    description="Internal MCP server hosting all internal tools",
    version="1.0.0"
)

# ============================================================================
# Tool Registry
# ============================================================================

tools = {
    "web_search_tool": WebSearchTool(),
    "prior_art_search_tool": PriorArtSearchTool(),
    "claim_drafting_tool": ClaimDraftingTool(),
    "claim_analysis_tool": ClaimAnalysisTool(),
    "document_modification_tool": DocumentModificationTool()
}

# ============================================================================
# Helper Functions
# ============================================================================

def _validate_jsonrpc(body: dict) -> tuple[bool, dict]:
    """Validate JSON-RPC 2.0 structure."""
    if not isinstance(body, dict) or "jsonrpc" not in body:
        return False, {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32600, "message": "Invalid JSON-RPC request"}
        }
    
    if body.get("jsonrpc") != "2.0":
        return False, {
            "jsonrpc": "2.0",
            "id": body.get("id", 1),
            "error": {"code": -32600, "message": "Invalid JSON-RPC version"}
        }
    
    return True, {}


def _error_response(request_id: int, code: int, message: str) -> dict:
    """Create error response."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message}
    }


def _success_response(request_id: int, result: dict) -> dict:
    """Create success response."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result
    }


# ============================================================================
# MCP Endpoint
# ============================================================================

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Handle MCP protocol requests."""
    try:
        # Validate content type
        content_type = request.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            return JSONResponse(
                _error_response(1, -32600, "Invalid content type. Expected application/json"),
                status_code=400
            )
        
        body = await request.json()
        
        # Validate JSON-RPC structure
        is_valid, error_response = _validate_jsonrpc(body)
        if not is_valid:
            return JSONResponse(error_response)
        
        method = body.get("method")
        request_id = body.get("id")
        params = body.get("params", {})
        
        # Handle notifications (no response needed)
        if request_id is None:
            if method == "notifications/initialized":
                logger.info("Client initialized notification received")
            else:
                logger.warning(f"Unknown notification method: {method}")
            return JSONResponse({}, status_code=204)
        
        # Handle initialize
        if method == "initialize":
            client_info = params.get("clientInfo", {})
            logger.info(f"Initializing MCP connection with client: {client_info.get('name', 'Unknown')}")
            
            return JSONResponse(_success_response(request_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"subscribe": False, "listChanged": False},
                    "prompts": {"listChanged": False},
                    "logging": {}
                },
                "serverInfo": {
                    "name": "Internal MCP Server",
                    "version": "1.0.0"
                }
            }))
        
        # Handle tools/list
        elif method == "tools/list":
            tools_list = [tool.get_schema() for tool in tools.values()]
            return JSONResponse(_success_response(request_id, {"tools": tools_list}))
        
        # Handle tools/call
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name not in tools:
                return JSONResponse(_error_response(
                    request_id, -32601, f"Tool '{tool_name}' not found"
                ))
            
            try:
                result = await tools[tool_name].execute(arguments)
                return JSONResponse(_success_response(request_id, {
                    "content": [{"type": "text", "text": str(result)}],
                    "isError": False
                }))
            except Exception as e:
                logger.error(f"Tool execution failed: {tool_name} - {e}")
                return JSONResponse(_success_response(request_id, {
                    "content": [{"type": "text", "text": f"Error executing tool: {str(e)}"}],
                    "isError": True
                }))
        
        # Handle resources/list
        elif method == "resources/list":
            return JSONResponse(_success_response(request_id, {"resources": []}))
        
        # Handle resources/read
        elif method == "resources/read":
            return JSONResponse(_error_response(
                request_id, -32601, "Resources not supported"
            ))
        
        # Handle prompts/list
        elif method == "prompts/list":
            return JSONResponse(_success_response(request_id, {"prompts": []}))
        
        # Handle prompts/get
        elif method == "prompts/get":
            return JSONResponse(_error_response(
                request_id, -32601, "Prompts not supported"
            ))
        
        # Handle logging/setLevel
        elif method == "logging/setLevel":
            level = params.get("level", "info")
            logger.info(f"Log level set to: {level}")
            return JSONResponse(_success_response(request_id, {}))
        
        # Method not found
        else:
            return JSONResponse(_error_response(
                request_id, -32601, f"Method '{method}' not found"
            ))
            
    except Exception as e:
        logger.error(f"MCP endpoint error: {e}")
        return JSONResponse(_error_response(1, -32603, str(e)))


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check for internal MCP server."""
    return {
        "status": "healthy",
        "server": "Internal MCP Server",
        "tools_count": len(tools),
        "tools": list(tools.keys())
    }


# ============================================================================
# Lifecycle Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Startup event for internal MCP server."""
    logger.info("Internal MCP Server starting up...")
    logger.info(f"Registered {len(tools)} tools: {list(tools.keys())}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event for internal MCP server."""
    logger.info("Internal MCP Server shutting down...")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)