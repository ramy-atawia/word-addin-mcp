"""
MCP Connection Manager - Persistent Connection Pool

This module manages persistent connections to MCP servers to avoid
the overhead of creating new connections for every request.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

import structlog

from app.core.fastmcp_client import FastMCPClient, MCPConnectionConfig, MCPConnectionState

logger = structlog.get_logger()


class ConnectionPoolState(Enum):
    """Connection pool state."""
    IDLE = "idle"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"
    SHUTDOWN = "shutdown"


@dataclass
class PooledConnection:
    """A pooled MCP connection."""
    client: FastMCPClient
    server_url: str
    server_name: str
    created_at: float
    last_used: float
    use_count: int
    is_healthy: bool = True
    last_health_check: float = 0


class MCPConnectionManager:
    """
    Manages persistent connections to MCP servers.
    
    This class maintains a pool of connections to external MCP servers,
    reusing them across requests to avoid the overhead of creating
    new connections for every tool discovery or execution.
    """
    
    def __init__(self, max_connections_per_server: int = 3, connection_ttl: float = 300.0):
        """
        Initialize the connection manager.
        
        Args:
            max_connections_per_server: Maximum connections per server
            connection_ttl: Connection time-to-live in seconds (5 minutes default)
        """
        self.max_connections_per_server = max_connections_per_server
        self.connection_ttl = connection_ttl
        self.connection_pools: Dict[str, List[PooledConnection]] = {}
        self.state = ConnectionPoolState.IDLE
        self.cleanup_task: Optional[asyncio.Task] = None
        self.health_check_interval = 60.0  # Health check every minute
        
        logger.info("MCP Connection Manager initialized")
    
    async def start(self) -> None:
        """Start the connection manager and cleanup task."""
        if self.state != ConnectionPoolState.IDLE:
            return
        
        self.state = ConnectionPoolState.CONNECTING
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.state = ConnectionPoolState.CONNECTED
        
        logger.info("MCP Connection Manager started")
    
    async def stop(self) -> None:
        """Stop the connection manager and close all connections."""
        if self.state == ConnectionPoolState.SHUTDOWN:
            return
        
        self.state = ConnectionPoolState.SHUTDOWN
        
        # Cancel cleanup task
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        for server_url, pool in self.connection_pools.items():
            for connection in pool:
                try:
                    await connection.client.disconnect()
                except Exception as e:
                    logger.warning(f"Error disconnecting from {server_url}: {e}")
        
        self.connection_pools.clear()
        logger.info("MCP Connection Manager stopped")
    
    async def get_connection(self, server_url: str, server_name: str) -> Optional[PooledConnection]:
        """
        Get a connection from the pool or create a new one.
        
        Args:
            server_url: URL of the MCP server
            server_name: Name of the MCP server
            
        Returns:
            PooledConnection or None if failed
        """
        try:
            # Check if we have available connections in the pool
            if server_url in self.connection_pools:
                pool = self.connection_pools[server_url]
                
                # Find a healthy, available connection
                for connection in pool:
                    if (connection.is_healthy and 
                        connection.client.is_connected and
                        not connection.client.state == MCPConnectionState.CONNECTING):
                        
                        # Update usage stats
                        connection.last_used = time.time()
                        connection.use_count += 1
                        
                        logger.debug(f"Reusing connection to {server_name}")
                        return connection
                
                # If we have space for more connections, create one
                if len(pool) < self.max_connections_per_server:
                    connection = await self._create_connection(server_url, server_name)
                    if connection:
                        pool.append(connection)
                        logger.debug(f"Created new connection to {server_name} (pool size: {len(pool)})")
                        return connection
            else:
                # Create new pool for this server
                self.connection_pools[server_url] = []
                connection = await self._create_connection(server_url, server_name)
                if connection:
                    self.connection_pools[server_url].append(connection)
                    logger.debug(f"Created new connection pool for {server_name}")
                    return connection
            
            # If we can't create a new connection, try to reuse an existing one
            if server_url in self.connection_pools:
                pool = self.connection_pools[server_url]
                if pool:
                    # Try to reconnect the oldest connection
                    oldest_connection = min(pool, key=lambda c: c.last_used)
                    if await self._reconnect_connection(oldest_connection):
                        oldest_connection.last_used = time.time()
                        oldest_connection.use_count += 1
                        logger.debug(f"Reconnected to {server_name}")
                        return oldest_connection
            
            logger.warning(f"No available connections to {server_name}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get connection to {server_name}: {e}")
            return None
    
    async def _create_connection(self, server_url: str, server_name: str) -> Optional[PooledConnection]:
        """Create a new connection to an MCP server."""
        try:
            # Use real FastMCP Client through our wrapper
            from app.core.fastmcp_client import FastMCPClientFactory
            
            # Create client based on URL type
            if server_url.startswith(('http://', 'https://')):
                client = FastMCPClientFactory.create_http_client(
                    server_url, 
                    server_name, 
                    timeout=30.0
                )
            elif server_url.startswith(('ws://', 'wss://')):
                client = FastMCPClientFactory.create_websocket_client(
                    server_url,
                    server_name,
                    timeout=30.0
                )
            else:
                # Handle STDIO command
                server_command = server_url.split() if isinstance(server_url, str) else server_url
                client = FastMCPClientFactory.create_stdio_client(
                    server_command, 
                    server_name,
                    timeout=30.0
                )
            
            # Connect to the server
            if await client.connect():
                connection = PooledConnection(
                    client=client,
                    server_url=server_url,
                    server_name=server_name,
                    created_at=time.time(),
                    last_used=time.time(),
                    use_count=1,
                    is_healthy=True,
                    last_health_check=time.time()
                )
                
                logger.info(f"Created new connection to {server_name}")
                return connection
            else:
                logger.error(f"Failed to connect to {server_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating connection to {server_name}: {e}")
            return None
    
    async def _reconnect_connection(self, connection: PooledConnection) -> bool:
        """Reconnect a failed connection."""
        try:
            if connection.client.is_connected():
                return True
            
            # Try to reconnect
            if await connection.client.connect():
                connection.is_healthy = True
                connection.last_health_check = time.time()
                logger.info(f"Reconnected to {connection.server_name}")
                return True
            else:
                connection.is_healthy = False
                logger.warning(f"Failed to reconnect to {connection.server_name}")
                return False
                
        except Exception as e:
            connection.is_healthy = False
            logger.error(f"Error reconnecting to {connection.server_name}: {e}")
            return False
    
    async def _cleanup_loop(self) -> None:
        """Background task to clean up old connections and perform health checks."""
        while self.state != ConnectionPoolState.SHUTDOWN:
            try:
                current_time = time.time()
                
                for server_url, pool in list(self.connection_pools.items()):
                    # Remove expired or unhealthy connections
                    connections_to_remove = []
                    
                    for connection in pool:
                        # Check if connection is expired
                        if current_time - connection.created_at > self.connection_ttl:
                            connections_to_remove.append(connection)
                            logger.debug(f"Removing expired connection to {connection.server_name}")
                            continue
                        
                        # Check if connection needs health check
                        if (current_time - connection.last_health_check > self.health_check_interval and
                            connection.is_healthy):
                            
                            try:
                                is_healthy = await connection.client.health_check()
                                connection.is_healthy = is_healthy
                                connection.last_health_check = current_time
                                
                                if not is_healthy:
                                    logger.warning(f"Health check failed for {connection.server_name}")
                                    connections_to_remove.append(connection)
                                    
                            except Exception as e:
                                logger.warning(f"Health check error for {connection.server_name}: {e}")
                                connection.is_healthy = False
                                connections_to_remove.append(connection)
                    
                    # Remove unhealthy/expired connections
                    for connection in connections_to_remove:
                        try:
                            await connection.client.disconnect()
                        except Exception as e:
                            logger.debug(f"Error disconnecting {connection.server_name}: {e}")
                        pool.remove(connection)
                    
                    # Remove empty pools
                    if not pool:
                        del self.connection_pools[server_url]
                
                # Sleep for 30 seconds before next cleanup
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get statistics about connection pools."""
        stats = {
            "total_servers": len(self.connection_pools),
            "total_connections": sum(len(pool) for pool in self.connection_pools.values()),
            "healthy_connections": 0,
            "unhealthy_connections": 0,
            "servers": {}
        }
        
        for server_url, pool in self.connection_pools.items():
            healthy_count = sum(1 for conn in pool if conn.is_healthy)
            unhealthy_count = len(pool) - healthy_count
            
            stats["healthy_connections"] += healthy_count
            stats["unhealthy_connections"] += unhealthy_count
            
            stats["servers"][server_url] = {
                "total_connections": len(pool),
                "healthy_connections": healthy_count,
                "unhealthy_connections": unhealthy_count,
                "oldest_connection": min((conn.created_at for conn in pool), default=0),
                "newest_connection": max((conn.created_at for conn in pool), default=0)
            }
        
        return stats


# Global connection manager instance
_global_connection_manager: Optional[MCPConnectionManager] = None


async def get_connection_manager() -> MCPConnectionManager:
    """Get the global connection manager instance."""
    global _global_connection_manager
    
    if _global_connection_manager is None:
        _global_connection_manager = MCPConnectionManager()
        await _global_connection_manager.start()
    
    return _global_connection_manager


async def shutdown_connection_manager() -> None:
    """Shutdown the global connection manager."""
    global _global_connection_manager
    
    if _global_connection_manager is not None:
        await _global_connection_manager.stop()
        _global_connection_manager = None
