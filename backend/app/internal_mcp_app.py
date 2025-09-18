"""
Internal MCP Server as separate FastAPI app.

This app runs the internal MCP server on port 8001 using FastMCP,
providing true MCP protocol compliance for internal tools.
"""

import asyncio
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
import structlog

from .mcp_servers.tools.web_search import WebSearchTool
from .mcp_servers.tools.prior_art_search import PriorArtSearchTool
from .mcp_servers.tools.claim_drafting import ClaimDraftingTool
from .mcp_servers.tools.claim_analysis import ClaimAnalysisTool

logger = structlog.get_logger()

# Create FastAPI app for internal MCP server
app = FastAPI(
    title="Internal MCP Server",
    description="Internal MCP server hosting all internal tools",
    version="1.0.0"
)

# Initialize tools
tools = {
    "web_search_tool": WebSearchTool(),
    "prior_art_search_tool": PriorArtSearchTool(),
    "claim_drafting_tool": ClaimDraftingTool(),
    "claim_analysis_tool": ClaimAnalysisTool()
}

# MCP endpoint
@app.post("/")
async def mcp_endpoint(request: Request):
    """Handle MCP protocol requests."""
    try:
        # Validate MCP content type
        content_type = request.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": 1,
                "error": {
                    "code": -32600,
                    "message": "Invalid content type. Expected application/json"
                }
            }, status_code=400)
        
        body = await request.json()
        
        # Validate JSON-RPC 2.0 structure
        if not isinstance(body, dict) or "jsonrpc" not in body:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": 1,
                "error": {
                    "code": -32600,
                    "message": "Invalid JSON-RPC request"
                }
            })
        
        if body.get("jsonrpc") != "2.0":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": body.get("id", 1),
                "error": {
                    "code": -32600,
                    "message": "Invalid JSON-RPC version"
                }
            })
        
        method = body.get("method")
        request_id = body.get("id")
        
        # Handle notifications (no response needed)
        if request_id is None:
            if method == "notifications/initialized":
                logger.info("Client initialized notification received")
                return JSONResponse({}, status_code=204)  # No content for notifications
            else:
                logger.warning(f"Unknown notification method: {method}")
                return JSONResponse({}, status_code=204)
        
        if method == "initialize":
            # Get client capabilities from request
            params = body.get("params", {})
            client_capabilities = params.get("capabilities", {})
            client_info = params.get("clientInfo", {})
            
            logger.info(f"Initializing MCP connection with client: {client_info.get('name', 'Unknown')}")
            
            # Return server capabilities based on what we support
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {
                            "listChanged": False  # We don't support dynamic tool changes
                        },
                        "resources": {
                            "subscribe": False,
                            "listChanged": False
                        },
                        "prompts": {
                            "listChanged": False
                        },
                        "logging": {}
                    },
                    "serverInfo": {
                        "name": "Internal MCP Server",
                        "version": "1.0.0"
                    }
                }
            })
        elif method == "tools/list":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                    {
                        "name": "web_search_tool",
                        "description": "Search the web for information",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query"
                                },
                                "max_results": {
                                    "type": "integer",
                                    "description": "Maximum number of results to return",
                                    "default": 10
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "prior_art_search_tool",
                        "description": "Search for prior art and patents",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query for prior art"
                                },
                                "max_results": {
                                    "type": "integer",
                                    "description": "Maximum number of results to return",
                                    "default": 10
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "claim_drafting_tool",
                        "description": "Draft patent claims based on input",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "user_query": {
                                    "type": "string",
                                    "description": "User query describing what claims to draft",
                                    "minLength": 3,
                                    "maxLength": 1000
                                },
                                "conversation_context": {
                                    "type": "string",
                                    "description": "Additional context from conversation history",
                                    "maxLength": 5000
                                },
                                "document_reference": {
                                    "type": "string",
                                    "description": "Reference to existing document content",
                                    "maxLength": 10000
                                }
                            },
                            "required": ["user_query"]
                        }
                    },
                    {
                        "name": "claim_analysis_tool",
                        "description": "Analyze patent claims for quality and structure",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "claims": {
                                    "type": "array",
                                    "description": "List of patent claims to analyze",
                                    "minItems": 1,
                                    "maxItems": 50,
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "claim_number": {"type": "string"},
                                            "claim_text": {"type": "string"},
                                            "claim_type": {"type": "string", "enum": ["independent", "dependent"]},
                                            "dependency": {"type": "string"},
                                            "technical_focus": {"type": "string"}
                                        },
                                        "required": ["claim_text"]
                                    }
                                },
                                "analysis_type": {
                                    "type": "string",
                                    "description": "Type of analysis to perform",
                                    "enum": ["basic", "comprehensive", "expert"],
                                    "default": "comprehensive"
                                },
                                "focus_areas": {
                                    "type": "array",
                                    "description": "Specific areas to focus analysis on",
                                    "items": {"type": "string"},
                                    "default": []
                                }
                            },
                            "required": ["claims"]
                        }
                    }
                ]
            }
            })
        elif method == "tools/call":
            params = body.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            # Execute the tool
            if tool_name in tools:
                try:
                    result = await tools[tool_name].execute(arguments)
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": str(result)
                                }
                            ],
                            "isError": False
                        }
                    })
                except Exception as e:
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Error executing tool: {str(e)}"
                                }
                            ],
                            "isError": True
                        }
                    })
            else:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool '{tool_name}' not found"
                    }
                })
        elif method == "resources/list":
            # MCP Resources - return empty list for now
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "resources": []
                }
            })
        elif method == "resources/read":
            # MCP Resources - not implemented
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": "Resources not supported"
                }
            })
        elif method == "prompts/list":
            # MCP Prompts - return empty list for now
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "prompts": []
                }
            })
        elif method == "prompts/get":
            # MCP Prompts - not implemented
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": "Prompts not supported"
                }
            })
        elif method == "logging/setLevel":
            # MCP Logging - basic implementation
            params = body.get("params", {})
            level = params.get("level", "info")
            logger.info(f"Log level set to: {level}")
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {}
            })
        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method '{method}' not found"
                }
            })
            
    except Exception as e:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        })

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check for internal MCP server."""
    return {
        "status": "healthy",
        "server": "Internal MCP Server",
        "tools_count": len(tools),
        "tools": list(tools.keys())
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup event for internal MCP server."""
    logger.info("Internal MCP Server starting up...")
    logger.info(f"Registered {len(tools)} tools: {list(tools.keys())}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event for internal MCP server."""
    logger.info("Internal MCP Server shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
