"""
FastMCP-based MCP Client Implementation - Fixed Version

This implementation uses the FastMCP 2.x library correctly, following the proper
MCP protocol standards and FastMCP API patterns.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

import structlog
from fastmcp import Client
# FastMCP handles transport creation automatically
from fastmcp.exceptions import McpError

logger = structlog.get_logger()


class MCPConnectionState(Enum):
    """MCP connection state."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"


class MCPConnectionError(Exception):
    """Exception for MCP connection errors."""
    pass


class MCPToolError(Exception):
    """Exception for MCP tool operation errors."""
    pass


class MCPProtocolError(Exception):
    """Exception for MCP protocol errors."""
    pass


@dataclass
class MCPConnectionConfig:
    """Configuration for MCP connection."""
    server_url: str
    server_name: str
    client_name: str = "word-addin-mcp-client"
    client_version: str = "1.0.0"
    timeout: float = 30.0
    transport_type: str = "auto"  # auto, sse, http, stdio
    api_key: Optional[str] = None
    auth_type: str = "none"  # none, api_key, oauth, basic
    username: Optional[str] = None
    password: Optional[str] = None


class FastMCPClient:
    """
    FastMCP 2.x-based MCP client that properly implements the MCP protocol.
    
    This client uses FastMCP's simplified API while maintaining full protocol compliance.
    """
    
    def __init__(self, config: MCPConnectionConfig):
        self.config = config
        self.state = MCPConnectionState.DISCONNECTED
        self.client: Optional[Client] = None
        self.last_error: Optional[str] = None
        self.connection_time: Optional[float] = None
        self.successful_requests = 0
        self.failed_requests = 0
        
    async def connect(self) -> bool:
        """Connect to MCP server using FastMCP."""
        try:
            logger.info(f"Connecting to MCP server: {self.config.server_url}")
            self.state = MCPConnectionState.CONNECTING
            
            # Create transport based on configuration
            transport_source = self._get_transport_source()
            
            # Create FastMCP client with proper configuration
            auth_config = self._get_auth_config()
            self.client = Client(
                transport=transport_source,
                timeout=self.config.timeout,
                auth=auth_config
            )
            
            # Use async context manager to establish connection
            await self.client.__aenter__()
            
            # Test connection with a simple ping
            try:
                await self.client.ping()
                logger.info(f"Successfully connected and pinged {self.config.server_url}")
            except Exception as e:
                logger.warning(f"Connected but ping failed: {e}")
                # Connection might still be valid, continue
            
            self.state = MCPConnectionState.CONNECTED
            self.connection_time = time.time()
            self.last_error = None
            
            return True
            
        except Exception as e:
            self.state = MCPConnectionState.FAILED
            self.last_error = str(e)
            logger.error(f"Failed to connect to {self.config.server_url}: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from MCP server."""
        try:
            if self.client:
                await self.client.__aexit__(None, None, None)
                self.client = None
            
            self.state = MCPConnectionState.DISCONNECTED
            logger.info(f"Disconnected from {self.config.server_url}")
            
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    def _get_transport_source(self) -> str:
        """Get the transport source for FastMCP Client."""
        url = self.config.server_url
        
        # FastMCP 2.x uses automatic transport inference based on the source string
        # For HTTP/HTTPS URLs, it creates HttpTransport automatically
        # For commands (like "python server.py"), it creates StdioTransport
        # For FastMCP server instances, it uses in-memory transport
        
        if self.config.transport_type == "auto":
            # Let FastMCP auto-detect based on the URL/command
            return url
        elif self.config.transport_type == "stdio":
            # For stdio, return the command directly
            return url
        elif self.config.transport_type in ["http", "sse"]:
            # For HTTP/SSE, ensure proper URL format
            if not url.startswith(("http://", "https://")):
                raise ValueError(f"Invalid HTTP URL: {url}")
            return url
        else:
            raise ValueError(f"Unsupported transport type: {self.config.transport_type}")
    
    def _get_auth_config(self) -> Optional[Any]:
        """Get authentication configuration for FastMCP Client."""
        if self.config.auth_type == "none" or not self.config.auth_type:
            return None
        elif self.config.auth_type == "api_key" and self.config.api_key:
            # For API key authentication, we'll use basic auth with the API key
            import httpx
            return httpx.BasicAuth("api", self.config.api_key)
        elif self.config.auth_type == "basic" and self.config.username and self.config.password:
            import httpx
            return httpx.BasicAuth(self.config.username, self.config.password)
        elif self.config.auth_type == "oauth":
            # For OAuth, we'll use the API key as the bearer token
            if self.config.api_key:
                import httpx
                
                class BearerAuth(httpx.Auth):
                    def __init__(self, token: str):
                        self.token = token
                    
                    def auth_flow(self, request):
                        request.headers["Authorization"] = f"Bearer {self.token}"
                        yield request
                
                return BearerAuth(self.config.api_key)
        else:
            logger.warning(f"Authentication type '{self.config.auth_type}' not supported or missing credentials")
            return None
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server."""
        if not self.is_connected():
            raise MCPConnectionError("Not connected to server")
        
        try:
            # Use FastMCP's list_tools method
            tools_response = await self.client.list_tools()
            
            # Convert to standard format
            tool_list = []
            for tool in tools_response:
                tool_dict = {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                tool_list.append(tool_dict)
            
            logger.info(f"Retrieved {len(tool_list)} tools from {self.config.server_url}")
            return tool_list
            
        except Exception as e:
            self.failed_requests += 1
            logger.error(f"Failed to list tools from {self.config.server_url}: {e}")
            raise MCPToolError(f"Failed to list tools: {e}")
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a tool with proper error handling."""
        if not self.is_connected():
            raise MCPConnectionError("Not connected to server")
        
        if parameters is None:
            parameters = {}
        
        try:
            logger.info(f"Executing tool '{tool_name}' on {self.config.server_name}")
            start_time = time.time()
            
            # Use FastMCP's call_tool method
            result = await self.client.call_tool(tool_name, parameters)
            
            execution_time = time.time() - start_time
            self.successful_requests += 1
            
            logger.info(f"Tool '{tool_name}' executed successfully in {execution_time:.2f}s")
            
            # Convert FastMCP result to standard format
            return self._convert_tool_result(result)
            
        except McpError as e:
            self.failed_requests += 1
            logger.error(f"MCP protocol error for '{tool_name}' on {self.config.server_name}: {e}")
            raise MCPToolError(f"MCP protocol error: {e}")
        except Exception as e:
            self.failed_requests += 1
            logger.error(f"Tool execution failed for '{tool_name}' on {self.config.server_name}: {e}")
            raise MCPToolError(f"Tool execution failed: {e}")
    
    def _convert_tool_result(self, result) -> Dict[str, Any]:
        """Convert FastMCP tool result to standard format."""
        try:
            # FastMCP 2.x returns CallToolResult objects
            # The result should have a 'content' field with list of content items
            
            if hasattr(result, 'content') and result.content:
                # Content is a list of content items
                content_items = []
                for item in result.content:
                    if hasattr(item, 'type') and hasattr(item, 'text'):
                        # TextContent
                        content_items.append({
                            "type": item.type,
                            "text": item.text
                        })
                    elif hasattr(item, 'type') and hasattr(item, 'data'):
                        # ImageContent or other data content
                        content_items.append({
                            "type": item.type,
                            "data": item.data,
                            **({"mimeType": item.mimeType} if hasattr(item, 'mimeType') else {})
                        })
                    else:
                        # Fallback: convert to text
                        content_items.append({
                            "type": "text",
                            "text": str(item)
                        })
                
                response = {"content": content_items}
                
                # Add isError flag if present
                if hasattr(result, 'isError') and result.isError:
                    response["isError"] = True
                
                # Add meta if present
                if hasattr(result, '_meta') and result._meta:
                    response["_meta"] = result._meta
                
                return response
            
            else:
                # Fallback for unexpected result format
                return {
                    "content": [
                        {
                            "type": "text", 
                            "text": str(result)
                        }
                    ]
                }
                
        except Exception as e:
            logger.warning(f"Error converting tool result: {e}")
            return {
                "content": [
                    {
                        "type": "text", 
                        "text": f"Error converting result: {str(result)}"
                    }
                ]
            }
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources from the MCP server."""
        if not self.is_connected():
            raise MCPConnectionError("Not connected to server")
        
        try:
            resources_response = await self.client.list_resources()
            
            resource_list = []
            for resource in resources_response.resources:
                resource_dict = {
                    "uri": resource.uri,
                    "name": resource.name,
                    "description": resource.description,
                    "mimeType": getattr(resource, 'mimeType', None)
                }
                resource_list.append(resource_dict)
            
            logger.info(f"Retrieved {len(resource_list)} resources from {self.config.server_url}")
            return resource_list
            
        except Exception as e:
            self.failed_requests += 1
            logger.error(f"Failed to list resources from {self.config.server_url}: {e}")
            raise MCPToolError(f"Failed to list resources: {e}")
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a specific resource."""
        if not self.is_connected():
            raise MCPConnectionError("Not connected to server")
        
        try:
            result = await self.client.read_resource(uri)
            
            # Convert to standard format
            content_items = []
            for item in result.contents:
                if hasattr(item, 'type') and hasattr(item, 'text'):
                    content_items.append({
                        "type": item.type,
                        "text": item.text
                    })
                elif hasattr(item, 'type') and hasattr(item, 'data'):
                    content_items.append({
                        "type": item.type,
                        "data": item.data,
                        **({"mimeType": item.mimeType} if hasattr(item, 'mimeType') else {})
                    })
            
            return {"contents": content_items}
            
        except Exception as e:
            self.failed_requests += 1
            logger.error(f"Failed to read resource {uri}: {e}")
            raise MCPToolError(f"Failed to read resource: {e}")
    
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self.state == MCPConnectionState.CONNECTED and self.client is not None
    
    async def health_check(self) -> bool:
        """Perform a health check."""
        if not self.is_connected():
            return False
        
        try:
            await self.client.ping()
            return True
        except Exception:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "state": self.state.value,
            "server_url": self.config.server_url,
            "server_name": self.config.server_name,
            "connection_time": self.connection_time,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "last_error": self.last_error
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


class FastMCPClientFactory:
    """Factory for creating FastMCP clients."""
    
    @staticmethod
    def create_http_client(
        server_url: str,
        server_name: str,
        client_name: str = "word-addin-mcp-client",
        timeout: float = 30.0,
        api_key: Optional[str] = None,
        auth_type: str = "none"
    ) -> FastMCPClient:
        """Create an HTTP-based FastMCP client."""
        config = MCPConnectionConfig(
            server_url=server_url,
            server_name=server_name,
            client_name=client_name,
            transport_type="http",
            timeout=timeout,
            api_key=api_key,
            auth_type=auth_type
        )
        return FastMCPClient(config)
    
    @staticmethod
    def create_sse_client(
        server_url: str,
        server_name: str,
        client_name: str = "word-addin-mcp-client",
        timeout: float = 30.0,
        api_key: Optional[str] = None,
        auth_type: str = "none"
    ) -> FastMCPClient:
        """Create an SSE-based FastMCP client."""
        config = MCPConnectionConfig(
            server_url=server_url,
            server_name=server_name,
            client_name=client_name,
            transport_type="sse",
            timeout=timeout,
            api_key=api_key,
            auth_type=auth_type
        )
        return FastMCPClient(config)
    
    @staticmethod
    def create_stdio_client(
        server_command: Union[str, List[str]],
        server_name: str,
        client_name: str = "word-addin-mcp-client",
        timeout: float = 30.0
    ) -> FastMCPClient:
        """Create a STDIO-based FastMCP client."""
        # Convert list to string if needed
        if isinstance(server_command, list):
            command_str = " ".join(server_command)
        else:
            command_str = server_command
            
        config = MCPConnectionConfig(
            server_url=command_str,
            server_name=server_name,
            client_name=client_name,
            transport_type="stdio",
            timeout=timeout
        )
        return FastMCPClient(config)
    
    @staticmethod
    def create_from_config(config_dict: Dict[str, Any]) -> List[FastMCPClient]:
        """Create multiple clients from MCP configuration dictionary."""
        clients = []
        
        # Handle Claude Desktop style configuration
        if "mcpServers" in config_dict:
            servers = config_dict["mcpServers"]
        else:
            servers = config_dict
            
        for server_name, server_config in servers.items():
            if "command" in server_config:
                # STDIO transport
                command = server_config["command"]
                if isinstance(command, str):
                    command_str = command
                else:
                    command_str = " ".join(command)
                    
                config = MCPConnectionConfig(
                    server_url=command_str,
                    server_name=server_name,
                    transport_type="stdio",
                    timeout=server_config.get("timeout", 30.0)
                )
            elif "url" in server_config:
                # HTTP/SSE transport
                config = MCPConnectionConfig(
                    server_url=server_config["url"],
                    server_name=server_name,
                    transport_type="auto",
                    timeout=server_config.get("timeout", 30.0)
                )
            else:
                logger.warning(f"Invalid server configuration for {server_name}")
                continue
                
            clients.append(FastMCPClient(config))
        
        return clients


# Example usage and testing utilities
async def test_client_connection(client: FastMCPClient) -> bool:
    """Test a client connection with basic operations."""
    try:
        async with client:
            # Test basic connectivity
            if not await client.health_check():
                logger.error("Health check failed")
                return False
            
            # Test listing tools
            tools = await client.list_tools()
            logger.info(f"Found {len(tools)} tools")
            
            # Test listing resources if available
            try:
                resources = await client.list_resources()
                logger.info(f"Found {len(resources)} resources")
            except Exception as e:
                logger.info(f"No resources available: {e}")
            
            return True
            
    except Exception as e:
        logger.error(f"Client test failed: {e}")
        return False


# Example configuration for common MCP servers
EXAMPLE_CONFIGS = {
    "filesystem": {
        "command": ["python", "-m", "mcp_server_filesystem", "/path/to/allowed/files"],
        "timeout": 30.0
    },
    "sqlite": {
        "command": ["python", "-m", "mcp_server_sqlite", "--db-path", "/path/to/database.db"],
        "timeout": 30.0
    },
    "http_server": {
        "url": "http://localhost:8000/mcp",
        "timeout": 30.0
    }
}