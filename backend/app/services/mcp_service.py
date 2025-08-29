"""
MCP Service for Word Add-in MCP Project.

This service integrates MCP client functionality with the existing MCP API,
providing a clean service layer for MCP operations.
"""

import asyncio
from typing import Dict, Any, List, Optional
import structlog

from app.core.mcp_client import (
    MCPClient, 
    MCPConnectionConfig, 
    mcp_client_manager,
    ConnectionStatus
)
from app.core.config import settings

logger = structlog.get_logger()


class MCPService:
    """Service for managing MCP operations and connections."""
    
    def __init__(self):
        self.initialized = False
        self._connection_configs: Dict[str, MCPConnectionConfig] = {}
    
    async def initialize(self):
        """Initialize the MCP service with connection configurations."""
        if self.initialized:
            return
        
        try:
            # Create connection configuration for the main MCP server
            main_config = MCPConnectionConfig(
                server_url=settings.MCP_SERVER_URL,
                timeout=30,
                max_retries=3,
                retry_delay=1.0,
                health_check_interval=30.0,
                connection_pool_size=5
            )
            
            # Create connection pool
            await mcp_client_manager.create_connection_pool(main_config)
            self._connection_configs[settings.MCP_SERVER_URL] = main_config
            
            self.initialized = True
            logger.info("MCP service initialized successfully", 
                       server_url=settings.MCP_SERVER_URL)
            
        except Exception as e:
            logger.error("Failed to initialize MCP service", error=str(e))
            raise
    
    async def get_client(self, server_url: str = None) -> Optional[MCPClient]:
        """Get an MCP client for the specified server."""
        if not self.initialized:
            await self.initialize()
        
        server_url = server_url or settings.MCP_SERVER_URL
        return await mcp_client_manager.get_client(server_url)
    
    async def list_available_tools(self, server_url: str = None) -> List[Dict[str, Any]]:
        """List available tools from the MCP server."""
        try:
            client = await self.get_client(server_url)
            if not client:
                logger.warning("No MCP client available", server_url=server_url)
                return []
            
            tools = await client.list_tools()
            logger.info("Retrieved tools from MCP server", 
                       server_url=server_url, 
                       tool_count=len(tools))
            return tools
            
        except Exception as e:
            logger.error("Failed to list MCP tools", 
                        server_url=server_url, 
                        error=str(e))
            return []
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any], 
                          server_url: str = None) -> Dict[str, Any]:
        """Execute a tool on the MCP server."""
        try:
            client = await self.get_client(server_url)
            if not client:
                raise RuntimeError(f"No MCP client available for {server_url}")
            
            result = await client.call_tool(tool_name, parameters)
            logger.info("MCP tool executed successfully", 
                       tool_name=tool_name, 
                       server_url=server_url)
            return result
            
        except Exception as e:
            logger.error("Failed to execute MCP tool", 
                        tool_name=tool_name, 
                        server_url=server_url, 
                        error=str(e))
            raise
    
    async def get_server_status(self, server_url: str = None) -> Dict[str, Any]:
        """Get the status of the MCP server."""
        try:
            client = await self.get_client(server_url)
            if not client:
                return {
                    "status": "disconnected",
                    "error": "No client available"
                }
            
            server_info = await client.get_server_info()
            return {
                "status": "connected",
                "server_info": server_info
            }
            
        except Exception as e:
            logger.error("Failed to get MCP server status", 
                        server_url=server_url, 
                        error=str(e))
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def add_external_mcp_server(self, server_url: str, config: MCPConnectionConfig):
        """Add an external MCP server to the service."""
        try:
            await mcp_client_manager.create_connection_pool(config)
            self._connection_configs[server_url] = config
            
            logger.info("External MCP server added", 
                       server_url=server_url, 
                       config=config)
            
        except Exception as e:
            logger.error("Failed to add external MCP server", 
                        server_url=server_url, 
                        error=str(e))
            raise
    
    async def remove_external_mcp_server(self, server_url: str):
        """Remove an external MCP server from the service."""
        try:
            if server_url in mcp_client_manager.connection_pools:
                pool = mcp_client_manager.connection_pools[server_url]
                await pool.shutdown()
                del mcp_client_manager.connection_pools[server_url]
                
                if server_url in self._connection_configs:
                    del self._connection_configs[server_url]
                
                logger.info("External MCP server removed", server_url=server_url)
            
        except Exception as e:
            logger.error("Failed to remove external MCP server", 
                        server_url=server_url, 
                        error=str(e))
            raise
    
    async def get_all_connections_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all MCP connections."""
        status = {}
        
        for server_url, pool in mcp_client_manager.connection_pools.items():
            try:
                # Get connection info from the pool
                connections = pool.connections
                if server_url in connections:
                    conn_info = connections[server_url]
                    status[server_url] = {
                        "status": conn_info.status.value,
                        "last_heartbeat": conn_info.last_heartbeat,
                        "error_count": conn_info.error_count,
                        "last_error": conn_info.last_error,
                        "capabilities": conn_info.capabilities
                    }
                else:
                    status[server_url] = {
                        "status": "unknown",
                        "error": "No connection info available"
                    }
                    
            except Exception as e:
                status[server_url] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return status
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a comprehensive health check of all MCP connections."""
        try:
            connections_status = await self.get_all_connections_status()
            
            # Check if any connections are healthy
            healthy_connections = 0
            total_connections = len(connections_status)
            
            for server_url, status_info in connections_status.items():
                if status_info.get("status") == "connected":
                    healthy_connections += 1
            
            health_status = {
                "overall_status": "healthy" if healthy_connections > 0 else "unhealthy",
                "total_connections": total_connections,
                "healthy_connections": healthy_connections,
                "connections": connections_status,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            logger.info("MCP service health check completed", 
                       overall_status=health_status["overall_status"],
                       healthy_connections=healthy_connections,
                       total_connections=total_connections)
            
            return health_status
            
        except Exception as e:
            logger.error("MCP service health check failed", error=str(e))
            return {
                "overall_status": "error",
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }
    
    async def shutdown(self):
        """Shutdown the MCP service and cleanup resources."""
        try:
            await mcp_client_manager.shutdown()
            self.initialized = False
            logger.info("MCP service shutdown complete")
            
        except Exception as e:
            logger.error("MCP service shutdown failed", error=str(e))
            raise


# Global instance for application-wide use
mcp_service = MCPService()
