"""
MCP Client Connection Management for Word Add-in MCP Project.

This module provides robust connection management for MCP servers including:
- Connection establishment and pooling
- Automatic reconnection on failure
- Connection health monitoring
- Proper resource cleanup
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import aiohttp
import structlog

logger = structlog.get_logger()


class ConnectionStatus(Enum):
    """MCP connection status enumeration."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"
    RECONNECTING = "reconnecting"


@dataclass
class MCPConnectionConfig:
    """Configuration for MCP server connection."""
    server_url: str
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    health_check_interval: float = 30.0
    connection_pool_size: int = 5


@dataclass
class MCPConnectionInfo:
    """Information about an MCP connection."""
    server_url: str
    status: ConnectionStatus
    last_heartbeat: float
    connection_id: str
    capabilities: Dict[str, Any]
    error_count: int = 0
    last_error: Optional[str] = None


class MCPConnectionPool:
    """Connection pool for managing multiple MCP server connections."""
    
    def __init__(self, config: MCPConnectionConfig):
        self.config = config
        self.connections: Dict[str, MCPConnectionInfo] = {}
        self.connection_semaphore = asyncio.Semaphore(config.connection_pool_size)
        self.health_check_task: Optional[asyncio.Task] = None
        self._shutdown = False
    
    async def get_connection(self, server_url: str) -> Optional['MCPClient']:
        """Get a connection from the pool, creating if necessary."""
        async with self.connection_semaphore:
            if server_url not in self.connections:
                await self._create_connection(server_url)
            
            connection_info = self.connections.get(server_url)
            if connection_info and connection_info.status == ConnectionStatus.CONNECTED:
                return MCPClient(server_url, self.config)
            
            return None
    
    async def _create_connection(self, server_url: str):
        """Create a new connection to an MCP server."""
        connection_id = f"mcp_{int(time.time() * 1000)}"
        
        connection_info = MCPConnectionInfo(
            server_url=server_url,
            status=ConnectionStatus.CONNECTING,
            last_heartbeat=time.time(),
            connection_id=connection_id,
            capabilities={}
        )
        
        self.connections[server_url] = connection_info
        
        try:
            # Test connection
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{server_url}/health", timeout=self.config.timeout) as response:
                    if response.status == 200:
                        connection_info.status = ConnectionStatus.CONNECTED
                        logger.info("MCP connection established", server_url=server_url, connection_id=connection_id)
                    else:
                        connection_info.status = ConnectionStatus.FAILED
                        connection_info.last_error = f"HTTP {response.status}"
                        logger.error("MCP connection failed", server_url=server_url, status=response.status)
        except Exception as e:
            connection_info.status = ConnectionStatus.FAILED
            connection_info.last_error = str(e)
            logger.error("MCP connection failed", server_url=server_url, error=str(e))
    
    async def start_health_monitoring(self):
        """Start health monitoring for all connections."""
        if self.health_check_task:
            return
        
        self.health_check_task = asyncio.create_task(self._health_monitor_loop())
        logger.info("MCP connection health monitoring started")
    
    async def _health_monitor_loop(self):
        """Health monitoring loop for all connections."""
        while not self._shutdown:
            try:
                for server_url, connection_info in self.connections.items():
                    await self._check_connection_health(server_url, connection_info)
                
                await asyncio.sleep(self.config.health_check_interval)
            except Exception as e:
                logger.error("Health monitoring error", error=str(e))
                await asyncio.sleep(5.0)  # Brief pause on error
    
    async def _check_connection_health(self, server_url: str, connection_info: MCPConnectionInfo):
        """Check health of a specific connection."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{server_url}/health", timeout=10) as response:
                    if response.status == 200:
                        connection_info.status = ConnectionStatus.CONNECTED
                        connection_info.last_heartbeat = time.time()
                        connection_info.error_count = 0
                        connection_info.last_error = None
                    else:
                        await self._handle_connection_failure(server_url, connection_info, f"HTTP {response.status}")
        except Exception as e:
            await self._handle_connection_failure(server_url, connection_info, str(e))
    
    async def _handle_connection_failure(self, server_url: str, connection_info: MCPConnectionInfo, error: str):
        """Handle connection failure and attempt reconnection."""
        connection_info.error_count += 1
        connection_info.last_error = error
        connection_info.status = ConnectionStatus.FAILED
        
        logger.warning("MCP connection health check failed", 
                      server_url=server_url, 
                      error=error, 
                      error_count=connection_info.error_count)
        
        if connection_info.error_count <= self.config.max_retries:
            await self._attempt_reconnection(server_url, connection_info)
    
    async def _attempt_reconnection(self, server_url: str, connection_info: MCPConnectionInfo):
        """Attempt to reconnect to an MCP server."""
        connection_info.status = ConnectionStatus.RECONNECTING
        
        try:
            await asyncio.sleep(self.config.retry_delay * connection_info.error_count)
            await self._create_connection(server_url)
        except Exception as e:
            logger.error("MCP reconnection failed", server_url=server_url, error=str(e))
    
    async def shutdown(self):
        """Shutdown the connection pool and cleanup resources."""
        self._shutdown = True
        
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        
        # Cleanup connections
        for server_url in list(self.connections.keys()):
            await self._cleanup_connection(server_url)
        
        logger.info("MCP connection pool shutdown complete")
    
    async def _cleanup_connection(self, server_url: str):
        """Cleanup a specific connection."""
        if server_url in self.connections:
            connection_info = self.connections[server_url]
            connection_info.status = ConnectionStatus.DISCONNECTED
            del self.connections[server_url]
            logger.info("MCP connection cleaned up", server_url=server_url)


class MCPClient:
    """Individual MCP client for communicating with a specific MCP server."""
    
    def __init__(self, server_url: str, config: MCPConnectionConfig):
        self.server_url = server_url
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self._connection_established = False
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self):
        """Establish connection to MCP server."""
        if self._connection_established:
            return
        
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
            
            # Test connection
            async with self.session.get(f"{self.server_url}/health") as response:
                if response.status == 200:
                    self._connection_established = True
                    logger.info("MCP client connected", server_url=self.server_url)
                else:
                    raise ConnectionError(f"Failed to connect: HTTP {response.status}")
                    
        except Exception as e:
            logger.error("MCP client connection failed", server_url=self.server_url, error=str(e))
            raise
    
    async def disconnect(self):
        """Disconnect from MCP server."""
        if self.session:
            await self.session.close()
            self.session = None
        
        self._connection_established = False
        logger.info("MCP client disconnected", server_url=self.server_url)
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool on the server."""
        if not self._connection_established:
            raise ConnectionError("Client not connected")
        
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": f"call_{int(time.time() * 1000)}",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": parameters
                }
            }
            
            async with self.session.post(
                f"{self.server_url}/jsonrpc",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("result", {})
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"Tool call failed: HTTP {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error("MCP tool call failed", 
                        server_url=self.server_url, 
                        tool_name=tool_name, 
                        error=str(e))
            raise
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools on the MCP server."""
        if not self._connection_established:
            raise ConnectionError("Client not connected")
        
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": f"list_{int(time.time() * 1000)}",
                "method": "tools/list",
                "params": {}
            }
            
            async with self.session.post(
                f"{self.server_url}/jsonrpc",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("result", {}).get("tools", [])
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"Tool listing failed: HTTP {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error("MCP tool listing failed", 
                        server_url=self.server_url, 
                        error=str(e))
            raise
    
    async def get_server_info(self) -> Dict[str, Any]:
        """Get MCP server information and capabilities."""
        if not self._connection_established:
            raise ConnectionError("Client not connected")
        
        try:
            async with self.session.get(f"{self.server_url}/health") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise RuntimeError(f"Server info failed: HTTP {response.status}")
                    
        except Exception as e:
            logger.error("MCP server info failed", 
                        server_url=self.server_url, 
                        error=str(e))
            raise


class MCPClientManager:
    """Manager for multiple MCP clients and connection pools."""
    
    def __init__(self):
        self.connection_pools: Dict[str, MCPConnectionPool] = {}
        self._shutdown = False
    
    async def create_connection_pool(self, config: MCPConnectionConfig) -> MCPConnectionPool:
        """Create a new connection pool for MCP servers."""
        pool = MCPConnectionPool(config)
        self.connection_pools[config.server_url] = pool
        
        # Start health monitoring
        await pool.start_health_monitoring()
        
        logger.info("MCP connection pool created", server_url=config.server_url)
        return pool
    
    async def get_client(self, server_url: str) -> Optional[MCPClient]:
        """Get an MCP client for a specific server."""
        for pool in self.connection_pools.values():
            if pool.config.server_url == server_url:
                return await pool.get_connection(server_url)
        return None
    
    async def shutdown(self):
        """Shutdown all connection pools."""
        self._shutdown = True
        
        shutdown_tasks = []
        for pool in self.connection_pools.values():
            shutdown_tasks.append(pool.shutdown())
        
        if shutdown_tasks:
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)
        
        self.connection_pools.clear()
        logger.info("MCP client manager shutdown complete")


# Global instance for application-wide use
mcp_client_manager = MCPClientManager()
