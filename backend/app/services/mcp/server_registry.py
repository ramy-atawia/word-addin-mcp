"""
Unified MCP Server Registry.

This registry manages all MCP servers (internal and external)
through a unified interface.
"""

import asyncio
import time
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

import structlog

from app.core.exceptions import (
    ExternalMCPServerError,
    ConnectionError,
    AuthenticationError
)

logger = structlog.get_logger()


@dataclass
class MCPServerInfo:
    """Information about an MCP server."""
    
    server_id: str
    name: str
    url: str
    type: str  # 'internal' or 'external'
    config: Dict[str, Any]
    status: str = "unknown"
    connected: bool = False
    last_health_check: float = 0
    connection_errors: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UnifiedTool:
    """Unified tool representation from any MCP server."""
    
    name: str
    description: str
    server_id: str
    server_name: str
    source: str  # 'internal' or 'external'
    input_schema: Dict[str, Any] = field(default_factory=dict)
    category: str = "general"
    requires_auth: bool = False
    usage_count: int = 0


class MCPServerRegistry:
    """
    Unified registry for all MCP servers.
    
    This registry treats internal and external MCP servers uniformly.
    """
    
    def __init__(self):
        """Initialize the MCP server registry."""
        self.servers: Dict[str, MCPServerInfo] = {}
        self.health_monitor_task: Optional[asyncio.Task] = None
        self.health_monitor_running = False
        
        logger.info("MCP Server Registry initialized")
    
    async def initialize(self) -> None:
        """Initialize the MCP server registry."""
        try:
            await self._start_health_monitor()
            logger.info("MCP Server Registry initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MCP Server Registry: {e}")
            raise
    
    async def add_server(self, config: Dict[str, Any]) -> str:
        """
        Add an MCP server to the registry.
        
        Args:
            config: Server configuration
            
        Returns:
            Server ID for the newly added server
        """
        try:
            server_id = str(uuid.uuid4())
            
            server_info = MCPServerInfo(
                server_id=server_id,
                name=config.get('name', 'Unknown'),
                url=config.get('url', ''),
                type=config.get('type', 'external'),
                config=config,
                metadata=config.get('metadata', {})
            )
            
            # Test connection
            if await self._test_server_connection(server_info):
                self.servers[server_id] = server_info
                logger.info(f"MCP server '{server_info.name}' added with ID: {server_id}")
                return server_id
            else:
                raise ConnectionError(f"Failed to connect to server: {server_info.name}")
                
        except Exception as e:
            logger.error(f"Failed to add MCP server: {e}")
            raise ExternalMCPServerError(f"Failed to add server: {e}")
    
    async def remove_server(self, server_id: str) -> bool:
        """
        Remove an MCP server from the registry.
        
        Args:
            server_id: ID of the server to remove
            
        Returns:
            True if server was removed successfully
        """
        try:
            if server_id not in self.servers:
                return False
            
            server = self.servers[server_id]
            
            # Cleanup external servers
            if server.type == "external":
                await self._disconnect_external_server(server)
            
            del self.servers[server_id]
            logger.info(f"MCP server {server_id} removed successfully")
            return True
                
        except Exception as e:
            logger.error(f"Failed to remove MCP server {server_id}: {e}")
            raise ExternalMCPServerError(f"Failed to remove server: {e}")
    
    def get_server(self, server_id: str) -> Optional[MCPServerInfo]:
        """Get MCP server by ID."""
        return self.servers.get(server_id)
    
    def list_servers(self) -> List[MCPServerInfo]:
        """List all registered MCP servers."""
        return list(self.servers.values())
    
    async def list_all_tools(self) -> List[UnifiedTool]:
        """List all tools from all MCP servers."""
        all_tools = []
        
        for server in self.servers.values():
            try:
                tools = await self._discover_tools_from_server(server)
                all_tools.extend(tools)
            except Exception as e:
                logger.error(f"Failed to get tools from server {server.name}: {e}")
        
        logger.info(f"Retrieved {len(all_tools)} tools from {len(self.servers)} servers")
        return all_tools
    
    async def get_tool_info(self, tool_name: str) -> Optional[UnifiedTool]:
        """Get information about a specific tool from any server."""
        for server in self.servers.values():
            try:
                tools = await self._discover_tools_from_server(server)
                for tool in tools:
                    if tool.name == tool_name:
                        return tool
            except Exception:
                continue
        
        return None
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool from any server."""
        # Find tool and determine server
        tool_info = await self.get_tool_info(tool_name)
        if not tool_info:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        # Execute tool on the appropriate server
        result = await self._execute_tool_on_server(tool_info, parameters)
        
        # Update usage count
        tool_info.usage_count += 1
        
        return result
    
    async def get_health(self) -> Dict[str, Any]:
        """Get health status of all MCP servers."""
        try:
            server_healths = {}
            overall_status = "healthy"
            
            for server_id, server in self.servers.items():
                try:
                    health = await self._get_server_health(server)
                    server_healths[server_id] = health
                    
                    if health.get("status") != "healthy":
                        overall_status = "degraded"
                        
                except Exception as e:
                    server_healths[server_id] = {
                        "status": "unhealthy",
                        "error": str(e),
                        "timestamp": time.time()
                    }
                    overall_status = "degraded"
            
            return {
                "status": overall_status,
                "timestamp": time.time(),
                "servers": server_healths,
                "total_servers": len(self.servers),
                "healthy_servers": sum(1 for h in server_healths.values() 
                                     if h.get("status") == "healthy")
            }
            
        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def _discover_tools_from_server(self, server: MCPServerInfo) -> List[UnifiedTool]:
        """Discover tools from a specific server."""
        try:
            if server.type == "internal":
                return await self._discover_internal_tools(server)
            else:
                return await self._discover_external_tools(server)
        except Exception as e:
            logger.error(f"Failed to discover tools from server {server.name}: {e}")
            return []
    
    async def _discover_internal_tools(self, server: MCPServerInfo) -> List[UnifiedTool]:
        """Discover tools from internal server."""
        try:
            from app.mcp_servers.internal_server import get_global_server
            internal_mcp_server = get_global_server()
            
            tools_data = await internal_mcp_server.tool_registry.list_all_tools()
            
            unified_tools = []
            for tool_data in tools_data:
                unified_tool = UnifiedTool(
                    name=tool_data.get("name", ""),
                    description=tool_data.get("description", ""),
                    server_id=server.server_id,
                    server_name=server.name,
                    source="internal",
                    category=tool_data.get("category", "general"),
                    input_schema=tool_data.get("input_schema", {}),
                    requires_auth=tool_data.get("requires_auth", False),
                    usage_count=tool_data.get("usage_count", 0)
                )
                unified_tools.append(unified_tool)
            
            return unified_tools
            
        except Exception as e:
            logger.error(f"Failed to discover internal tools: {e}")
            return []
    
    async def _discover_external_tools(self, server: MCPServerInfo) -> List[UnifiedTool]:
        """Discover tools from external server."""
        try:
            from app.core.mcp_client import MCPClientFactory
            
            client = None
            if server.url.startswith(('http://', 'https://')):
                client = MCPClientFactory.create_http_client(server.url, timeout=30)
            else:
                server_command = server.url.split()
                client = MCPClientFactory.create_stdio_client(server_command, timeout=30)
            
            async with client:
                tools_data = await client.discover_tools()
                
                unified_tools = []
                for tool_data in tools_data:
                    if hasattr(tool_data, 'dict'):
                        tool_dict = tool_data.dict()
                    else:
                        tool_dict = tool_data
                    
                    if self._validate_tool_schema(tool_dict):
                        unified_tool = self._create_unified_tool_from_mcp(tool_dict, server)
                        unified_tools.append(unified_tool)
                
                return unified_tools
            
        except Exception as e:
            logger.error(f"Failed to discover external tools: {e}")
            return []
    
    def _validate_tool_schema(self, tool_data: Dict[str, Any]) -> bool:
        """Validate basic tool schema."""
        required_fields = ["name", "description"]
        
        for field in required_fields:
            if field not in tool_data or not isinstance(tool_data[field], str):
                return False
        
        return bool(tool_data["name"].strip())
    
    def _create_unified_tool_from_mcp(self, tool_data: Dict[str, Any], server: MCPServerInfo) -> UnifiedTool:
        """Create UnifiedTool from MCP tool data."""
        input_schema = tool_data.get("inputSchema", tool_data.get("input_schema", {}))
        
        return UnifiedTool(
            name=tool_data.get("name", ""),
            description=tool_data.get("description", ""),
            server_id=server.server_id,
            server_name=server.name,
            source="external",
            category=tool_data.get("category", "general"),
            input_schema=input_schema,
            requires_auth=tool_data.get("requires_auth", False),
            usage_count=tool_data.get("usage_count", 0)
        )
    
    async def _execute_tool_on_server(self, tool_info: UnifiedTool, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool on its specific server."""
        server = self.servers.get(tool_info.server_id)
        if not server:
            raise ValueError(f"Server {tool_info.server_id} not found")
        
        if server.type == "internal":
            return await self._execute_internal_tool(tool_info, parameters)
        else:
            return await self._execute_external_tool(server, tool_info, parameters)
    
    async def _execute_internal_tool(self, tool_info: UnifiedTool, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool on internal server."""
        from app.mcp_servers.internal_server import get_global_server
        internal_mcp_server = get_global_server()
        
        return await internal_mcp_server.tool_registry.execute_tool(
            tool_info.name, parameters
        )
    
    async def _execute_external_tool(self, server: MCPServerInfo, tool_info: UnifiedTool, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool on external server."""
        from app.core.mcp_client import MCPClientFactory
        
        client = None
        if server.url.startswith(('http://', 'https://')):
            client = MCPClientFactory.create_http_client(server.url, timeout=30)
        else:
            server_command = server.url.split()
            client = MCPClientFactory.create_stdio_client(server_command, timeout=30)
        
        async with client:
            return await client.execute_tool(tool_info.name, parameters)
    
    async def _test_server_connection(self, server: MCPServerInfo) -> bool:
        """Test connection to a server."""
        try:
            if server.type == "internal":
                from app.mcp_servers.internal_server import get_global_server
                internal_server = get_global_server()
                
                if internal_server and internal_server.is_running:
                    server.connected = True
                    server.status = "healthy"
                    server.last_health_check = time.time()
                    return True
                
                server.connected = False
                server.status = "failed"
                return False
            else:
                # External server connection test
                from app.core.mcp_client import MCPClientFactory
                
                client = None
                if server.url.startswith(('http://', 'https://')):
                    client = MCPClientFactory.create_http_client(server.url, timeout=10)
                else:
                    server_command = server.url.split()
                    client = MCPClientFactory.create_stdio_client(server_command, timeout=10)
                
                async with client:
                    # Test basic connectivity
                    tools = await client.discover_tools()
                    
                    server.connected = True
                    server.status = "healthy"
                    server.last_health_check = time.time()
                    return True
                    
        except Exception as e:
            server.connected = False
            server.status = "failed"
            server.connection_errors += 1
            server.last_health_check = time.time()
            logger.debug(f"Connection test failed for {server.name}: {e}")
            return False
    
    async def _get_server_health(self, server: MCPServerInfo) -> Dict[str, Any]:
        """Get health status of a specific server."""
        try:
            if server.type == "internal":
                from app.mcp_servers.internal_server import get_global_server
                internal_server = get_global_server()
                
                if internal_server and internal_server.is_running:
                    return {
                        "status": "healthy",
                        "server_id": server.server_id,
                        "server_name": server.name,
                        "type": "internal",
                        "last_health_check": time.time()
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "server_id": server.server_id,
                        "server_name": server.name,
                        "type": "internal",
                        "error": "Internal server not running"
                    }
            else:
                # External server health check
                try:
                    from app.core.mcp_client import MCPClientFactory
                    
                    client = None
                    if server.url.startswith(('http://', 'https://')):
                        client = MCPClientFactory.create_http_client(server.url, timeout=10)
                    else:
                        server_command = server.url.split()
                        client = MCPClientFactory.create_stdio_client(server_command, timeout=10)
                    
                    async with client:
                        # Simple health check via tool discovery
                        await client.discover_tools()
                        
                        server.last_health_check = time.time()
                        server.status = "healthy"
                        server.connected = True
                        
                        return {
                            "status": "healthy",
                            "server_id": server.server_id,
                            "server_name": server.name,
                            "type": "external"
                        }
                        
                except Exception as e:
                    server.connection_errors += 1
                    server.status = "unhealthy"
                    server.connected = False
                    
                    return {
                        "status": "unhealthy",
                        "server_id": server.server_id,
                        "server_name": server.name,
                        "type": "external",
                        "error": str(e)
                    }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "server_id": server.server_id,
                "server_name": server.name
            }
    
    async def _disconnect_external_server(self, server: MCPServerInfo) -> None:
        """Gracefully disconnect from an external server."""
        try:
            if server.type != "external":
                return
            
            from app.core.mcp_client import MCPClientFactory
            
            client = None
            if server.url.startswith(('http://', 'https://')):
                client = MCPClientFactory.create_http_client(server.url, timeout=5)
            else:
                server_command = server.url.split()
                client = MCPClientFactory.create_stdio_client(server_command, timeout=5)
            
            if hasattr(client, 'disconnect'):
                await client.disconnect()
            
        except Exception as e:
            logger.debug(f"Error during server disconnection for {server.name}: {e}")
    
    async def _start_health_monitor(self) -> None:
        """Start the health monitoring task."""
        if self.health_monitor_running:
            return
        
        self.health_monitor_running = True
        
        async def health_monitor():
            while self.health_monitor_running:
                try:
                    for server in list(self.servers.values()):
                        # Skip recent health checks (within last 5 minutes)
                        if (server.connected and 
                            server.last_health_check > 0 and 
                            time.time() - server.last_health_check < 300):
                            continue
                        
                        await self._get_server_health(server)
                    
                    await asyncio.sleep(60)  # Check every minute
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Health monitor error: {e}")
                    await asyncio.sleep(60)
        
        self.health_monitor_task = asyncio.create_task(health_monitor())
    
    async def stop_health_monitor(self) -> None:
        """Stop the health monitoring task."""
        if not self.health_monitor_running:
            return
        
        self.health_monitor_running = False
        
        if self.health_monitor_task:
            self.health_monitor_task.cancel()
            try:
                await self.health_monitor_task
            except asyncio.CancelledError:
                pass
            self.health_monitor_task = None
    
    async def shutdown(self) -> None:
        """Shutdown the server registry gracefully."""
        try:
            logger.info("Shutting down MCP Server Registry...")
            
            # Stop health monitoring
            await self.stop_health_monitor()
            
            # Disconnect from all external servers
            for server in list(self.servers.values()):
                if server.type == "external":
                    await self._disconnect_external_server(server)
            
            # Clear server registry
            self.servers.clear()
            
            logger.info("MCP Server Registry shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Global registry instance
_global_registry: Optional[MCPServerRegistry] = None


async def get_global_registry() -> MCPServerRegistry:
    """Get or create the global MCP server registry."""
    global _global_registry
    
    if _global_registry is None:
        _global_registry = MCPServerRegistry()
        await _global_registry.initialize()
    
    return _global_registry


async def shutdown_global_registry() -> None:
    """Shutdown the global MCP server registry."""
    global _global_registry
    
    if _global_registry is not None:
        await _global_registry.shutdown()
        _global_registry = None