"""
Unified MCP Server Registry - Fixed Version.

This registry manages all MCP servers (internal and external)
through a unified interface using the corrected FastMCP client.
"""

import asyncio
import json
import os
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
        
        # Health check caching to prevent frequent connections
        self._health_cache: Dict[str, Dict[str, Any]] = {}
        self._health_cache_ttl = 60  # Cache health checks for 30 seconds
        
        logger.info("MCP Server Registry initialized")
    
    def _is_health_cache_valid(self, server_id: str) -> bool:
        """Check if health cache for a server is still valid."""
        if server_id not in self._health_cache:
            return False
        
        cache_entry = self._health_cache[server_id]
        cache_time = cache_entry.get("timestamp", 0)
        return (time.time() - cache_time) < self._health_cache_ttl
    
    def clear_health_cache(self, server_id: str = None) -> None:
        """Clear health cache for a specific server or all servers."""
        if server_id:
            self._health_cache.pop(server_id, None)
            logger.debug(f"Cleared health cache for server: {server_id}")
        else:
            self._health_cache.clear()
            logger.debug("Cleared all health cache")
    
    async def _load_servers_from_config(self) -> None:
        """Load external servers from configuration file."""
        try:
            config_file = os.path.join(os.path.dirname(__file__), "..", "..", "..", "configured_mcp_servers.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                servers_config = config_data.get("servers", {})
                for server_id, server_config in servers_config.items():
                    if server_config.get("type") == "external":
                        await self.add_server(server_config)
                        logger.info(f"Loaded external server from config: {server_config.get('name', server_id)}")
            else:
                logger.warning(f"Configuration file not found: {config_file}")
        except Exception as e:
            logger.error(f"Failed to load servers from config: {e}")
    
    async def initialize(self) -> None:
        """Initialize the MCP server registry."""
        try:
            await self._load_servers_from_config()
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
            
            # For internal servers, skip connection test during registration
            # Connection will be established when tools are executed
            if server_info.type == "internal":
                self.servers[server_id] = server_info
                # Clear health cache since we have a new server
                self.clear_health_cache(server_id)
                logger.info(f"Internal MCP server '{server_info.name}' added with ID: {server_id}")
                return server_id
            else:
                # Test connection for external servers
                if await self._test_server_connection(server_info):
                    self.servers[server_id] = server_info
                    # Clear health cache since we have a new server
                    self.clear_health_cache(server_id)
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
            
            # Clear health cache for removed server
            self.clear_health_cache(server_id)
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
        """Discover tools from internal MCP server via direct HTTP call."""
        try:
            import aiohttp
            import os

            # Resolve internal MCP endpoint from env (INTERNAL_MCP_URL) or default to localhost
            internal_mcp_url = os.getenv("INTERNAL_MCP_URL", "http://localhost:8001/mcp")

            # Make direct HTTP call to internal MCP server
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    internal_mcp_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/list"
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Handle new MCP format where tools are returned as direct array
                        tools_data = data.get("result", [])
                        if not isinstance(tools_data, list):
                            # Fallback for old format with "tools" wrapper
                            tools_data = data.get("result", {}).get("tools", [])
                        
                        unified_tools = []
                        for tool_data in tools_data:
                            unified_tool = UnifiedTool(
                                name=tool_data.get("name", ""),
                                description=tool_data.get("description", ""),
                                server_id=server.server_id,
                                server_name=server.name,
                                source="internal",
                                category=tool_data.get("category", "general"),
                                input_schema=tool_data.get("inputSchema", {}),
                                requires_auth=tool_data.get("requires_auth", False),
                                usage_count=tool_data.get("usage_count", 0)
                            )
                            unified_tools.append(unified_tool)
                        
                        return unified_tools
                    else:
                        logger.error(f"HTTP error {response.status} from internal MCP server")
                        return []
            
        except Exception as e:
            logger.error(f"Failed to discover tools from internal MCP server: {e}")
            return []
    
    async def _discover_external_tools(self, server: MCPServerInfo) -> List[UnifiedTool]:
        """Discover tools from external server using persistent connections."""
        try:
            # Use short-lived FastMCP client per call to avoid cross-task context issues
            from app.core.fastmcp_client import FastMCPClient, MCPConnectionConfig

            config = MCPConnectionConfig(
                server_url=server.url,
                server_name=server.name,
                timeout=30.0,
            )

            client = FastMCPClient(config)

            if not await client.connect():
                logger.error(f"Failed to connect to external server {server.name}")
                return []

            try:
                tools_data = await client.list_tools()

                unified_tools: List[UnifiedTool] = []
                logger.debug(f"Processing {len(tools_data)} tools from {server.name}")
                for tool_data in tools_data:
                    if self._validate_tool_schema(tool_data):
                        unified_tool = self._create_unified_tool_from_mcp(tool_data, server)
                        unified_tools.append(unified_tool)
                        logger.debug(f"Created tool: {unified_tool.name}")
                    else:
                        logger.warning(f"Tool validation failed: {tool_data.get('name', 'unknown')}")

                logger.debug(f"Returned {len(unified_tools)} tools from {server.name}")
                return unified_tools
            finally:
                try:
                    await client.disconnect()
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Failed to discover external tools: {e}")
            return []
    
    def _validate_tool_schema(self, tool_data: Dict[str, Any]) -> bool:
        """Validate basic tool schema."""
        # Only name is required, description can be None
        if "name" not in tool_data or not isinstance(tool_data["name"], str):
            return False
        
        # Description is optional, but if present should be a string
        if "description" in tool_data and tool_data["description"] is not None:
            if not isinstance(tool_data["description"], str):
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
        """Execute a tool on internal MCP server via direct HTTP call."""
        try:
            import aiohttp
            import os

            # Resolve internal MCP endpoint from env (INTERNAL_MCP_URL) or default to localhost
            internal_mcp_url = os.getenv("INTERNAL_MCP_URL", "http://localhost:8001/mcp")

            # Make direct HTTP call to internal MCP server
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    internal_mcp_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/call",
                        "params": {
                            "name": tool_info.name,
                            "arguments": parameters
                        }
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "result" in data:
                            return data["result"]
                        elif "error" in data:
                            raise ConnectionError(f"MCP server error: {data['error']['message']}")
                        else:
                            raise ConnectionError("Invalid response from internal MCP server")
                    else:
                        raise ConnectionError(f"HTTP error {response.status} from internal MCP server")
            
        except Exception as e:
            logger.error(f"Failed to execute tool on internal MCP server: {e}")
            raise ConnectionError(f"Failed to execute tool: {e}")
    
    async def _execute_external_tool(self, server: MCPServerInfo, tool_info: UnifiedTool, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool on external server using persistent connections."""
        try:
            # Use a short-lived FastMCP client for execution to keep contexts task-local
            from app.core.fastmcp_client import FastMCPClient, MCPConnectionConfig

            config = MCPConnectionConfig(
                server_url=server.url,
                server_name=server.name,
                timeout=60.0,
            )

            client = FastMCPClient(config)
            if not await client.connect():
                raise ConnectionError(f"Failed to connect to {server.name}")

            try:
                result = await client.call_tool(tool_info.name, parameters)
                return result
            finally:
                try:
                    await client.disconnect()
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Failed to execute external tool {tool_info.name} on {server.name}: {e}")
            raise ConnectionError(f"Execution failed: {e}")
    
    async def _test_server_connection(self, server: MCPServerInfo) -> bool:
        """Test connection to a server."""
        try:
            if server.type == "internal":
                # Test internal MCP server via HTTP health check
                import aiohttp

                internal_health_url = os.getenv("INTERNAL_MCP_HEALTH", "http://localhost:8001/health")

                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(internal_health_url, timeout=5) as resp:
                            if resp.status == 200:
                                server.connected = True
                                server.status = "healthy"
                                server.last_health_check = time.time()
                                return True
                except Exception as e:
                    logger.debug(f"Internal server health check failed: {e}")

                server.connected = False
                server.status = "failed"
                return False
            else:
                # External server connection test using FastMCP client
                from app.core.fastmcp_client import FastMCPClient, MCPConnectionConfig
                
                # Create connection config
                config = MCPConnectionConfig(
                    server_url=server.url,
                    server_name=server.name,
                    timeout=10.0
                )
                
                client = FastMCPClient(config)
                
                # Connect to the server
                if await client.connect():
                    # Test basic connectivity with health check
                    is_connected = await client.health_check()
                    
                    if is_connected:
                        # Also try to list tools to ensure full functionality
                        await client.list_tools()
                    
                    # Disconnect after test
                    await client.disconnect()
                    
                    server.connected = is_connected
                    server.status = "healthy" if is_connected else "failed"
                    server.last_health_check = time.time()
                    return is_connected
                else:
                    server.connected = False
                    server.status = "failed"
                    server.last_health_check = time.time()
                    return False
                    
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
            # Check cache first for external servers to avoid frequent connections
            if server.type == "external" and self._is_health_cache_valid(server.server_id):
                cached_health = self._health_cache[server.server_id]
                logger.debug(f"Using cached health for {server.name}")
                return cached_health["health_data"]
            
            if server.type == "internal":
                # Test internal MCP server via HTTP health check
                import aiohttp

                internal_health_url = os.getenv("INTERNAL_MCP_HEALTH", "http://localhost:8001/health")

                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(internal_health_url, timeout=5) as resp:
                            if resp.status == 200:
                                return {
                                    "status": "healthy",
                                    "server_id": server.server_id,
                                    "server_name": server.name,
                                    "type": "internal",
                                    "last_health_check": time.time()
                                }
                except Exception as e:
                    logger.debug(f"Internal server health check failed: {e}")

                return {
                    "status": "unhealthy",
                    "server_id": server.server_id,
                    "server_name": server.name,
                    "type": "internal",
                    "error": f"Internal server health check failed: {str(e)}",
                    "last_health_check": time.time()
                }
            else:
                # External server health check using persistent connections
                try:
                    from app.core.mcp_connection_manager import get_connection_manager
                    
                    # Get connection from pool
                    connection_manager = await get_connection_manager()
                    connection = await connection_manager.get_connection(server.url, server.name)
                    
                    if not connection:
                        server.connection_errors += 1
                        server.status = "unhealthy"
                        server.connected = False
                        
                        health_data = {
                            "status": "unhealthy",
                            "server_id": server.server_id,
                            "server_name": server.name,
                            "type": "external",
                            "error": "No connection available"
                        }
                        
                        # Cache the health result
                        self._health_cache[server.server_id] = {
                            "health_data": health_data,
                            "timestamp": time.time()
                        }
                        
                        return health_data
                    
                    # Use health check method from persistent connection
                    is_healthy = await connection.client.health_check()
                    
                    if is_healthy:
                        server.last_health_check = time.time()
                        server.status = "healthy"
                        server.connected = True
                        
                        health_data = {
                            "status": "healthy",
                            "server_id": server.server_id,
                            "server_name": server.name,
                            "type": "external",
                            "last_health_check": server.last_health_check
                        }
                        
                        # Cache the health result
                        self._health_cache[server.server_id] = {
                            "health_data": health_data,
                            "timestamp": time.time()
                        }
                        
                        return health_data
                    else:
                        server.connection_errors += 1
                        server.status = "unhealthy"
                        server.connected = False
                        
                        health_data = {
                            "status": "unhealthy",
                            "server_id": server.server_id,
                            "server_name": server.name,
                            "type": "external",
                            "error": "Health check failed"
                        }
                        
                        # Cache the health result (even unhealthy ones)
                        self._health_cache[server.server_id] = {
                            "health_data": health_data,
                            "timestamp": time.time()
                        }
                        
                        return health_data
                        
                except Exception as e:
                    server.connection_errors += 1
                    server.status = "unhealthy"
                    server.connected = False
                    
                    health_data = {
                        "status": "unhealthy",
                        "server_id": server.server_id,
                        "server_name": server.name,
                        "type": "external",
                        "error": str(e)
                    }
                    
                    # Cache the health result (even error cases)
                    self._health_cache[server.server_id] = {
                        "health_data": health_data,
                        "timestamp": time.time()
                    }
                    
                    return health_data
                
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
            
            # The corrected FastMCP client handles disconnection automatically
            # through the async context manager, so no explicit disconnect needed
            logger.debug(f"Disconnection handled by FastMCP client for {server.name}")
            
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
                        
                        # Skip health checks for external servers that are working well
                        if (server.type == "external" and 
                            server.connected and 
                            server.status == "healthy"):
                            logger.debug(f"Skipping health check for healthy external server: {server.name}")
                            continue
                        
                        await self._get_server_health(server)
                    
                    await asyncio.sleep(300)  # Check every 5 minutes
                    
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