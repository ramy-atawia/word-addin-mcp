"""
MCP API endpoints for tool discovery and execution.

This module provides REST API endpoints for MCP tools using the compliant
MCP hub implementation.
"""

import json
import logging
import os
import time
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ...services.mcp.orchestrator import get_initialized_mcp_orchestrator
# Removed old MCP schema imports - using official MCP types now
from ...schemas.agent import AgentChatRequest, AgentChatResponse
from ...services.agent import agent_service
from ...schemas.mcp import ExternalServerRequest

logger = logging.getLogger(__name__)

# Authentication is now handled by Azure API Management

router = APIRouter(prefix="/mcp", tags=["mcp"])

@router.get("/test-auth")
async def test_auth():
    """Test endpoint - authentication handled by APIM"""
    import time
    return {
        "message": "Endpoint accessible - authentication handled by Azure API Management",
        "timestamp": time.time(),
        "status": "ready"
    }


@router.post("/agent/chat", response_model=AgentChatResponse)
async def agent_chat(request: AgentChatRequest):
    """
    Process user message through the intelligent agent.
    
    This endpoint handles:
    - Intent detection using LLM
    - Routing decisions to appropriate tools
    - Tool execution when needed
    - Conversational responses
    - Conversation memory management
    
    Expected context format:
    {
        "document_content": "string - document text or empty",
        "chat_history": "string - previous conversation",
        "available_tools": "string - comma-separated tool names"
    }
    
    Args:
        request: Agent chat request with message and context
        
    Returns:
        Complete response with intent, routing, execution result, and metrics
    """
    try:
        logger.info(f"Processing chat request: '{request.message[:50]}...' ({len(request.message)} chars)")

        # Extract context information (all as strings)
        document_content = request.context.get("document_content", "")
        chat_history = request.context.get("chat_history", "")
        available_tools_string = request.context.get("available_tools", "")
        
        # Parse chat history from frontend
        parsed_chat_history = []
        if chat_history:
            try:
                parsed_chat_history = json.loads(chat_history)
                logger.debug(f"Parsed {len(parsed_chat_history)} messages from frontend chat history")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse chat history: {str(e)}")
                parsed_chat_history = []
        
        # Get available tools from MCP orchestrator (backend handles this dynamically)
        available_tools = []
        try:
            mcp_orchestrator = get_initialized_mcp_orchestrator()
            tools_data = await mcp_orchestrator.list_all_tools()
            available_tools = tools_data.get("tools", [])
            logger.debug(f"Retrieved {len(available_tools)} available tools")
        except Exception as e:
            logger.warning(f"Failed to get available tools: {str(e)}")
        
        # Process message through agent service with frontend chat history
        response = await agent_service.process_user_message(
            user_message=request.message,
            document_content=document_content,
            available_tools=available_tools,
            frontend_chat_history=parsed_chat_history
        )

        logger.info(f"Chat processed - intent: {response.get('intent_type')}, tool: {response.get('tool_name')}, time: {response.get('execution_time', 0):.2f}s")
        logger.debug(f"DEBUG: Agent response type: {type(response)}")
        logger.debug(f"DEBUG: Agent response keys: {response.keys() if isinstance(response, dict) else 'Not a dict'}")
        logger.debug(f"DEBUG: Agent response['response'] type: {type(response.get('response')) if isinstance(response, dict) else 'Not accessible'}")
        logger.debug(f"DEBUG: Agent response['response'] length: {len(response.get('response', '')) if isinstance(response, dict) and response.get('response') else 'None or empty'}")
        
        agent_chat_response = AgentChatResponse(**response)
        logger.debug(f"DEBUG: AgentChatResponse created successfully")
        
        return agent_chat_response
        
    except Exception as e:
        logger.error(f"Agent chat request failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": f"Failed to process agent chat request: {str(e)}"
            }
        )


class ToolExecutionRequest(BaseModel):
    """Request model for tool execution."""
    parameters: Dict[str, Any]
    server_id: Optional[str] = None


class ToolListResponse(BaseModel):
    """Response model for tool listing."""
    tools: List[Dict[str, Any]]
    total_count: int
    built_in_count: int
    external_count: int
    timestamp: float


@router.get("/tools", response_model=ToolListResponse)
async def list_available_tools():
    """
    List all available MCP tools from both built-in and external servers.
    
    Returns:
        List of all available tools with source information
    """
    try:
        logger.info("Listing all available MCP tools")
        
        mcp_orchestrator = get_initialized_mcp_orchestrator()
        tools_data = await mcp_orchestrator.list_all_tools()
        
        logger.info(f"Retrieved {tools_data['total_count']} total tools "
                   f"(built-in: {tools_data['built_in_count']}, "
                   f"external: {tools_data['external_count']})")
        
        return ToolListResponse(
            tools=tools_data["tools"],
            total_count=tools_data["total_count"],
            built_in_count=tools_data["built_in_count"],
            external_count=tools_data["external_count"],
            timestamp=tools_data["timestamp"]
        )
        
    except Exception as e:
        logger.error(f"Failed to list available tools: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )


@router.get("/tools/{tool_name}")
async def get_mcp_tool_info(tool_name: str):
    """
    Get information about a specific MCP tool.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        Tool information
    """
    try:
        logger.info(f"Getting MCP tool info for: {tool_name}")
        
        mcp_orchestrator = get_initialized_mcp_orchestrator()
        tool_info = await mcp_orchestrator.get_tool_info(tool_name)
        
        if not tool_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{tool_name}' not found"
            )
        
        logger.info(f"Retrieved tool info for: {tool_name}")
        return {
            "status": "success",
            "tool": tool_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tool info for '{tool_name}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )


@router.post("/tools/{tool_name}/execute")
async def execute_mcp_tool(tool_name: str, request: ToolExecutionRequest):
    """
    Execute an MCP tool.
    
    Args:
        tool_name: Name of the tool to execute
        request: Tool execution request
        
    Returns:
        Tool execution result
    """
    try:
        logger.info(f"Executing MCP tool '{tool_name}' with parameters: {request.parameters}")
        
        # Execute tool using the hub
        mcp_orchestrator = get_initialized_mcp_orchestrator()
        result = await mcp_orchestrator.execute_tool(
            tool_name=tool_name,
            parameters=request.parameters
        )
        
        logger.info(f"Tool '{tool_name}' executed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Failed to execute tool '{tool_name}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Tool Execution Error",
                "message": str(e),
                "tool_name": tool_name
            }
        )


@router.post("/proxy")
async def mcp_proxy(request: Request):
    """
    Proxy MCP requests to the internal MCP server.
    
    This endpoint allows external MCP clients to connect to the internal
    MCP server through the main backend, making it accessible from Azure.
    
    Args:
        request: Raw MCP JSON-RPC request
        
    Returns:
        MCP JSON-RPC response from internal server
    """
    try:
        import aiohttp
        
        # Get the request body
        body = await request.body()
        
        # Forward the request to the internal MCP server
        internal_mcp_url = os.getenv("INTERNAL_MCP_URL", "http://localhost:8001/mcp")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                internal_mcp_url,
                data=body,
                headers={"Content-Type": "application/json"}
            ) as response:
                response_data = await response.read()
                
                # Parse and return the response
                if response_data:
                    try:
                        response_json = json.loads(response_data.decode())
                        return JSONResponse(
                            content=response_json,
                            status_code=response.status
                        )
                    except json.JSONDecodeError:
                        return JSONResponse(
                            content={"error": "Invalid JSON response from internal server"},
                            status_code=500
                        )
                else:
                    return JSONResponse(
                        content={},
                        status_code=response.status
                    )
                
    except Exception as e:
        logger.error(f"MCP proxy error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                }
            }
        )


@router.get("/status")
async def get_mcp_orchestrator_status():
    """
    Get overall MCP orchestrator status and statistics.
    
    Returns:
        Orchestrator status and statistics
    """
    try:
        logger.info("Getting MCP hub status")
        
        mcp_orchestrator = get_initialized_mcp_orchestrator()
        orchestrator_status = await mcp_orchestrator.get_server_health()
        
        logger.info(f"MCP orchestrator status: {orchestrator_status['status']}")
        return orchestrator_status
        
    except Exception as e:
        logger.error(f"Failed to get MCP hub status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )


@router.get("/health")
async def get_health():
    """
    Get basic health status of the MCP service.
    
    Returns:
        Health status information
    """
    try:
        import time
        return {
            "status": "healthy",
            "service": "MCP Service",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Health Check Error",
                "message": str(e)
            }
        )

@router.get("/external/servers")
async def get_external_servers():
    """
    Get list of external MCP servers.
    
    Returns:
        List of external server information
    """
    try:
        logger.info("Getting external MCP servers list")
        
        mcp_orchestrator = get_initialized_mcp_orchestrator()
        servers = await mcp_orchestrator.get_external_servers()
        
        logger.info(f"Retrieved {len(servers)} external MCP servers")
        return {
            "status": "success",
            "servers": servers,
            "total_count": len(servers)
        }
        
    except Exception as e:
        logger.error(f"Failed to get external MCP servers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )


@router.get("/external/servers/health")
async def get_external_servers_health():
    """
    Get health status of all external MCP servers.
    
    Returns:
        Health status of all external servers
    """
    try:
        logger.info("Getting external MCP servers health status")
        
        mcp_orchestrator = get_initialized_mcp_orchestrator()
        health_status = await mcp_orchestrator.get_external_server_health()
        
        logger.info(f"Retrieved health status for {len(health_status)} external MCP servers")
        return {
            "status": "success",
            "servers": health_status,
            "total_count": len(health_status)
        }
        
    except Exception as e:
        logger.error(f"Failed to get external MCP servers health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )


@router.post("/external/servers")
async def add_external_server(request: ExternalServerRequest):
    """
    Add a new external MCP server.
    
    Args:
        request: External server request with frontend payload structure
        
    Returns:
        Server addition result
    """
    try:
        logger.info(f"Adding external MCP server: {request.name}")
        
        # Convert frontend payload to backend expected format
        config = request.to_backend_config()
        logger.info(f"Converted config: {config}")
        
        mcp_orchestrator = get_initialized_mcp_orchestrator()
        server_id = await mcp_orchestrator.add_external_server(config)
        
        logger.info(f"External MCP server added successfully with ID: {server_id}")
        return {
            "status": "success",
            "message": "External MCP server added successfully",
            "server_id": server_id
        }
        
    except Exception as e:
        logger.error(f"Failed to add external MCP server: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": f"Failed to add server: {str(e)}"
            }
        )


@router.delete("/external/servers/{server_id}")
async def remove_external_server(server_id: str):
    """
    Remove an external MCP server.
    
    Args:
        server_id: ID of the server to remove
        
    Returns:
        Removal result
    """
    try:
        logger.info(f"Removing external MCP server: {server_id}")
        
        mcp_orchestrator = get_initialized_mcp_orchestrator()
        success = await mcp_orchestrator.remove_external_server(server_id)
        
        if success:
            logger.info(f"External MCP server {server_id} removed successfully")
            return {
                "status": "success",
                "message": f"External MCP server {server_id} removed successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to remove external MCP server {server_id}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove external MCP server {server_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )


@router.post("/external/servers/{server_id}/test-connection")
async def test_external_server_connection(server_id: str):
    """
    Test connection to an external MCP server.
    
    Args:
        server_id: ID of the server to test
        
    Returns:
        Connection test result
    """
    try:
        logger.info(f"Testing connection to external MCP server: {server_id}")
        
        mcp_orchestrator = get_initialized_mcp_orchestrator()
        success = await mcp_orchestrator.test_external_server_connection(server_id)
        
        if success:
            logger.info(f"Connection test successful for external MCP server {server_id}")
            return {
                "status": "success",
                "message": "Connection test successful",
                "server_id": server_id,
                "connected": True
            }
        else:
            logger.warning(f"Connection test failed for external MCP server {server_id}")
            return {
                "status": "error",
                "message": "Connection test failed",
                "server_id": server_id,
                "connected": False
            }
        
    except Exception as e:
        logger.error(f"Failed to test connection to external MCP server {server_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )

