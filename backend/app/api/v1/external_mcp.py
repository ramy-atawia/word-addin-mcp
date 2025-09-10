"""
External MCP Server Management API endpoints - Fixed Version.

This module provides REST API endpoints for managing external MCP servers
using the corrected MCP client implementation and proper error handling.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ...core.fastmcp_client import MCPConnectionError, MCPToolError
from ...services.mcp.orchestrator import mcp_orchestrator
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/external", tags=["external-mcp"])


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
    timeout: float = 30.0  # Changed to float for consistency
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
    timeout: float = 30.0  # Changed to float for consistency
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


class ConnectionTestRequest(BaseModel):
    """Request model for testing connections."""
    name: str
    server_url: str
    timeout: float = 10.0


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
        
        # Test connection first using the corrected client
        try:
            from ...core.fastmcp_client import FastMCPClientFactory
            
            # Create appropriate client based on URL
            client = None
            if request.server_url.startswith(('http://', 'https://')):
                client = FastMCPClientFactory.create_http_client(
                    request.server_url, 
                    request.name, 
                    timeout=request.timeout
                )
            else:
                # Assume STDIO command
                server_command = request.server_url.split()
                client = FastMCPClientFactory.create_stdio_client(
                    server_command, 
                    request.name, 
                    timeout=request.timeout
                )
            
            # Test connection
            async with client:
                await client.health_check()
                tools = await client.list_tools()
                logger.info(f"Connection test successful. Found {len(tools)} tools.")
                
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            raise MCPConnectionError(f"Failed to connect to server: {e}")
        
        # Add server using the orchestrator with proper configuration
        server_config = {
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
        }
        
        server_id = await mcp_orchestrator.add_external_server(server_config)
        
        # Get server info for response
        servers = await mcp_orchestrator.get_external_servers()
        server = next((s for s in servers if s.get("server_id") == server_id), None)
        
        if not server:
            # Create basic server info if not found in orchestrator response
            server = {
                "server_id": server_id,
                "name": request.name,
                "description": request.description,
                "server_url": request.server_url,
                "status": "connected",
                "tools_count": len(tools) if 'tools' in locals() else 0,
                "total_requests": 0,
                "avg_response_time": 0.0
            }
        
        logger.info(f"External MCP server '{request.name}' added successfully with ID: {server_id}")
        
        return AddServerResponse(
            status="success",
            message=f"External MCP server '{request.name}' added successfully",
            server_id=server_id,
            server_info=server
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
async def test_external_server_connection(request: ConnectionTestRequest):
    """
    Test connection to external MCP server before adding it.
    
    Args:
        request: Server configuration to test
        
    Returns:
        Connection test result
    """
    try:
        logger.info(f"Testing connection to external MCP server: {request.name}")
        
        # Use the same corrected FastMCP client implementation as add_external_server
        from ...core.fastmcp_client import FastMCPClient, MCPConnectionConfig
        
        # Create client configuration (same as add_external_server)
        config = MCPConnectionConfig(
            server_url=request.server_url,
            server_name=request.name,
            timeout=request.timeout
        )
        
        # Create client
        client = FastMCPClient(config)
        
        try:
            
            # Test connection using the corrected client
            start_time = datetime.now()
            async with client:
                # Perform health check and get tools
                await client.health_check()
                
                # Try to list tools to verify full functionality
                try:
                    tools = await client.list_tools()
                    tools_count = len(tools)
                except Exception as tool_error:
                    logger.warning(f"Tool listing failed but connection is healthy: {tool_error}")
                    tools_count = 0
                
                # Try to list resources if available
                resources_count = 0
                try:
                    resources = await client.list_resources()
                    resources_count = len(resources)
                except Exception:
                    # Resources might not be supported, that's okay
                    pass
                
                response_time = (datetime.now() - start_time).total_seconds()
                
                return {
                    "connection_test": "mcp_successful",
                    "server_url": request.server_url,
                    "server_name": request.name,
                    "timestamp": datetime.now().isoformat(),
                    "response_time_seconds": response_time,
                    "tools_count": tools_count,
                    "resources_count": resources_count,
                    "success": True,
                    "message": f"MCP connection successful. Found {tools_count} tools and {resources_count} resources."
                }
                
        except MCPConnectionError as e:
            return {
                "connection_test": "mcp_connection_failed",
                "server_url": request.server_url,
                "server_name": request.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "message": f"MCP connection failed: {str(e)}"
            }
        except MCPToolError as e:
            return {
                "connection_test": "mcp_tool_error",
                "server_url": request.server_url,
                "server_name": request.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "message": f"MCP tool error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"MCP connection test failed: {str(e)}")
            return {
                "connection_test": "mcp_failed",
                "server_url": request.server_url,
                "server_name": request.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "message": f"Connection test failed: {str(e)}"
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
        
        # Convert to response format and ensure proper structure
        server_responses = []
        for server in servers:
            # Ensure all required fields are present with defaults
            server_info = ServerInfoResponse(
                server_id=server.get("server_id", ""),
                name=server.get("name", "Unknown"),
                description=server.get("description", ""),
                server_url=server.get("server_url", ""),
                status=server.get("status", "unknown"),
                tools_count=server.get("tools_count", 0),
                last_request=server.get("last_request"),
                total_requests=server.get("total_requests", 0),
                avg_response_time=server.get("avg_response_time", 0.0),
                protocol_version=server.get("protocol_version"),
                server_capabilities=server.get("server_capabilities")
            )
            server_responses.append(server_info)
        
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
        server = next((s for s in servers if s.get("server_id") == server_id), None)
        
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"External MCP server with ID '{server_id}' not found"
            )
        
        # Ensure all required fields are present
        server_info = ServerInfoResponse(
            server_id=server.get("server_id", server_id),
            name=server.get("name", "Unknown"),
            description=server.get("description", ""),
            server_url=server.get("server_url", ""),
            status=server.get("status", "unknown"),
            tools_count=server.get("tools_count", 0),
            last_request=server.get("last_request"),
            total_requests=server.get("total_requests", 0),
            avg_response_time=server.get("avg_response_time", 0.0),
            protocol_version=server.get("protocol_version"),
            server_capabilities=server.get("server_capabilities")
        )
        
        return server_info
        
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
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"External MCP server {server_id} not found or could not be removed"
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
        server_tools = [
            tool for tool in all_tools.get("tools", []) 
            if tool.get("server_id") == server_id
        ]
        
        if not server_tools:
            # Check if server exists first
            servers = await mcp_orchestrator.get_external_servers()
            server = next((s for s in servers if s.get("server_id") == server_id), None)
            
            if not server:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"External MCP server with ID '{server_id}' not found"
                )
            
            # Server exists but has no tools
            return {
                "server_id": server_id,
                "server_name": server.get("name", "Unknown"),
                "tools": [],
                "total_count": 0
            }
        
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
        
        # Verify server exists
        servers = await mcp_orchestrator.get_external_servers()
        server = next((s for s in servers if s.get("server_id") == server_id), None)
        
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"External MCP server with ID '{server_id}' not found"
            )
        
        # Execute tool through the orchestrator
        result = await mcp_orchestrator.execute_tool(tool_name, parameters)
        
        logger.info(f"Tool '{tool_name}' executed successfully on external MCP server {server_id}")
        return result
        
    except HTTPException:
        raise
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
        
        # Verify server exists
        servers = await mcp_orchestrator.get_external_servers()
        server = next((s for s in servers if s.get("server_id") == server_id), None)
        
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"External MCP server with ID '{server_id}' not found"
            )
        
        # Test connection using the corrected FastMCP client
        from ...core.fastmcp_client import FastMCPClientFactory
        
        try:
            # Create appropriate client
            client = None
            server_url = server.get("server_url", "")
            
            if server_url.startswith(('http://', 'https://')):
                client = FastMCPClientFactory.create_http_client(
                    server_url, 
                    server.get("name", "Unknown"), 
                    timeout=10.0
                )
            else:
                server_command = server_url.split()
                client = FastMCPClientFactory.create_stdio_client(
                    server_command, 
                    server.get("name", "Unknown"), 
                    timeout=10.0
                )
            
            # Test connection
            start_time = datetime.now()
            async with client:
                is_healthy = await client.health_check()
                response_time = (datetime.now() - start_time).total_seconds()
                
                # Get tool count
                try:
                    tools = await client.list_tools()
                    tools_count = len(tools)
                except Exception:
                    tools_count = 0
                
                health_status = HealthStatusResponse(
                    server_id=server_id,
                    name=server.get("name", "Unknown"),
                    status="healthy" if is_healthy else "unhealthy",
                    last_check=datetime.now().isoformat(),
                    tools_count=tools_count,
                    response_time=response_time,
                    error_message=None if is_healthy else "Health check failed",
                    uptime=None  # Not implemented yet
                )
                
                return health_status
                
        except Exception as e:
            logger.error(f"Health check failed for server {server_id}: {e}")
            
            health_status = HealthStatusResponse(
                server_id=server_id,
                name=server.get("name", "Unknown"),
                status="unhealthy",
                last_check=datetime.now().isoformat(),
                tools_count=0,
                response_time=None,
                error_message=str(e),
                uptime=None
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
        
        # Get server info
        servers = await mcp_orchestrator.get_external_servers()
        server = next((s for s in servers if s.get("server_id") == server_id), None)
        
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"External MCP server with ID '{server_id}' not found"
            )
        
        # Test connection using the corrected FastMCP client
        from ...core.fastmcp_client import FastMCPClientFactory
        
        try:
            # Create appropriate client
            client = None
            server_url = server.get("server_url", "")
            
            if server_url.startswith(('http://', 'https://')):
                client = FastMCPClientFactory.create_http_client(
                    server_url, 
                    server.get("name", "Unknown"), 
                    timeout=10.0
                )
            else:
                server_command = server_url.split()
                client = FastMCPClientFactory.create_stdio_client(
                    server_command, 
                    server.get("name", "Unknown"), 
                    timeout=10.0
                )
            
            # Test connection
            start_time = datetime.now()
            async with client:
                is_connected = await client.health_check()
                response_time = (datetime.now() - start_time).total_seconds()
                
                if is_connected:
                    logger.info(f"Connection test successful for external MCP server {server_id}")
                    return {
                        "status": "success",
                        "message": "Connection test successful",
                        "server_id": server_id,
                        "server_name": server.get("name", "Unknown"),
                        "connected": True,
                        "response_time_seconds": response_time,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    logger.warning(f"Connection test failed for external MCP server {server_id}")
                    return {
                        "status": "error",
                        "message": "Connection test failed - health check returned false",
                        "server_id": server_id,
                        "server_name": server.get("name", "Unknown"),
                        "connected": False,
                        "response_time_seconds": response_time,
                        "timestamp": datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"Connection test exception for server {server_id}: {e}")
            return {
                "status": "error",
                "message": f"Connection test failed with exception: {str(e)}",
                "server_id": server_id,
                "server_name": server.get("name", "Unknown"),
                "connected": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
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
            server_id = server.get("server_id", "")
            server_name = server.get("name", "Unknown")
            
            try:
                # Test connection for each server
                connection_result = await test_server_connection(server_id)
                
                if isinstance(connection_result, dict):
                    refresh_results.append({
                        "server_id": server_id,
                        "name": server_name,
                        "status": "connected" if connection_result.get("connected", False) else "disconnected",
                        "success": connection_result.get("connected", False),
                        "response_time": connection_result.get("response_time_seconds"),
                        "error": connection_result.get("error")
                    })
                else:
                    refresh_results.append({
                        "server_id": server_id,
                        "name": server_name,
                        "status": "error",
                        "success": False,
                        "error": "Unexpected response format"
                    })
                    
            except Exception as e:
                logger.error(f"Failed to refresh connection for server {server_id}: {str(e)}")
                refresh_results.append({
                    "server_id": server_id,
                    "name": server_name,
                    "status": "error",
                    "success": False,
                    "error": str(e)
                })
        
        successful_connections = sum(1 for result in refresh_results if result.get("success", False))
        
        logger.info(f"Refreshed connections for {len(servers)} external MCP servers - {successful_connections} successful")
        return {
            "status": "success",
            "message": f"Refreshed connections for {len(servers)} external MCP servers",
            "total_servers": len(servers),
            "successful_connections": successful_connections,
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
        
        # Get all servers
        servers = await mcp_orchestrator.get_external_servers()
        
        server_healths = {}
        for server in servers:
            server_id = server.get("server_id", "")
            try:
                # Get health status for each server
                health_response = await get_server_health(server_id)
                server_healths[server_id] = {
                    "server_id": health_response.server_id,
                    "name": health_response.name,
                    "status": health_response.status,
                    "last_check": health_response.last_check,
                    "tools_count": health_response.tools_count,
                    "response_time": health_response.response_time,
                    "error_message": health_response.error_message
                }
            except Exception as e:
                logger.error(f"Failed to get health for server {server_id}: {e}")
                server_healths[server_id] = {
                    "server_id": server_id,
                    "name": server.get("name", "Unknown"),
                    "status": "error",
                    "last_check": datetime.now().isoformat(),
                    "tools_count": 0,
                    "error_message": str(e)
                }
        
        healthy_servers = sum(1 for health in server_healths.values() if health.get("status") == "healthy")
        
        logger.info(f"Retrieved health status for {len(server_healths)} external MCP servers - {healthy_servers} healthy")
        return {
            "status": "success",
            "total_servers": len(server_healths),
            "healthy_servers": healthy_servers,
            "servers": server_healths
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
        
        # Verify server exists
        servers = await mcp_orchestrator.get_external_servers()
        server = next((s for s in servers if s.get("server_id") == server_id), None)
        
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"External MCP server with ID '{server_id}' not found"
            )
        
        # Force tool discovery using the corrected FastMCP client
        from ...core.fastmcp_client import FastMCPClientFactory
        
        try:
            # Create appropriate client
            client = None
            server_url = server.get("server_url", "")
            
            if server_url.startswith(('http://', 'https://')):
                client = FastMCPClientFactory.create_http_client(
                    server_url, 
                    server.get("name", "Unknown"), 
                    timeout=30.0
                )
            else:
                server_command = server_url.split()
                client = FastMCPClientFactory.create_stdio_client(
                    server_command, 
                    server.get("name", "Unknown"), 
                    timeout=30.0
                )
            
            # Discover tools directly
            async with client:
                tools = await client.list_tools()
                
                # Also try to list resources
                resources = []
                try:
                    resources = await client.list_resources()
                except Exception:
                    # Resources might not be supported
                    pass
                
                logger.info(f"Manual tool discovery completed: {len(tools)} tools, {len(resources)} resources found")
                return {
                    "status": "success",
                    "message": f"Tools refreshed successfully. Found {len(tools)} tools and {len(resources)} resources.",
                    "server_id": server_id,
                    "server_name": server.get("name", "Unknown"),
                    "tools_count": len(tools),
                    "resources_count": len(resources),
                    "tools": tools,
                    "resources": resources,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to refresh tools for server {server_id}: {e}")
            return {
                "status": "error",
                "message": f"Failed to refresh tools: {str(e)}",
                "server_id": server_id,
                "server_name": server.get("name", "Unknown"),
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh tools for external MCP server {server_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )