"""
Unit tests for MCP Client Connection Management.

Tests the MCP client functionality including:
- Connection establishment and pooling
- Automatic reconnection on failure
- Connection health monitoring
- Proper resource cleanup
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from aiohttp import ClientResponseError, ClientTimeout

from app.core.mcp_client import (
    ConnectionStatus,
    MCPConnectionConfig,
    MCPConnectionInfo,
    MCPConnectionPool,
    MCPClient,
    MCPClientManager
)


class TestMCPConnectionConfig:
    """Test MCP connection configuration."""
    
    def test_connection_config_defaults(self):
        """Test connection config with default values."""
        config = MCPConnectionConfig(server_url="http://localhost:9000")
        
        assert config.server_url == "http://localhost:9000"
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.health_check_interval == 30.0
        assert config.connection_pool_size == 5
    
    def test_connection_config_custom_values(self):
        """Test connection config with custom values."""
        config = MCPConnectionConfig(
            server_url="http://localhost:9000",
            timeout=60,
            max_retries=5,
            retry_delay=2.0,
            health_check_interval=60.0,
            connection_pool_size=10
        )
        
        assert config.server_url == "http://localhost:9000"
        assert config.timeout == 60
        assert config.max_retries == 5
        assert config.retry_delay == 2.0
        assert config.health_check_interval == 60.0
        assert config.connection_pool_size == 10


class TestMCPConnectionInfo:
    """Test MCP connection information."""
    
    def test_connection_info_creation(self):
        """Test creating connection info."""
        conn_info = MCPConnectionInfo(
            server_url="http://localhost:9000",
            status=ConnectionStatus.CONNECTED,
            last_heartbeat=time.time(),
            connection_id="test-123",
            capabilities={"tools": ["file_reader"]}
        )
        
        assert conn_info.server_url == "http://localhost:9000"
        assert conn_info.status == ConnectionStatus.CONNECTED
        assert conn_info.connection_id == "test-123"
        assert conn_info.capabilities == {"tools": ["file_reader"]}
        assert conn_info.error_count == 0
        assert conn_info.last_error is None
    
    def test_connection_info_with_errors(self):
        """Test connection info with error information."""
        conn_info = MCPConnectionInfo(
            server_url="http://localhost:9000",
            status=ConnectionStatus.FAILED,
            last_heartbeat=time.time(),
            connection_id="test-123",
            capabilities={},
            error_count=2,
            last_error="Connection timeout"
        )
        
        assert conn_info.error_count == 2
        assert conn_info.last_error == "Connection timeout"


class TestMCPConnectionPool:
    """Test MCP connection pool functionality."""
    
    @pytest.fixture
    def connection_config(self):
        """Create a test connection configuration."""
        return MCPConnectionConfig(
            server_url="http://localhost:9000",
            timeout=5,
            max_retries=2,
            retry_delay=0.1,
            health_check_interval=0.1,
            connection_pool_size=2
        )
    
    @pytest.fixture
    def connection_pool(self, connection_config):
        """Create a test connection pool."""
        return MCPConnectionPool(connection_config)
    
    async def test_connection_pool_creation(self, connection_config):
        """Test creating a connection pool."""
        pool = MCPConnectionPool(connection_config)
        
        assert pool.config == connection_config
        assert len(pool.connections) == 0
        assert pool.health_check_task is None
        assert not pool._shutdown
    
    async def test_connection_pool_semaphore(self, connection_pool):
        """Test connection pool semaphore limits."""
        assert connection_pool.connection_semaphore._value == 2
    
    @patch('aiohttp.ClientSession')
    async def test_create_connection_success(self, mock_session_class, connection_pool):
        """Test successful connection creation."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status = 200
        
        # Create a proper mock for the async context manager chain
        mock_context = Mock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        
        # Mock the ClientSession constructor and its async context manager
        mock_session_instance = Mock()
        mock_session_instance.__aenter__ = AsyncMock(return_value=mock_context)
        mock_session_instance.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session_instance
        
        await connection_pool._create_connection("http://localhost:9000")
        
        assert "http://localhost:9000" in connection_pool.connections
        conn_info = connection_pool.connections["http://localhost:9000"]
        assert conn_info.status == ConnectionStatus.CONNECTED
        assert conn_info.connection_id.startswith("mcp_")
    
    @patch('aiohttp.ClientSession')
    async def test_create_connection_failure(self, mock_session_class, connection_pool):
        """Test connection creation failure."""
        # Mock failed HTTP response
        mock_response = Mock()
        mock_response.status = 500
        
        # Create a proper mock for the async context manager chain
        mock_context = Mock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        
        # Mock the ClientSession constructor and its async context manager
        mock_session_instance = Mock()
        mock_session_instance.__aenter__ = AsyncMock(return_value=mock_context)
        mock_session_instance.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session_instance
        
        await connection_pool._create_connection("http://localhost:9000")
        
        conn_info = connection_pool.connections["http://localhost:9000"]
        assert conn_info.status == ConnectionStatus.FAILED
        assert conn_info.last_error == "HTTP 500"
    
    @patch('aiohttp.ClientSession')
    async def test_create_connection_exception(self, mock_session_class, connection_pool):
        """Test connection creation with exception."""
        # Mock exception during connection
        mock_session_class.side_effect = Exception("Network error")
        
        await connection_pool._create_connection("http://localhost:9000")
        
        conn_info = connection_pool.connections["http://localhost:9000"]
        assert conn_info.status == ConnectionStatus.FAILED
        assert conn_info.last_error == "Network error"
    
    async def test_start_health_monitoring(self, connection_pool):
        """Test starting health monitoring."""
        await connection_pool.start_health_monitoring()
        
        assert connection_pool.health_check_task is not None
        assert not connection_pool.health_check_task.done()
        
        # Cleanup
        connection_pool._shutdown = True
        if connection_pool.health_check_task:
            connection_pool.health_check_task.cancel()
    
    @patch('aiohttp.ClientSession')
    async def test_health_check_success(self, mock_session_class, connection_pool):
        """Test successful health check."""
        # Setup connection
        conn_info = MCPConnectionInfo(
            server_url="http://localhost:9000",
            status=ConnectionStatus.CONNECTED,
            last_heartbeat=time.time(),
            connection_id="test-123",
            capabilities={}
        )
        connection_pool.connections["http://localhost:9000"] = conn_info
        
        # Mock successful health check
        mock_response = Mock()
        mock_response.status = 200
        
        # Create a proper mock for the async context manager chain
        mock_context = Mock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        
        # Mock the ClientSession constructor and its async context manager
        mock_session_instance = Mock()
        mock_session_instance.__aenter__ = AsyncMock(return_value=mock_context)
        mock_session_instance.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session_instance
        
        await connection_pool._check_connection_health("http://localhost:9000", conn_info)
        
        assert conn_info.status == ConnectionStatus.CONNECTED
        assert conn_info.error_count == 0
        assert conn_info.last_error is None
    
    @patch('aiohttp.ClientSession')
    async def test_health_check_failure(self, mock_session_class, connection_pool):
        """Test health check failure."""
        # Setup connection
        conn_info = MCPConnectionInfo(
            server_url="http://localhost:9000",
            status=ConnectionStatus.CONNECTED,
            last_heartbeat=time.time(),
            connection_id="test-123",
            capabilities={}
        )
        connection_pool.connections["http://localhost:9000"] = conn_info
        
        # Mock failed health check
        mock_session_class.side_effect = Exception("Health check failed")
        
        await connection_pool._check_connection_health("http://localhost:9000", conn_info)
        
        assert conn_info.status == ConnectionStatus.FAILED
        assert conn_info.error_count == 1
        assert conn_info.last_error == "Health check failed"
    
    @patch.object(connection_pool, '_attempt_reconnection')
    async def test_handle_connection_failure(self, mock_reconnect, connection_pool):
        """Test handling connection failure."""
        conn_info = MCPConnectionInfo(
            server_url="http://localhost:9000",
            status=ConnectionStatus.CONNECTED,
            last_heartbeat=time.time(),
            connection_id="test-123",
            capabilities={}
        )
        
        await connection_pool._handle_connection_failure("http://localhost:9000", conn_info, "Test error")
        
        assert conn_info.status == ConnectionStatus.FAILED
        assert conn_info.error_count == 1
        assert conn_info.last_error == "Test error"
        mock_reconnect.assert_called_once_with("http://localhost:9000", conn_info)
    
    async def test_attempt_reconnection(self, connection_pool):
        """Test reconnection attempt."""
        conn_info = MCPConnectionInfo(
            server_url="http://localhost:9000",
            status=ConnectionStatus.FAILED,
            last_heartbeat=time.time(),
            connection_id="test-123",
            capabilities={},
            error_count=1
        )
        
        with patch.object(connection_pool, '_create_connection') as mock_create:
            await connection_pool._attempt_reconnection("http://localhost:9000", conn_info)
            
            assert conn_info.status == ConnectionStatus.RECONNECTING
            mock_create.assert_called_once_with("http://localhost:9000")
    
    async def test_shutdown(self, connection_pool):
        """Test connection pool shutdown."""
        # Start health monitoring
        await connection_pool.start_health_monitoring()
        
        # Shutdown
        await connection_pool.shutdown()
        
        assert connection_pool._shutdown
        assert len(connection_pool.connections) == 0


class TestMCPClient:
    """Test individual MCP client functionality."""
    
    @pytest.fixture
    def connection_config(self):
        """Create a test connection configuration."""
        return MCPConnectionConfig(
            server_url="http://localhost:9000",
            timeout=5
        )
    
    @pytest.fixture
    def mcp_client(self, connection_config):
        """Create a test MCP client."""
        return MCPClient("http://localhost:9000", connection_config)
    
    def test_mcp_client_creation(self, connection_config):
        """Test creating an MCP client."""
        client = MCPClient("http://localhost:9000", connection_config)
        
        assert client.server_url == "http://localhost:9000"
        assert client.config == connection_config
        assert client.session is None
        assert not client._connection_established
    
    @patch('aiohttp.ClientSession')
    async def test_connect_success(self, mock_session, mcp_client):
        """Test successful connection."""
        # Mock successful health check
        mock_response = Mock()
        mock_response.status = 200
        
        mock_session.return_value.get.return_value.__aenter__.return_value = mock_response
        
        await mcp_client.connect()
        
        assert mcp_client._connection_established
        assert mcp_client.session is not None
    
    @patch('aiohttp.ClientSession')
    async def test_connect_failure(self, mock_session, mcp_client):
        """Test connection failure."""
        # Mock failed health check
        mock_response = Mock()
        mock_response.status = 500
        
        mock_session.return_value.get.return_value.__aenter__.return_value = mock_response
        
        with pytest.raises(ConnectionError, match="Failed to connect: HTTP 500"):
            await mcp_client.connect()
        
        assert not mcp_client._connection_established
    
    @patch('aiohttp.ClientSession')
    async def test_connect_exception(self, mock_session, mcp_client):
        """Test connection with exception."""
        # Mock exception during connection
        mock_session.return_value.get.side_effect = Exception("Network error")
        
        with pytest.raises(Exception, match="Network error"):
            await mcp_client.connect()
        
        assert not mcp_client._connection_established
    
    async def test_disconnect(self, mcp_client):
        """Test disconnection."""
        # Mock session
        mcp_client.session = Mock()
        mcp_client._connection_established = True
        
        await mcp_client.disconnect()
        
        assert not mcp_client._connection_established
        assert mcp_client.session is None
    
    @patch('aiohttp.ClientSession')
    async def test_call_tool_success(self, mock_session, mcp_client):
        """Test successful tool call."""
        # Setup connected client
        mcp_client._connection_established = True
        mcp_client.session = Mock()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"result": {"output": "test"}})
        
        mcp_client.session.post.return_value.__aenter__.return_value = mock_response
        
        result = await mcp_client.call_tool("test_tool", {"param": "value"})
        
        assert result == {"output": "test"}
    
    async def test_call_tool_not_connected(self, mcp_client):
        """Test tool call without connection."""
        with pytest.raises(ConnectionError, match="Client not connected"):
            await mcp_client.call_tool("test_tool", {"param": "value"})
    
    @patch('aiohttp.ClientSession')
    async def test_list_tools_success(self, mock_session, mcp_client):
        """Test successful tool listing."""
        # Setup connected client
        mcp_client._connection_established = True
        mcp_client.session = Mock()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"result": {"tools": ["tool1", "tool2"]}})
        
        mcp_client.session.post.return_value.__aenter__.return_value = mock_response
        
        tools = await mcp_client.list_tools()
        
        assert tools == ["tool1", "tool2"]
    
    @patch('aiohttp.ClientSession')
    async def test_get_server_info_success(self, mock_session, mcp_client):
        """Test successful server info retrieval."""
        # Setup connected client
        mcp_client._connection_established = True
        mcp_client.session = Mock()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"status": "healthy"})
        
        mcp_client.session.get.return_value.__aenter__.return_value = mock_response
        
        info = await mcp_client.get_server_info()
        
        assert info == {"status": "healthy"}


class TestMCPClientManager:
    """Test MCP client manager functionality."""
    
    @pytest.fixture
    def client_manager(self):
        """Create a test client manager."""
        return MCPClientManager()
    
    @pytest.fixture
    def connection_config(self):
        """Create a test connection configuration."""
        return MCPConnectionConfig(
            server_url="http://localhost:9000",
            timeout=5
        )
    
    async def test_client_manager_creation(self, client_manager):
        """Test creating a client manager."""
        assert len(client_manager.connection_pools) == 0
        assert not client_manager._shutdown
    
    async def test_create_connection_pool(self, client_manager, connection_config):
        """Test creating a connection pool."""
        pool = await client_manager.create_connection_pool(connection_config)
        
        assert pool.config == connection_config
        assert connection_config.server_url in client_manager.connection_pools
        assert client_manager.connection_pools[connection_config.server_url] == pool
        
        # Cleanup
        await pool.shutdown()
    
    async def test_get_client(self, client_manager, connection_config):
        """Test getting a client."""
        # Create pool first
        pool = await client_manager.create_connection_pool(connection_config)
        
        # Mock successful connection
        with patch.object(pool, 'get_connection', return_value=Mock()):
            client = await client_manager.get_client(connection_config.server_url)
            assert client is not None
        
        # Cleanup
        await pool.shutdown()
    
    async def test_get_client_no_pool(self, client_manager):
        """Test getting client when no pool exists."""
        client = await client_manager.get_client("http://nonexistent:9000")
        assert client is None
    
    async def test_shutdown(self, client_manager, connection_config):
        """Test client manager shutdown."""
        # Create a pool
        pool = await client_manager.create_connection_pool(connection_config)
        
        # Shutdown
        await client_manager.shutdown()
        
        assert client_manager._shutdown
        assert len(client_manager.connection_pools) == 0


class TestMCPClientIntegration:
    """Integration tests for MCP client components."""
    
    @pytest.fixture
    def connection_config(self):
        """Create a test connection configuration."""
        return MCPConnectionConfig(
            server_url="http://localhost:9000",
            timeout=5,
            max_retries=2,
            retry_delay=0.1,
            health_check_interval=0.1,
            connection_pool_size=2
        )
    
    async def test_full_connection_lifecycle(self, connection_config):
        """Test full connection lifecycle."""
        # Create pool
        pool = MCPConnectionPool(connection_config)
        
        # Start health monitoring
        await pool.start_health_monitoring()
        
        # Wait a bit for health monitoring to run
        await asyncio.sleep(0.2)
        
        # Shutdown
        await pool.shutdown()
        
        assert pool._shutdown
        assert len(pool.connections) == 0
    
    async def test_client_manager_integration(self, connection_config):
        """Test client manager integration."""
        # Create manager
        manager = MCPClientManager()
        
        # Create pool
        pool = await manager.create_connection_pool(connection_config)
        
        # Get client
        client = await manager.get_client(connection_config.server_url)
        
        # Shutdown
        await manager.shutdown()
        
        assert manager._shutdown
        assert len(manager.connection_pools) == 0
