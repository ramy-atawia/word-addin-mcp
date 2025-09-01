"""
External MCP Server Management API endpoints.

This module provides REST API endpoints for managing external MCP servers
using the compliant MCP client implementation.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

# Removed old MCP schema import - defining locally
from ...core.mcp_client import MCPConnectionError, MCPToolError
from ...services.mcp.orchestrator import mcp_orchestrator
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/external", tags=["external-mcp"])

# Use the MCP orchestrator directly

class ExternalMCPServerConfig(BaseModel):
    """Configuration for external MCP server."""
    name: str
    description: str
    server_url: str
    server_type: str = "MCP"
    authentication_type: str = "NONE"
    api_key: Optional[str] = None
    oauth_token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 30
    health_check_interval: int = 60
    max_retries: int = 3
    retry_delay: int = 5


class AddServerRequest(BaseModel):
    """Request model for adding an external MCP server."""
    name: str
    description: str
    server_url: str
    server_type: str = "MCP"
    authentication_type: str = "NONE"
    api_key: Optional[str] = None
    oauth_token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 30
    health_check_interval: int = 60
    max_retries: int = 3
    retry_delay: int = 5


class AddServerResponse(BaseModel):
    """Response model for adding an external MCP server."""
    status: str
    message: str
    server_id: str
    server_info: Dict[str, Any]


class ServerInfoResponse(BaseModel):
    """Response model for server information."""
    server_id: str
    name: str
    description: str
    server_url: str
    status: str
    tools_count: int
    last_request: Optional[str] = None
    total_requests: int
    avg_response_time: float
    protocol_version: Optional[str] = None
    server_capabilities: Optional[Dict[str, Any]] = None


class HealthStatusResponse(BaseModel):
    """Response model for server health status."""
    server_id: str
    name: str
    status: str
    last_check: str
    tools_count: int
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    uptime: Optional[str] = None


@router.post("/servers", response_model=AddServerResponse, status_code=status.HTTP_201_CREATED)
async def add_external_server(request: AddServerRequest):
    """
    Add a new external MCP server.
    
    Args:
        request: Server configuration
        
    Returns:
        Server addition result with server ID and info
    """
    try:
        logger.info(f"Adding external MCP server: {request.name}")
        
        # Convert request to ExternalMCPServerConfig
        config = ExternalMCPServerConfig(
            name=request.name,
            description=request.description,
            server_url=request.server_url,
            server_type=request.server_type,
            authentication_type=request.authentication_type,
            api_key=request.api_key,
            oauth_token=request.oauth_token,
            username=request.username,
            password=request.password,
            timeout=request.timeout,
            health_check_interval=request.health_check_interval,
            max_retries=request.max_retries,
            retry_delay=request.retry_delay
        )
        
        # Add server using the orchestrator
        server_id = await mcp_orchestrator.add_external_server({
            "name": request.name,
            "url": request.server_url,
            "type": "external",
            "metadata": {
                "description": request.description,
                "server_type": request.server_type,
                "authentication_type": request.authentication_type,
                "api_key": request.api_key,
                "oauth_token": request.oauth_token,
                "username": request.username,
                "password": request.password,
                "timeout": request.timeout,
                "health_check_interval": request.health_check_interval,
                "max_retries": request.max_retries,
                "retry_delay": request.retry_delay
            }
        })
        
        # Get server info for response
        servers = await mcp_orchestrator.get_external_servers()
        server = next((s for s in servers if s["server_id"] == server_id), None)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server was added but could not be retrieved"
            )
        
        server_info = server
        
        logger.info(f"External MCP server '{request.name}' added successfully with ID: {server_id}")
        
        return AddServerResponse(
            status="success",
            message=f"External MCP server '{request.name}' added successfully",
            server_id=server_id,
            server_info=server_info
        )
        
    except MCPConnectionError as e:
        logger.error(f"Connection error adding external MCP server: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Connection Error",
                "message": str(e),
                "server_url": request.server_url
            }
        )
    except Exception as e:
        logger.error(f"Failed to add external MCP server: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )


@router.post("/servers/test-connection")
async def test_external_server_connection(request: AddServerRequest):
    """
    Test connection to external MCP server before adding it.
    
    Args:
        request: Server configuration to test
        
    Returns:
        Connection test result
    """
    try:
        logger.info(f"Testing connection to external MCP server: {request.name}")
        
        # Test basic HTTP connectivity first
        try:
            import aiohttp
            
            # Test basic HTTP connectivity
            timeout = aiohttp.ClientTimeout(total=request.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(request.server_url) as response:
                    if response.status == 200:
                        return {
                            "connection_test": "http_successful",
                            "server_url": request.server_url,
                            "server_name": request.name,
                            "timestamp": datetime.now().isoformat(),
                            "message": "HTTP connectivity successful - server is reachable"
                        }
                    else:
                        return {
                            "connection_test": "http_failed",
                            "server_url": request.server_url,
                            "server_name": request.name,
                            "timestamp": datetime.now().isoformat(),
                            "message": f"HTTP connectivity failed - status {response.status}"
                        }
                        
        except Exception as e:
            logger.error(f"HTTP connectivity test failed: {str(e)}")
            return {
                "connection_test": "http_failed",
                "server_url": request.server_url,
                "server_name": request.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Failed to test external MCP server connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )


@router.get("/servers", response_model=List[ServerInfoResponse])
async def list_external_servers():
    """
    List all external MCP servers.
    
    Returns:
        List of external server information
    """
    try:
        logger.info("Listing external MCP servers")
        
        servers = await mcp_orchestrator.get_external_servers()
        
        # Convert to response format
        server_responses = []
        for server in servers:
            # The server info is already in the right format
            server_responses.append(ServerInfoResponse(**server))
        
        logger.info(f"Retrieved {len(server_responses)} external MCP servers")
        return server_responses
        
    except Exception as e:
        logger.error(f"Failed to list external MCP servers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )


@router.get("/servers/{server_id}", response_model=ServerInfoResponse)
async def get_external_server(server_id: str):
    """
    Get information about a specific external MCP server.
    
    Args:
        server_id: ID of the server
        
    Returns:
        Server information
    """
    try:
        logger.info(f"Getting external MCP server info: {server_id}")
        
        servers = await mcp_orchestrator.get_external_servers()
        server = next((s for s in servers if s["server_id"] == server_id), None)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"External MCP server with ID '{server_id}' not found"
            )
        
        return ServerInfoResponse(**server)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get external MCP server {server_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )


@router.delete("/servers/{server_id}")
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


@router.get("/servers/{server_id}/tools")
async def list_server_tools(server_id: str):
    """
    List tools available on a specific external MCP server.
    
    Args:
        server_id: ID of the server
        
    Returns:
        List of available tools
    """
    try:
        logger.info(f"Listing tools for external MCP server: {server_id}")
        
        # Get tools from the orchestrator
        all_tools = await mcp_orchestrator.list_all_tools()
        server_tools = [tool for tool in all_tools["tools"] if tool.get("server_id") == server_id]
        
        if not server_tools:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"External MCP server with ID '{server_id}' not found or has no tools"
            )
        
        logger.info(f"Found {len(server_tools)} tools on external MCP server {server_id}")
        return {
            "server_id": server_id,
            "server_name": server_tools[0].get("server_name", "Unknown"),
            "tools": server_tools,
            "total_count": len(server_tools)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list tools for external MCP server {server_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )


@router.post("/servers/{server_id}/tools/{tool_name}/execute")
async def execute_server_tool(server_id: str, tool_name: str, parameters: Dict[str, Any]):
    """
    Execute a tool on a specific external MCP server.
    
    Args:
        server_id: ID of the server
        tool_name: Name of the tool to execute
        parameters: Tool execution parameters
        
    Returns:
        Tool execution result
    """
    try:
        logger.info(f"Executing tool '{tool_name}' on external MCP server: {server_id}")
        
        # Execute tool through the orchestrator
        result = await mcp_orchestrator.execute_tool(tool_name, parameters)
        
        logger.info(f"Tool '{tool_name}' executed successfully on external MCP server {server_id}")
        return result
        
    except MCPToolError as e:
        logger.error(f"Tool execution error on external MCP server {server_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Tool Execution Error",
                "message": str(e),
                "server_id": server_id,
                "tool_name": tool_name
            }
        )
    except Exception as e:
        logger.error(f"Failed to execute tool '{tool_name}' on external MCP server {server_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )


@router.get("/servers/{server_id}/health", response_model=HealthStatusResponse)
async def get_server_health(server_id: str):
    """
    Get health status of a specific external MCP server.
    
    Args:
        server_id: ID of the server
        
    Returns:
        Server health status
    """
    try:
        logger.info(f"Getting health status for external MCP server: {server_id}")
        
        # Get server health from orchestrator
        external_health = await mcp_orchestrator.get_external_server_health()
        server_health = external_health.get("external_servers", {}).get(server_id)
        
        if not server_health:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"External MCP server with ID '{server_id}' not found"
            )
        
        # Test connection
        connection_test = await mcp_orchestrator.test_external_server_connection(server_id)
        is_healthy = connection_test.get("success", False)
        
        health_status = HealthStatusResponse(
            server_id=server_id,
            name=server_health.get("server_name", "Unknown"),
            status="connected" if is_healthy else "disconnected",
            last_check=datetime.now().isoformat(),
            tools_count=0,  # Will need to implement tool counting
            response_time=None,
            error_message=None if is_healthy else "Connection test failed",
            uptime=None  # Not implemented in current version
        )
        
        return health_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get health status for external MCP server {server_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )


@router.post("/servers/{server_id}/test-connection")
async def test_server_connection(server_id: str):
    """
    Test connection to a specific external MCP server.
    
    Args:
        server_id: ID of the server
        
    Returns:
        Connection test result
    """
    try:
        logger.info(f"Testing connection to external MCP server: {server_id}")
        
        # Test connection using orchestrator
        connection_test = await mcp_orchestrator.test_external_server_connection(server_id)
        is_connected = connection_test.get("success", False)
        
        if is_connected:
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test connection to external MCP server {server_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )


@router.post("/servers/refresh")
async def refresh_all_connections():
    """
    Refresh connections to all external MCP servers.
    
    Returns:
        Refresh result
    """
    try:
        logger.info("Refreshing all external MCP server connections")
        
        # Get all servers from orchestrator
        servers = await mcp_orchestrator.get_external_servers()
        
        refresh_results = []
        for server in servers:
            try:
                # Test connection
                connection_test = await mcp_orchestrator.test_external_server_connection(server["server_id"])
                is_connected = connection_test.get("success", False)
                refresh_results.append({
                    "server_id": server["server_id"],
                    "name": server["name"],
                    "status": "connected" if is_connected else "disconnected",
                    "success": is_connected
                })
            except Exception as e:
                logger.error(f"Failed to refresh connection for server {server['server_id']}: {str(e)}")
                refresh_results.append({
                    "server_id": server["server_id"],
                    "name": server["name"],
                    "status": "error",
                    "success": False,
                    "error": str(e)
                })
        
        logger.info(f"Refreshed connections for {len(servers)} external MCP servers")
        return {
            "status": "success",
            "message": f"Refreshed connections for {len(servers)} external MCP servers",
            "results": refresh_results
        }
        
    except Exception as e:
        logger.error(f"Failed to refresh external MCP server connections: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )


@router.get("/health")
async def get_all_servers_health():
    """
    Get health status of all external MCP servers.
    
    Returns:
        Health status of all servers
    """
    try:
        logger.info("Getting health status for all external MCP servers")
        
        health_status = await mcp_orchestrator.get_external_server_health()
        
        logger.info(f"Retrieved health status for {len(health_status)} external MCP servers")
        return {
            "status": "success",
            "total_servers": len(health_status),
            "servers": health_status
        }
        
    except Exception as e:
        logger.error(f"Failed to get health status for all external MCP servers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )


@router.post("/servers/{server_id}/refresh-tools")
async def refresh_server_tools(server_id: str):
    """
    Manually refresh tools from a specific external MCP server.
    
    Args:
        server_id: ID of the server
        
    Returns:
        Tool refresh result
    """
    try:
        logger.info(f"Manually refreshing tools for external MCP server: {server_id}")
        
        # Force tool discovery through orchestrator
        logger.info(f"Starting manual tool discovery for server: {server_id}")
        
        # Get all tools and filter by server
        all_tools = await mcp_orchestrator.list_all_tools()
        server_tools = [tool for tool in all_tools["tools"] if tool.get("server_id") == server_id]
        
        if not server_tools:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"External MCP server with ID '{server_id}' not found or has no tools"
            )
        
        logger.info(f"Manual tool discovery completed: {len(server_tools)} tools found")
        return {
            "status": "success",
            "message": f"Tools refreshed successfully. Found {len(server_tools)} tools.",
            "server_id": server_id,
            "server_name": server_tools[0].get("server_name", "Unknown"),
            "tools_count": len(server_tools),
            "tools": server_tools
        }
        
    except Exception as e:
        logger.error(f"Failed to refresh tools for external MCP server {server_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )
