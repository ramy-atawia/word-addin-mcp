"""
External MCP Server Management API endpoints - RESTORED.

This module provides REST API endpoints for managing external MCP servers
using the corrected MCP client implementation and proper error handling.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ...core.fastmcp_client import MCPConnectionError, MCPToolError
from ...services.mcp.orchestrator import get_initialized_mcp_orchestrator
from datetime import datetime

logger = logging.getLogger(__name__)

# Authentication is now handled by Azure API Management

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
    timeout: float = 30.0
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
    timeout: float = 30.0
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
        
        # Test connection first using FastMCP client
        try:
            from ...core.fastmcp_client import FastMCPClient, MCPConnectionConfig
            
            # Create connection config
            config = MCPConnectionConfig(
                server_url=request.server_url,
                server_name=request.name,
                timeout=request.timeout
            )
            
            client = FastMCPClient(config)
            
            # Test connection
            async with client:
                health_result = await client.health_check()
                if health_result.get("status") != "healthy":
                    raise Exception(f"Health check failed: {health_result}")
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
        
        try:
            mcp_orchestrator = get_initialized_mcp_orchestrator()
            server_id = await mcp_orchestrator.add_external_server(server_config)
        except RuntimeError as e:
            if "not yet initialized" in str(e):
                logger.warning("MCP Orchestrator not initialized, creating mock server ID")
                server_id = f"server-{datetime.now().timestamp()}"
            else:
                raise
        
        # Get server info for response
        try:
            servers = await mcp_orchestrator.get_external_servers()
            server = next((s for s in servers if s.get("server_id") == server_id), None)
        except RuntimeError:
            servers = []
            server = None
        
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
                health_result = await client.health_check()
                if health_result.get("status") != "healthy":
                    raise Exception(f"Health check failed: {health_result}")
                
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
        
        try:
            mcp_orchestrator = get_initialized_mcp_orchestrator()
            servers = await mcp_orchestrator.get_external_servers()
        except RuntimeError as e:
            if "not yet initialized" in str(e):
                logger.warning("MCP Orchestrator not initialized, returning empty servers list")
                return []
            raise
        
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
        
        try:
            mcp_orchestrator = get_initialized_mcp_orchestrator()
            servers = await mcp_orchestrator.get_external_servers()
        except RuntimeError as e:
            if "not yet initialized" in str(e):
                logger.warning("MCP Orchestrator not initialized, server not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"External MCP server with ID '{server_id}' not found"
                )
            raise
        
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
        
        try:
            mcp_orchestrator = get_initialized_mcp_orchestrator()
            success = await mcp_orchestrator.remove_external_server(server_id)
        except RuntimeError as e:
            if "not yet initialized" in str(e):
                logger.warning("MCP Orchestrator not initialized, cannot remove server")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"External MCP server {server_id} not found or could not be removed"
                )
            raise
        
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


@router.put("/servers/{server_id}")
async def update_external_server(server_id: str, request: AddServerRequest):
    """
    Update an external MCP server.
    
    Args:
        server_id: ID of the server to update
        request: Updated server configuration
        
    Returns:
        Update result
    """
    try:
        logger.info(f"Updating external MCP server: {server_id}")
        
        # First remove the old server
        try:
            mcp_orchestrator = get_initialized_mcp_orchestrator()
            await mcp_orchestrator.remove_external_server(server_id)
        except RuntimeError as e:
            if "not yet initialized" in str(e):
                logger.warning("MCP Orchestrator not initialized, cannot update server")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"External MCP server with ID '{server_id}' not found"
                )
            raise
        
        # Add the updated server
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
        
        new_server_id = await mcp_orchestrator.add_external_server(server_config)
        
        logger.info(f"External MCP server {server_id} updated successfully with new ID: {new_server_id}")
        return {
            "status": "success",
            "message": f"External MCP server updated successfully",
            "old_server_id": server_id,
            "new_server_id": new_server_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update external MCP server {server_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )
