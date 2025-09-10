"""
MCP Orchestrator - Unified MCP Service Manager.

This module provides a single, unified interface for all MCP operations including:
- Tool discovery from built-in and external sources
- Tool execution orchestration
- Server management
- Health monitoring
"""

import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

import structlog

from app.core.exceptions import (
    ToolNotFoundError, 
    ValidationError, 
    ToolExecutionError,
    ExternalMCPServerError
)
from .server_registry import MCPServerRegistry
from .execution_engine import ToolExecutionEngine

logger = structlog.get_logger()


@dataclass
class UnifiedTool:
    """Unified tool representation across all sources."""
    
    name: str
    description: str
    source: str  # 'internal' or 'external'
    server_id: Optional[str] = None
    # Removed unused fields: capabilities, metadata, version, author, tags, category
    input_schema: Dict[str, Any] = field(default_factory=dict)
    # Removed unused fields: output_schema, examples, rate_limit, timeout, requires_auth, deprecated, status, usage_count


class MCPOrchestrator:
    """
    Unified MCP service orchestrator.
    
    This class provides a single interface for all MCP operations, eliminating
    the need for multiple separate MCP services. It coordinates between:
    - Internal MCP server (built-in tools)
    - External MCP servers
    - Tool execution engine
    """
    
    def __init__(self):
        """Initialize the MCP orchestrator."""
        self.server_registry = MCPServerRegistry()
        self.execution_engine = ToolExecutionEngine()
        self.internal_server = None
        
        # Performance metrics
        self.request_count = 0
        self.error_count = 0
        self.total_execution_time = 0.0
        
        # Tool discovery caching
        self._tool_cache = {}
        self._cache_timestamp = 0
        self._cache_ttl = 300  # 5 minutes cache TTL for better performance
        
        logger.info("MCP Orchestrator initialized successfully")
    
    def _clear_tool_cache(self) -> None:
        """Clear the tool discovery cache."""
        self._tool_cache = {}
        self._cache_timestamp = 0
        logger.info("Tool discovery cache cleared")
    
    async def initialize(self) -> None:
        """Initialize all MCP components."""
        try:
            logger.info("Initializing MCP Orchestrator components...")
            
            # Initialize connection manager for persistent connections
            from app.core.mcp_connection_manager import get_connection_manager
            await get_connection_manager()
            logger.info("MCP Connection Manager initialized with real FastMCP API")
            
            # Initialize server registry
            await self.server_registry.initialize()
            
            # Initialize execution engine
            await self.execution_engine.initialize()
            
            # Start internal MCP server (FastMCP compatible)
            await self._start_internal_server()
            
            # Register internal server in registry
            await self._register_internal_server()
            
            # Set global initialization state
            global _mcp_orchestrator_initialized
            _mcp_orchestrator_initialized = True
            
            logger.info("MCP Orchestrator components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP Orchestrator: {str(e)}")
            raise
    
    async def list_all_tools(self) -> Dict[str, Any]:
        """
        List all available tools from all MCP servers.
        
        Returns:
            Dictionary containing tools from all sources with metadata
        """
        start_time = time.time()
        self.request_count += 1
        
        try:
            # Check cache first
            current_time = time.time()
            if (current_time - self._cache_timestamp) < self._cache_ttl and self._tool_cache:
                logger.info("Returning cached tools (cache hit)")
                cached_result = self._tool_cache.copy()
                cached_result["cache_hit"] = True
                cached_result["execution_time"] = time.time() - start_time
                return cached_result
            
            logger.info("Listing all available tools from all MCP servers (cache miss)")
            
            # Get tools from all servers (unified)
            all_tools = await self.server_registry.list_all_tools()
            logger.info(f"Orchestrator received {len(all_tools)} tools from server registry")
            
            # Count tools by source
            internal_count = sum(1 for tool in all_tools if tool.source == "internal")
            external_count = sum(1 for tool in all_tools if tool.source == "external")
            logger.info(f"Tool counts - Internal: {internal_count}, External: {external_count}")
            
            execution_time = time.time() - start_time
            self.total_execution_time += execution_time
            
            # Cache the result
            result = {
                "tools": [tool.__dict__ for tool in all_tools],
                "total_count": len(all_tools),
                "built_in_count": internal_count,
                "external_count": external_count,
                "timestamp": current_time,
                "execution_time": execution_time,
                "cache_hit": False
            }
            
            self._tool_cache = result
            self._cache_timestamp = current_time
            
            logger.info(f"Successfully listed {len(all_tools)} tools", 
                       total_tools=len(all_tools),
                       internal_count=internal_count,
                       external_count=external_count,
                       execution_time=execution_time)
            
            return result
            
        except Exception as e:
            self.error_count += 1
            execution_time = time.time() - start_time
            logger.error(f"Failed to list all tools: {str(e)}", 
                        execution_time=execution_time)
            raise
    
    async def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific tool.
        
        Args:
            tool_name: Name of the tool to get info for
            
        Returns:
            Tool information or None if not found
        """
        start_time = time.time()
        self.request_count += 1
        
        try:
            logger.info(f"Getting tool info for: {tool_name}")
            
            # Get tool info from server registry (unified)
            tool_info = await self.server_registry.get_tool_info(tool_name)
            if tool_info:
                execution_time = time.time() - start_time
                self.total_execution_time += execution_time
                
                logger.info(f"Found tool '{tool_name}' in server: {tool_info.server_name}")
                return tool_info.__dict__
            
            execution_time = time.time() - start_time
            logger.warning(f"Tool '{tool_name}' not found in any server")
            return None
            
        except Exception as e:
            self.error_count += 1
            execution_time = time.time() - start_time
            logger.error(f"Failed to get tool info for '{tool_name}': {str(e)}", 
                        execution_time=execution_time)
            raise
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool from any server with unified interface.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            
        Returns:
            Tool execution result
            
        Raises:
            ToolNotFoundError: If tool is not found
            ValidationError: If parameters are invalid
            ToolExecutionError: If tool execution fails
        """
        start_time = time.time()
        self.request_count += 1
        
        try:
            logger.info(f"Executing tool: {tool_name}", parameters=parameters)
            
            # Validate parameters
            is_valid, errors = await self.execution_engine.validate_parameters(tool_name, parameters)
            if not is_valid:
                raise ValidationError(f"Invalid parameters for tool '{tool_name}': {errors}")
            
            # Execute tool through server registry (unified)
            result = await self.server_registry.execute_tool(tool_name, parameters)
            
            # Format result
            formatted_result = await self.execution_engine.format_result(result, tool_name)
            
            execution_time = time.time() - start_time
            self.total_execution_time += execution_time
            
            logger.info(f"Tool '{tool_name}' executed successfully", 
                       execution_time=execution_time,
                       result_status=formatted_result.get("status"))
            
            return formatted_result
            
        except (ToolNotFoundError, ValidationError, ToolExecutionError):
            # Re-raise these specific errors
            raise
        except Exception as e:
            self.error_count += 1
            execution_time = time.time() - start_time
            logger.error(f"Unexpected error executing tool '{tool_name}': {str(e)}", 
                        execution_time=execution_time)
            raise ToolExecutionError(f"Tool execution failed: {str(e)}")
    
    async def add_external_server(self, config: Dict[str, Any]) -> str:
        """
        Add an external MCP server.
        
        Args:
            config: Server configuration
            
        Returns:
            Server ID for the newly added server
        """
        try:
            # Ensure config has external type
            config["type"] = "external"
            server_id = await self.server_registry.add_server(config)
            
            # Clear tool cache since we added a new server
            self._clear_tool_cache()
            
            logger.info(f"External MCP server added successfully with ID: {server_id}")
            return server_id
            
        except Exception as e:
            logger.error(f"Failed to add external MCP server: {str(e)}")
            raise ExternalMCPServerError(f"Failed to add server: {str(e)}")
    
    async def remove_external_server(self, server_id: str) -> bool:
        """
        Remove an external MCP server.
        
        Args:
            server_id: ID of the server to remove
            
        Returns:
            True if server was removed successfully
        """
        try:
            success = await self.server_registry.remove_server(server_id)
            if success:
                # Clear tool cache since we removed a server
                self._clear_tool_cache()
                logger.info(f"External MCP server {server_id} removed successfully")
            else:
                logger.warning(f"External MCP server {server_id} not found for removal")
            return success
            
        except Exception as e:
            logger.error(f"Failed to remove external MCP server {server_id}: {str(e)}")
            raise ExternalMCPServerError(f"Failed to remove server: {str(e)}")
    
    async def get_server_health(self) -> Dict[str, Any]:
        """
        Get health status of all MCP components.
        
        Returns:
            Health status dictionary
        """
        try:
            logger.info("Getting MCP orchestrator health status")
            
            # Get server registry health
            registry_health = await self.server_registry.get_health()
            
            # Get execution engine health
            execution_health = await self.execution_engine.get_health()
            
            # Get internal server health
            internal_server_health = await self._get_internal_server_health()
            
            # Calculate overall health
            overall_status = "healthy"
            if (registry_health["status"] != "healthy" or 
                execution_health["status"] != "healthy" or
                internal_server_health["status"] != "healthy"):
                overall_status = "degraded"
            
            health_info = {
                "status": overall_status,
                "timestamp": time.time(),
                "components": {
                    "server_registry": registry_health,
                    "execution_engine": execution_health,
                    "internal_server": internal_server_health
                },
                "metrics": {
                    "request_count": self.request_count,
                    "error_count": self.error_count,
                    "total_execution_time": self.total_execution_time,
                    "average_execution_time": (
                        self.total_execution_time / max(self.request_count, 1)
                    )
                }
            }
            
            logger.info(f"MCP orchestrator health status: {overall_status}")
            return health_info
            
        except Exception as e:
            logger.error(f"Failed to get health status: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def _start_internal_server(self):
        """Start the internal MCP server (FastMCP compatible)."""
        try:
            # Import here to avoid circular imports
            from app.mcp_servers.internal_server import get_global_server
            
            # Get the global FastMCP server instance
            self.internal_server = get_global_server()
            
            # Ensure the server is properly initialized
            if not self.internal_server:
                raise RuntimeError("Failed to create internal MCP server instance")
            
            # Start the internal server
            await self.internal_server.start()
            
            # Verify server is running
            if not self.internal_server.is_running:
                raise RuntimeError("Internal MCP server failed to start")
            
            # Test tool registration
            tools = await self.internal_server.list_available_tools()
            logger.info(f"Internal FastMCP server started with {len(tools)} tools")
            
        except ImportError as e:
            logger.error(f"Failed to import internal server: {str(e)}")
            self.internal_server = None
        except Exception as e:
            logger.error(f"Failed to start internal MCP server: {str(e)}")
            self.internal_server = None
            # Don't re-raise - allow orchestrator to continue without internal server
            logger.warning("Continuing without internal MCP server")
    
    async def _register_internal_server(self):
        """Register the internal MCP server in the registry."""
        try:
            # Only register if internal server started successfully
            if self.internal_server and self.internal_server.is_running:
                config = {
                    "name": "Internal MCP Server",
                    "description": "Built-in tools exposed through FastMCP protocol",
                    "server_url": "internal://localhost:9001",
                    "type": "internal",
                    "protocol": "fastmcp",  # Updated to reflect FastMCP usage
                    "capabilities": ["tools/list", "tools/call"]
                }
                
                server_id = await self.server_registry.add_server(config)
                logger.info("Internal FastMCP server registered in registry")
            else:
                logger.warning("Internal server not running - skipping registration")
            
        except Exception as e:
            logger.error(f"Failed to register internal MCP server: {str(e)}")
            # Don't re-raise - this is not critical for orchestrator startup
            logger.warning("Continuing without internal server registration")
    
    async def _get_internal_server_health(self) -> Dict[str, Any]:
        """Get health status of the internal server."""
        try:
            if not self.internal_server:
                return {
                    "status": "not_started",
                    "message": "Internal server not initialized",
                    "timestamp": time.time()
                }
            
            if self.internal_server.is_running:
                # Get available tools as a health check
                tools = await self.internal_server.list_available_tools()
                return {
                    "status": "healthy",
                    "tool_count": len(tools),
                    "server_type": "fastmcp",
                    "timestamp": time.time()
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "Internal server not running",
                    "timestamp": time.time()
                }
                
        except Exception as e:
            logger.error(f"Failed to get internal server health: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    # Removed get_hub_status - redundant wrapper around get_server_health
    
    async def get_external_servers(self) -> List[Dict[str, Any]]:
        """
        Get list of external servers.
        
        Returns:
            List of external server information
        """
        try:
            servers = []
            for server_id, server in self.server_registry.servers.items():
                if server.type == "external":
                    server_info = {
                        "server_id": server_id,
                        "name": server.name,
                        "url": server.url,
                        "status": server.status,
                        "connected": server.status == "healthy",
                        "last_health_check": server.last_health_check
                    }
                    servers.append(server_info)
            
            return servers
            
        except Exception as e:
            logger.error(f"Failed to get external servers: {str(e)}")
            return []
    
    async def get_external_server_health(self) -> Dict[str, Any]:
        """
        Get health status of external servers.
        
        Returns:
            External server health information
        """
        try:
            # Get health from server registry, filter for external servers only
            all_health = await self.server_registry.get_health()
            
            # Filter for external servers
            external_servers = {}
            for server_id, server_health in all_health.get("servers", {}).items():
                if server_health.get("type") == "external":
                    external_servers[server_id] = server_health
            
            return {
                "status": "healthy" if external_servers else "no_external_servers",
                "external_servers": external_servers,
                "total_external_servers": len(external_servers),
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Failed to get external server health: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def test_external_server_connection(self, server_id: str) -> Dict[str, Any]:
        """
        Test connection to an external server.
        
        Args:
            server_id: ID of the server to test
            
        Returns:
            Connection test result
        """
        try:
            server = self.server_registry.get_server(server_id)
            if not server:
                return {
                    "success": False,
                    "error": f"Server {server_id} not found"
                }
            
            if server.type != "external":
                return {
                    "success": False,
                    "error": f"Server {server_id} is not an external server"
                }
            
            # Test connection using server registry
            is_healthy = await self.server_registry._test_server_connection(server)
            
            return {
                "success": is_healthy,
                "server_id": server_id,
                "server_name": server.name,
                "connected": is_healthy,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Failed to test connection to server {server_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "server_id": server_id,
                "timestamp": time.time()
            }
    
    async def shutdown(self):
        """Shutdown all MCP components gracefully."""
        try:
            logger.info("Shutting down MCP Orchestrator...")
            
            # Stop internal server first
            if self.internal_server:
                try:
                    await self.internal_server.stop()
                    logger.info("Internal server stopped")
                except Exception as e:
                    logger.error(f"Error stopping internal server: {str(e)}")
            
            # Shutdown connection manager
            try:
                from app.core.mcp_connection_manager import shutdown_connection_manager
                await shutdown_connection_manager()
                logger.info("Connection manager shutdown completed")
            except Exception as e:
                logger.error(f"Error shutting down connection manager: {str(e)}")
            
            # Shutdown server registry
            try:
                if hasattr(self.server_registry, 'shutdown'):
                    await self.server_registry.shutdown()
                elif hasattr(self.server_registry, 'stop_health_monitor'):
                    await self.server_registry.stop_health_monitor()
                logger.info("Server registry shutdown completed")
            except Exception as e:
                logger.error(f"Error shutting down server registry: {str(e)}")
            
            # Shutdown execution engine
            try:
                if hasattr(self.execution_engine, 'shutdown'):
                    await self.execution_engine.shutdown()
                logger.info("Execution engine shutdown completed")
            except Exception as e:
                logger.error(f"Error shutting down execution engine: {str(e)}")
            
            # Clear server references
            self.internal_server = None
            
            # Reset global state
            global _mcp_orchestrator_initialized
            _mcp_orchestrator_initialized = False
            
            logger.info("MCP Orchestrator shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during MCP Orchestrator shutdown: {str(e)}")
            # Don't re-raise - shutdown should be best-effort
    
    # Removed get_internal_tools - functionality available through list_all_tools
    
    # Removed execute_internal_tool - functionality available through execute_tool


# Global instance with proper singleton pattern
_mcp_orchestrator_instance = None
_mcp_orchestrator_initialized = False

def get_mcp_orchestrator() -> MCPOrchestrator:
    """Get the global MCP orchestrator instance."""
    global _mcp_orchestrator_instance
    if _mcp_orchestrator_instance is None:
        _mcp_orchestrator_instance = MCPOrchestrator()
    return _mcp_orchestrator_instance

def get_initialized_mcp_orchestrator() -> MCPOrchestrator:
    """Get the initialized MCP orchestrator instance."""
    global _mcp_orchestrator_instance, _mcp_orchestrator_initialized
    if _mcp_orchestrator_instance is None:
        _mcp_orchestrator_instance = MCPOrchestrator()
    if not _mcp_orchestrator_initialized:
        raise RuntimeError("MCP Orchestrator not yet initialized. Call initialize() first.")
    return _mcp_orchestrator_instance

# Backward compatibility
mcp_orchestrator = get_mcp_orchestrator()