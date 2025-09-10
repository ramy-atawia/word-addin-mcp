"""
FastMCP Client Implementation - Real FastMCP API

This implementation uses the actual FastMCP library API from the fastmcp source code,
replacing all custom classes with real FastMCP classes.
"""

import asyncio
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

import structlog
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from mcp import McpError  # McpError comes from mcp package directly
from fastmcp.exceptions import ClientError, ToolError

logger = structlog.get_logger()


class MCPConnectionState(Enum):
    """MCP Connection states using real FastMCP patterns."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"


class MCPConnectionError(Exception):
    """MCP Connection error - wrapper around FastMCP ClientError."""
    pass


class MCPToolError(Exception):
    """MCP Tool execution error - wrapper around FastMCP ToolError."""
    pass


class MCPProtocolError(Exception):
    """MCP Protocol error - wrapper around FastMCP McpError."""
    pass


@dataclass
class MCPConnectionConfig:
    """Configuration for MCP connections using real FastMCP transports."""
    server_url: str
    server_name: str
    transport_type: str = "auto"  # auto, ws, sse, stdio, fastmcp
    timeout: float = 30.0
    max_retries: int = 3
    auth_token: Optional[str] = None


class FastMCPClient:
    """
    FastMCP Client wrapper that uses the real FastMCP Client API.
    
    This class provides compatibility with existing code while using
    the actual FastMCP implementation underneath.
    """
    
    def __init__(self, config: MCPConnectionConfig):
        """Initialize FastMCP client with real transport."""
        self.config = config
        self.client: Optional[Client] = None
        self.state = MCPConnectionState.DISCONNECTED
        
        logger.info(f"FastMCP client initialized for {config.server_name}")
    
    async def connect(self) -> bool:
        """Connect to MCP server using FastMCP 2.3.0 with StreamableHttpTransport."""
        try:
            self.state = MCPConnectionState.CONNECTING
            logger.info(f"Connecting to MCP server: {self.config.server_name}")
            
            # Use StreamableHttpTransport for HTTP/HTTPS URLs (FastMCP 2.3.0+)
            if self.config.server_url.startswith(('http://', 'https://')):
                transport = StreamableHttpTransport(url=self.config.server_url)
                self.client = Client(transport)
                logger.info(f"Using StreamableHttpTransport for {self.config.server_name}")
            else:
                # For other URLs (stdio, ws, etc.), let FastMCP auto-detect
                self.client = Client(self.config.server_url)
                logger.info(f"Using auto-detected transport for {self.config.server_name}")
            
            self.state = MCPConnectionState.CONNECTED
            logger.info(f"Successfully created FastMCP client for {self.config.server_name}")
            return True
            
        except Exception as e:
            self.state = MCPConnectionState.FAILED
            logger.error(f"Failed to create FastMCP client: {e}")
            raise MCPConnectionError(f"Connection failed: {e}")
    
    
    async def disconnect(self):
        """Disconnect from MCP server."""
        try:
            if self.client:
                # Real FastMCP client handles disconnect through context manager
                # Close is available but optional
                if hasattr(self.client, 'close'):
                    await self.client.close()
            self.state = MCPConnectionState.DISCONNECTED
            logger.info(f"Disconnected from {self.config.server_name}")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools using real FastMCP API with context manager."""
        if not self.client:
            raise MCPConnectionError("Client not initialized")
        
        try:
            # Use async context manager for FastMCP client
            async with self.client:
                tools_result = await self.client.list_tools()
                
                # Convert to expected format
                tools = []
                for tool in tools_result:
                    # Handle both dict and object formats
                    if isinstance(tool, dict):
                        tools.append({
                            "name": tool.get("name", ""),
                            "description": tool.get("description", ""),
                            "input_schema": tool.get("inputSchema", {})
                        })
                    else:
                        # Handle MCP Tool objects (inputSchema is already a dict)
                        input_schema = {}
                        if hasattr(tool, 'inputSchema') and tool.inputSchema:
                            # inputSchema is already a dict, no need for model_dump()
                            input_schema = tool.inputSchema
                        
                        tools.append({
                            "name": tool.name,
                            "description": tool.description,
                            "input_schema": input_schema
                        })
                
                return tools
            
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            raise MCPToolError(f"Failed to list tools: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check using real FastMCP API."""
        if not self.client:
            raise MCPConnectionError("Client not initialized")
        
        try:
            # Try to ping the server using real FastMCP
            result = await self.client.ping()
            return {
                "status": "healthy" if result else "unhealthy",
                "server_name": self.config.server_name,
                "ping_successful": result
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "server_name": self.config.server_name,
                "error": str(e)
            }
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Call a tool using real FastMCP API."""
        if not self.client or self.state != MCPConnectionState.CONNECTED:
            raise MCPConnectionError("Client not connected")
        
        try:
            logger.info(f"Calling tool {tool_name} with parameters: {parameters}")
            
            # Use real FastMCP call_tool with context manager
            async with self.client:
                result = await self.client.call_tool(
                    name=tool_name,
                    arguments=parameters
                )
            
            logger.info(f"Tool {tool_name} executed successfully")
            return result
            
        except ToolError as e:
            logger.error(f"Tool execution failed: {e}")
            raise MCPToolError(f"Tool execution failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error calling tool: {e}")
            raise MCPProtocolError(f"Unexpected error: {e}")
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self.state == MCPConnectionState.CONNECTED
    
    
    async def __aenter__(self):
        """Async context manager entry - delegate to real FastMCP client."""
        # Initialize client if not already done
        if not self.client:
            await self.connect()
        
        # Enter the real FastMCP client context
        self._client_context = await self.client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - delegate to real FastMCP client."""
        if self.client and hasattr(self, '_client_context'):
            await self.client.__aexit__(exc_type, exc_val, exc_tb)
        await self.disconnect()
        return False

