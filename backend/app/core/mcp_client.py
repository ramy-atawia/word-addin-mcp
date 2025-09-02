"""
Custom MCP Client Implementation - Production Ready

This implementation provides a robust, abstracted MCP client with proper error handling,
retry mechanisms, connection pooling, and comprehensive logging.
"""

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum 
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class MCPConnectionState(Enum):
    """MCP connection state."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"
    RECONNECTING = "reconnecting"


class MCPTransportType(Enum):
    """MCP transport types."""
    STDIO = "stdio"
    HTTP = "http"
    WEBSOCKET = "websocket"


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
    """Configuration for MCP server connection."""
    # Server identification
    server_name: str
    server_url: Optional[str] = None
    server_command: Optional[List[str]] = None
    
    # Connection settings
    transport_type: MCPTransportType = MCPTransportType.HTTP
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 5
    
    # Client identification
    client_name: str = "Word-Addin-MCP-Client"
    client_version: str = "1.0.0"
    
    # Health monitoring (disabled for external servers to prevent constant reconnection)
    health_check_interval: int = 60    # Default: 1 minute
    heartbeat_interval: int = 30       # Default: 30 seconds
    
    # Tool caching
    tool_cache_ttl: int = 300  # 5 minutes
    
    def __post_init__(self):
        """Validate configuration."""
        if self.transport_type == MCPTransportType.HTTP and not self.server_url:
            raise ValueError("server_url is required for HTTP transport")
        if self.transport_type == MCPTransportType.STDIO and not self.server_command:
            raise ValueError("server_command is required for STDIO transport")


class MCPTransport(ABC):
    """Abstract base class for MCP transports."""
    
    def __init__(self, config: MCPConnectionConfig):
        self.config = config
        self.connection_id = str(uuid.uuid4())
        self.state = MCPConnectionState.DISCONNECTED
        self.last_error: Optional[str] = None
        self.connection_time: Optional[datetime] = None
        
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the MCP server."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        pass
    
    @abstractmethod
    async def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a JSON-RPC request to the MCP server."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Perform a health check."""
        pass
    
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        return self.state == MCPConnectionState.CONNECTED


class StdioTransport(MCPTransport):
    """STDIO transport for local MCP servers."""
    
    def __init__(self, config: MCPConnectionConfig):
        super().__init__(config)
        self.process: Optional[asyncio.subprocess.Process] = None
        self.request_id = 0
        
    async def connect(self) -> bool:
        """Connect to MCP server via STDIO."""
        try:
            logger.info(f"Connecting to MCP server via STDIO: {' '.join(self.config.server_command)}")
            self.state = MCPConnectionState.CONNECTING
            
            # Start the server process
            self.process = await asyncio.create_subprocess_exec(
                *self.config.server_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Initialize the MCP connection
            init_response = await self.send_request("initialize", {
                "protocolVersion": "1.0.0",
                "capabilities": {},
                "clientInfo": {
                    "name": self.config.client_name,
                    "version": self.config.client_version
                }
            })
            
            if init_response.get("result"):
                self.state = MCPConnectionState.CONNECTED
                self.connection_time = datetime.now()
                logger.info(f"Successfully connected to MCP server via STDIO")
                return True
            else:
                self.state = MCPConnectionState.FAILED
                self.last_error = "Initialization failed"
                return False
                
        except Exception as e:
            self.state = MCPConnectionState.FAILED
            self.last_error = str(e)
            logger.error(f"STDIO connection failed: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        try:
            if self.process and self.process.returncode is None:
                self.process.terminate()
                await self.process.wait()
            self.state = MCPConnectionState.DISCONNECTED
            logger.info("STDIO transport disconnected")
        except Exception as e:
            logger.error(f"Error during STDIO disconnect: {e}")
    
    async def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send JSON-RPC request via STDIO."""
        if not self.process or self.process.returncode is not None:
            raise MCPConnectionError("Not connected to server")
        
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        try:
            # Send request
            request_data = json.dumps(request) + "\n"
            self.process.stdin.write(request_data.encode())
            await self.process.stdin.drain()
            
            # Read response
            response_data = await self.process.stdout.readline()
            if not response_data:
                raise MCPConnectionError("No response from server")
            
            response = json.loads(response_data.decode().strip())
            
            if "error" in response:
                raise MCPProtocolError(f"Server error: {response['error']}")
            
            return response
            
        except Exception as e:
            logger.error(f"STDIO request failed: {e}")
            raise MCPConnectionError(f"Request failed: {e}")
    
    async def health_check(self) -> bool:
        """Perform health check via ping."""
        try:
            response = await self.send_request("ping")
            return response.get("result") is not None
        except:
            return False


class HTTPTransport(MCPTransport):
    """HTTP transport for remote MCP servers."""
    
    def __init__(self, config: MCPConnectionConfig):
        super().__init__(config)
        self.session: Optional[Any] = None  # aiohttp.ClientSession
        self.request_id = 0
        self.session_id: Optional[str] = None  # MCP session ID from server
        self.server_capabilities: Dict[str, Any] = {}  # Server capabilities from initialize
        self.server_info: Dict[str, Any] = {}  # Server info from initialize
        
    async def connect(self) -> bool:
        """Connect to MCP server via HTTP with complete MCP lifecycle."""
        try:
            import aiohttp
            
            logger.info(f"Connecting to MCP server via HTTP: {self.config.server_url}")
            self.state = MCPConnectionState.CONNECTING
            
            # Create HTTP session with SSE support
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            headers = {
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json"
            }
            
            # Create session and ensure cleanup on failure
            session = None
            try:
                session = aiohttp.ClientSession(timeout=timeout, headers=headers)
                self.session = session
                
                # STEP 1: Initialize MCP connection
                logger.info(f"Step 1: Sending initialize request to {self.config.server_url}")
                init_response = await self.send_request("initialize", {
                    "protocolVersion": "2025-06-18",  # Use latest MCP protocol version
                    "capabilities": {
                        "roots": {"listChanged": True},      # Client supports roots
                        "sampling": {},                      # Client supports sampling
                        "elicitation": {}                    # Client supports elicitation
                    },
                    "clientInfo": {
                        "name": self.config.client_name,
                        "title": f"{self.config.client_name} Client",  # Human-readable title
                        "version": self.config.client_version
                    }
                })
                
                if not init_response.get("result"):
                    self.state = MCPConnectionState.FAILED
                    self.last_error = "MCP initialization failed - no result"
                    logger.error(f"Initialize failed: {init_response}")
                    return False

                # Check if this server requires session IDs
                if not self.session_id:
                    logger.warning("No session ID received - server may require it for subsequent requests")
                else:
                    logger.info(f"MCP initialization successful with session ID: {self.session_id}")
                
                # STEP 3: Send initialized notification (OPTIONAL in MCP spec)
                try:
                    logger.info(f"Step 3: Sending initialized notification")
                    await self.send_request("notifications/initialized")  # No params needed per MCP spec
                    logger.info("Initialized notification sent successfully")
                except Exception as e:
                    logger.info(f"Initialized notification not supported by server: {e}, continuing...")
                    # This is optional, so we continue without it
                
                # STEP 4: Test tool discovery to verify connection (with timeout handling)
                try:
                    logger.info(f"Step 4: Testing tool discovery")
                    # Use HTTP-level timeout, not async timeout per MCP spec
                    tools_response = await self.send_request("tools/list")  # No params needed per MCP spec
                    
                    if tools_response.get("result", {}).get("tools"):
                        tool_count = len(tools_response["result"]["tools"])
                        logger.info(f"Successfully discovered {tool_count} tools")
                    else:
                        logger.info("No tools discovered (server may not support tools)")
                        
                except Exception as e:
                    logger.info(f"Tool discovery test failed: {e}, but connection established")
                    # Don't fail the connection for tool discovery issues
                
                # Connection successful
                self.state = MCPConnectionState.CONNECTED
                self.connection_time = datetime.now()
                logger.info(f"Successfully connected to MCP server via HTTP")
                logger.info(f"MCP Session ID: {self.session_id}")
                return True
                        
            except aiohttp.ClientError as e:
                self.state = MCPConnectionState.FAILED
                self.last_error = f"HTTP error: {e}"
                logger.error(f"HTTP error during connection: {e}")
                return False
            except Exception as e:
                self.state = MCPConnectionState.FAILED
                self.last_error = f"Connection error: {e}"
                logger.error(f"Connection failed: {e}")
                return False
            finally:
                # Clean up session if connection failed
                if session and self.state != MCPConnectionState.CONNECTED:
                    try:
                        await session.close()
                        logger.info("Cleaned up failed connection session")
                    except Exception as cleanup_error:
                        logger.error(f"Error cleaning up session: {cleanup_error}")
                    self.session = None
                
        except ImportError:
            self.state = MCPConnectionState.FAILED
            self.last_error = "aiohttp not available"
            logger.error("aiohttp is required for HTTP transport")
            return False
        except Exception as e:
            self.state = MCPConnectionState.FAILED
            self.last_error = str(e)
            logger.error(f"HTTP connection failed: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            self.state = MCPConnectionState.DISCONNECTED
            logger.info("HTTP transport disconnected")
        except Exception as e:
            logger.error(f"Error during HTTP disconnect: {e}")
    
    async def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send JSON-RPC request via HTTP with proper MCP session handling."""
        if not self.session:
            raise MCPConnectionError("Not connected to server")
        
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method
        }
        
        # Only add params if they exist (MCP spec allows no params)
        if params:
            request["params"] = params
        
        try:
            # Build headers
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
            
            # Add session ID for subsequent requests (not for initialize)
            if method != "initialize" and self.session_id:
                headers["Mcp-Session-Id"] = self.session_id
                logger.debug(f"Added session ID header: {self.session_id[:8]}...")
            
            logger.debug(f"Sending {method} request to {self.config.server_url}")
            async with self.session.post(
                self.config.server_url,
                json=request,
                headers=headers
            ) as response:
                if response.status != 200:
                    response_text = await response.text()
                    logger.error(f"HTTP {response.status} error: {response_text}")
                    raise MCPConnectionError(f"HTTP {response.status}: {response_text}")
                
                # Handle SSE response FIRST
                if response.headers.get("content-type", "").startswith("text/event-stream"):
                    response_data = await self._parse_sse_response(response)
                else:
                    response_data = await response.json()
                
                # Check for errors in response
                if "error" in response_data:
                    logger.error(f"Server error in {method}: {response_data['error']}")
                    raise MCPProtocolError(f"Server error: {response_data['error']}")
                
                # Extract session ID from response headers for initialize request
                if method == "initialize":
                    # MCP spec: Check for protocol version in response
                    if "result" in response_data:
                        result = response_data["result"]
                        # Store server capabilities and info
                        self.server_capabilities = result.get("capabilities", {})
                        self.server_info = result.get("serverInfo", {})
                        logger.info(f"Server capabilities: {self.server_capabilities}")
                        logger.info(f"Server info: {self.server_info}")
                    
                    # Check for session ID in response headers (some servers require it)
                    if "mcp-session-id" in response.headers:
                        self.session_id = response.headers["mcp-session-id"]
                        logger.info(f"Received MCP Session ID: {self.session_id}")
                    else:
                        logger.warning("No session ID in initialize response headers")
                
                logger.debug(f"Successfully received response for {method}")
                return response_data
                
        except Exception as e:
            logger.error(f"HTTP request failed for {method}: {e}")
            raise MCPConnectionError(f"Request failed: {e}")
    
    async def _parse_sse_response(self, response) -> Dict[str, Any]:
        """Parse Server-Sent Events response with proper streaming."""
        try:
            # Read SSE stream line by line instead of consuming all at once
            async for line in response.content:
                line_text = line.decode('utf-8').strip()
                
                if line_text.startswith('data: '):
                    data_content = line_text[6:].strip()
                    if data_content:
                        try:
                            parsed_data = json.loads(data_content)
                            logger.debug(f"Successfully parsed SSE data: {parsed_data}")
                            return parsed_data
                        except json.JSONDecodeError as e:
                            logger.warning(f"Invalid JSON in SSE data: {e}")
                            continue
                
                elif line_text.startswith('event: '):
                    event_type = line_text[7:].strip()
                    logger.debug(f"SSE event: {event_type}")
                
                elif line_text == '':
                    # Empty line - end of SSE message
                    continue
                
                else:
                    logger.debug(f"SSE line: {line_text}")
            
            # If we get here, no valid data was found
            logger.warning("No valid data found in SSE stream")
            return {}
            
        except asyncio.TimeoutError:
            logger.error("SSE parsing timed out")
            raise
        except Exception as e:
            logger.error(f"SSE parsing failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise MCPProtocolError(f"SSE parsing failed: {e}")
    
    async def health_check(self) -> bool:
        """Perform health check via HTTP."""
        try:
            if not self.session:
                return False
            async with self.session.get(self.config.server_url) as response:
                return response.status == 200
        except:
            return False


class MCPClient:
    """Production-ready MCP client with robust error handling and connection management."""
    
    def __init__(self, config: MCPConnectionConfig):
        self.config = config
        self.transport: Optional[MCPTransport] = None
        self.connection_lock = asyncio.Lock()
        
        # Caching
        self.tool_cache: List[Dict[str, Any]] = []
        self.tool_cache_time: Optional[datetime] = None
        
        # Monitoring
        self.connection_attempts = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.last_heartbeat: Optional[datetime] = None
        
        # Health monitoring
        self.health_monitor_task: Optional[asyncio.Task] = None
        
        logger.info(f"MCP Client initialized for {config.server_name}")
    
    def _create_transport(self) -> MCPTransport:
        """Create appropriate transport based on configuration."""
        if self.config.transport_type == MCPTransportType.STDIO:
            return StdioTransport(self.config)
        elif self.config.transport_type == MCPTransportType.HTTP:
            return HTTPTransport(self.config)
        else:
            raise ValueError(f"Unsupported transport type: {self.config.transport_type}")
    
    async def connect(self) -> bool:
        """Connect to MCP server with retry logic."""
        async with self.connection_lock:
            if self.is_connected():
                return True
            
            for attempt in range(self.config.max_retries):
                transport = None
                try:
                    self.connection_attempts += 1
                    logger.info(f"Connection attempt {attempt + 1}/{self.config.max_retries} to {self.config.server_name}")
                    
                    # Create transport
                    transport = self._create_transport()
                    
                    # Attempt connection
                    if await transport.connect():
                        # Connection successful, assign to self.transport
                        self.transport = transport
                        # Start health monitoring
                        await self._start_health_monitoring()
                        logger.info(f"Successfully connected to {self.config.server_name}")
                        return True
                    else:
                        logger.warning(f"Connection attempt {attempt + 1} failed")
                        # Clean up failed transport
                        if transport:
                            await transport.disconnect()
                        if attempt < self.config.max_retries - 1:
                            await asyncio.sleep(self.config.retry_delay)
                
                except Exception as e:
                    logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                    # Clean up failed transport
                    if transport:
                        try:
                            await transport.disconnect()
                        except Exception as cleanup_error:
                            logger.error(f"Error cleaning up transport: {cleanup_error}")
                    if attempt < self.config.max_retries - 1:
                        await asyncio.sleep(self.config.retry_delay)
            
            logger.error(f"Failed to connect to {self.config.server_name} after {self.config.max_retries} attempts")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        async with self.connection_lock:
            # Stop health monitoring
            if self.health_monitor_task and not self.health_monitor_task.done():
                self.health_monitor_task.cancel()
                try:
                    await self.health_monitor_task
                except asyncio.CancelledError:
                    pass
            
            # Disconnect transport
            if self.transport:
                await self.transport.disconnect()
                self.transport = None
            
            logger.info(f"Disconnected from {self.config.server_name}")
    
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self.transport is not None and self.transport.is_connected()
    
    async def discover_tools(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Discover available tools with proper MCP lifecycle and caching."""
        # Check cache first
        if not force_refresh and self._is_tool_cache_valid():
            logger.debug(f"Returning cached tools for {self.config.server_name}")
            return self.tool_cache.copy()
        
        if not self.is_connected():
            logger.info(f"Not connected to {self.config.server_name}, connecting first...")
            if not await self.connect():
                logger.error(f"Failed to connect to {self.config.server_name}")
                return []
        
        try:
            logger.info(f"Discovering tools from {self.config.server_name}")
            response = await self.transport.send_request("tools/list")
            
            if "result" in response and "tools" in response["result"]:
                tools = response["result"]["tools"]
                
                # Update cache
                self.tool_cache = tools
                self.tool_cache_time = datetime.now()
                
                self.successful_requests += 1
                logger.info(f"Successfully discovered {len(tools)} tools from {self.config.server_name}")
                
                # Log tool details for debugging
                for tool in tools:
                    logger.debug(f"Tool: {tool.get('name', 'Unknown')} - {tool.get('description', 'No description')[:50]}...")
                
                return tools
            else:
                logger.warning(f"Invalid tools list response from {self.config.server_name}: {response}")
                return []
                
        except Exception as e:
            self.failed_requests += 1
            logger.error(f"Tool discovery failed for {self.config.server_name}: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            return []
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a tool with error handling."""
        if not self.is_connected():
            raise MCPConnectionError("Not connected to server")
        
        if parameters is None:
            parameters = {}
        
        try:
            logger.info(f"Executing tool '{tool_name}' on {self.config.server_name}")
            start_time = time.time()
            
            response = await self.transport.send_request("tools/call", {
                "name": tool_name,
                "arguments": parameters
            })
            
            execution_time = time.time() - start_time
            
            if "result" in response:
                self.successful_requests += 1
                logger.info(f"Tool '{tool_name}' executed successfully in {execution_time:.2f}s")
                return response["result"]
            else:
                raise MCPProtocolError("Invalid tool execution response")
                
        except Exception as e:
            self.failed_requests += 1
            logger.error(f"Tool execution failed for '{tool_name}' on {self.config.server_name}: {e}")
            raise MCPToolError(f"Tool execution failed: {e}")
    
    async def health_check(self) -> bool:
        """Perform a health check."""
        try:
            if not self.transport:
                return False
            return await self.transport.health_check()
        except:
            return False
    
    def _is_tool_cache_valid(self) -> bool:
        """Check if tool cache is still valid."""
        if not self.tool_cache or not self.tool_cache_time:
            return False
        
        cache_age = datetime.now() - self.tool_cache_time
        return cache_age < timedelta(seconds=self.config.tool_cache_ttl)
    
    async def _start_health_monitoring(self):
        """Start periodic health monitoring."""
        if self.health_monitor_task:
            return
        
        # Skip health monitoring for external servers to prevent constant reconnection
        if self.config.server_url and "remote.mcpservers.org" in self.config.server_url:
            logger.info(f"Health monitoring disabled for external server: {self.config.server_name}")
            return
        
        async def health_monitor():
            while self.is_connected():
                try:
                    await asyncio.sleep(self.config.health_check_interval)
                    
                    if await self.health_check():
                        self.last_heartbeat = datetime.now()
                    else:
                        logger.warning(f"Health check failed for {self.config.server_name}")
                        break
                        
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Health monitoring error for {self.config.server_name}: {e}")
                    break
        
        self.health_monitor_task = asyncio.create_task(health_monitor())
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get comprehensive connection status."""
        return {
            "server_name": self.config.server_name,
            "connection_id": self.transport.connection_id if self.transport else None,
            "state": self.transport.state.value if self.transport else "no_transport",
            "is_connected": self.is_connected(),
            "transport_type": self.config.transport_type.value,
            "connection_attempts": self.connection_attempts,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "tool_cache_size": len(self.tool_cache),
            "connection_time": self.transport.connection_time.isoformat() if self.transport and self.transport.connection_time else None,
            "last_error": self.transport.last_error if self.transport else None
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()


class MCPClientFactory:
    """Factory for creating MCP clients with different configurations."""
    
    @staticmethod
    def create_http_client(server_url: str, server_name: str = None, timeout: int = 30) -> MCPClient:
        """Create an HTTP-based MCP client."""
        # Set longer health check intervals for external servers to prevent constant reconnection
        health_check_interval = 3600 if "remote.mcpservers.org" in server_url else 60
        heartbeat_interval = 1800 if "remote.mcpservers.org" in server_url else 30
        
        config = MCPConnectionConfig(
            server_name=server_name or server_url,
            server_url=server_url,
            transport_type=MCPTransportType.HTTP,
            timeout=timeout,
            health_check_interval=health_check_interval,
            heartbeat_interval=heartbeat_interval
        )
        return MCPClient(config)
    
    @staticmethod
    def create_stdio_client(server_command: List[str], server_name: str = None, timeout: int = 30) -> MCPClient:
        """Create a STDIO-based MCP client."""
        config = MCPConnectionConfig(
            server_name=server_name or " ".join(server_command),
            server_command=server_command,
            transport_type=MCPTransportType.STDIO,
            timeout=timeout
        )
        return MCPClient(config)


