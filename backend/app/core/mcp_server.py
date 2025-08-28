"""
MCP Server Core Implementation for Word Add-in MCP Project.

This module implements the core MCP server functionality including:
- MCP server initialization and lifecycle management
- Tool registry system integration
- Tool execution engine
- Server capability management
- Server health monitoring
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import structlog

from .mcp_tool_interface import (
    ToolRegistry, 
    ToolExecutionEngine, 
    ToolExecutionContext,
    ToolExecutionResult,
    ToolExecutionStatus,
    ToolErrorCode
)

logger = structlog.get_logger()


class ServerStatus(Enum):
    """MCP server status enumeration."""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class ServerCapability(Enum):
    """MCP server capabilities."""
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    TOOLS_GET = "tools/get"
    CHAT_COMPLETIONS = "chat/completions"
    TEXT_COMPLETIONS = "text/completions"
    EMBEDDINGS = "embeddings"
    FILES_LIST = "files/list"
    FILES_UPLOAD = "files/upload"
    FILES_DELETE = "files/delete"


@dataclass
class ServerCapabilityInfo:
    """Information about a server capability."""
    name: str
    description: str
    version: str = "1.0.0"
    enabled: bool = True
    config: Dict[str, Any] = None


@dataclass
class ServerHealthInfo:
    """Server health information."""
    status: ServerStatus
    uptime: float
    tool_count: int
    active_connections: int
    total_requests: int
    error_rate: float
    last_health_check: float
    capabilities: List[str]
    version: str = "1.0.0"


class MCPServer:
    """Core MCP server implementation."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.status = ServerStatus.STOPPED
        self.start_time = None
        self.tool_registry = ToolRegistry()
        self.execution_engine = ToolExecutionEngine(self.tool_registry)
        self.capabilities: Dict[str, ServerCapabilityInfo] = {}
        self.health_check_task: Optional[asyncio.Task] = None
        self._shutdown = False
        self._request_count = 0
        self._error_count = 0
        
        # Initialize default capabilities
        self._initialize_capabilities()
    
    def _initialize_capabilities(self):
        """Initialize default server capabilities."""
        default_capabilities = {
            ServerCapability.TOOLS_LIST: ServerCapabilityInfo(
                name="tools/list",
                description="List available tools",
                version="1.0.0",
                enabled=True
            ),
            ServerCapability.TOOLS_CALL: ServerCapabilityInfo(
                name="tools/call",
                description="Execute a tool",
                version="1.0.0",
                enabled=True
            ),
            ServerCapability.TOOLS_GET: ServerCapabilityInfo(
                name="tools/get",
                description="Get tool information",
                version="1.0.0",
                enabled=True
            ),
            ServerCapability.CHAT_COMPLETIONS: ServerCapabilityInfo(
                name="chat/completions",
                description="Chat completion API",
                version="1.0.0",
                enabled=True
            )
        }
        
        for capability, info in default_capabilities.items():
            self.capabilities[capability.value] = info
        
        logger.info("MCP server capabilities initialized", capabilities=list(self.capabilities.keys()))
    
    async def start(self):
        """Start the MCP server."""
        if self.status != ServerStatus.STOPPED:
            logger.warning("MCP server is not in STOPPED state", current_status=self.status.value)
            return
        
        try:
            self.status = ServerStatus.STARTING
            self.start_time = time.time()
            
            # Start health monitoring
            await self._start_health_monitoring()
            
            # Register built-in tools
            await self._register_builtin_tools()
            
            self.status = ServerStatus.RUNNING
            logger.info("MCP server started successfully", 
                       start_time=self.start_time,
                       tool_count=len(self.tool_registry.get_all_tools()))
            
        except Exception as e:
            self.status = ServerStatus.ERROR
            logger.error("Failed to start MCP server", error=str(e))
            raise
    
    async def stop(self):
        """Stop the MCP server."""
        if self.status == ServerStatus.STOPPED:
            return
        
        try:
            self.status = ServerStatus.STOPPING
            self._shutdown = True
            
            # Stop health monitoring
            if self.health_check_task:
                self.health_check_task.cancel()
                try:
                    await self.health_check_task
                except asyncio.CancelledError:
                    pass
            
            # Cleanup tools
            await self._cleanup_tools()
            
            self.status = ServerStatus.STOPPED
            logger.info("MCP server stopped successfully")
            
        except Exception as e:
            logger.error("Failed to stop MCP server", error=str(e))
            raise
    
    async def _start_health_monitoring(self):
        """Start server health monitoring."""
        if self.health_check_task:
            return
        
        self.health_check_task = asyncio.create_task(self._health_monitor_loop())
        logger.info("MCP server health monitoring started")
    
    async def _health_monitor_loop(self):
        """Health monitoring loop."""
        while not self._shutdown:
            try:
                # Update server health
                await self._update_health_status()
                
                # Wait for next health check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error("Health monitoring error", error=str(e))
                await asyncio.sleep(5)  # Brief pause on error
    
    async def _update_health_status(self):
        """Update server health status."""
        try:
            # Calculate error rate
            total_requests = max(self._request_count, 1)
            error_rate = self._error_count / total_requests
            
            # Update health info
            health_info = ServerHealthInfo(
                status=self.status,
                uptime=time.time() - (self.start_time or time.time()),
                tool_count=len(self.tool_registry.get_all_tools()),
                active_connections=0,  # TODO: Implement connection tracking
                total_requests=self._request_count,
                error_rate=error_rate,
                last_health_check=time.time(),
                capabilities=[cap.value for cap in ServerCapability if self.capabilities.get(cap.value, {}).get('enabled', False)]
            )
            
            # Log health status
            if error_rate > 0.1:  # More than 10% error rate
                logger.warning("High error rate detected", error_rate=error_rate)
            
            logger.debug("Server health updated", 
                        status=health_info.status.value,
                        tool_count=health_info.tool_count,
                        error_rate=health_info.error_rate)
            
        except Exception as e:
            logger.error("Failed to update health status", error=str(e))
    
    async def _register_builtin_tools(self):
        """Register built-in MCP tools."""
        try:
            # Import and register built-in tools
            from app.tools.file_reader import FileReaderTool
            from app.tools.text_processor import TextProcessorTool
            from app.tools.document_analyzer import DocumentAnalyzerTool
            from app.tools.web_content_fetcher import WebContentFetcherTool
            from app.tools.data_formatter import DataFormatterTool
            
            tools = [
                FileReaderTool(),
                TextProcessorTool(),
                DocumentAnalyzerTool(),
                WebContentFetcherTool(),
                DataFormatterTool()
            ]
            
            for tool in tools:
                self.tool_registry.register_tool(tool)
                logger.info(f"Built-in tool registered", tool_name=tool.metadata.name)
            
        except ImportError as e:
            logger.warning("Some built-in tools could not be imported", error=str(e))
        except Exception as e:
            logger.error("Failed to register built-in tools", error=str(e))
    
    async def _cleanup_tools(self):
        """Cleanup tool resources."""
        try:
            # Get all tools and cleanup if they have cleanup methods
            tools = self.tool_registry.get_all_tools()
            for tool in tools:
                if hasattr(tool, 'cleanup') and callable(getattr(tool, 'cleanup')):
                    try:
                        await tool.cleanup()
                    except Exception as e:
                        logger.warning(f"Tool cleanup failed", tool_name=tool.metadata.name, error=str(e))
            
            logger.info("Tool cleanup completed")
            
        except Exception as e:
            logger.error("Failed to cleanup tools", error=str(e))
    
    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP request."""
        start_time = time.time()
        self._request_count += 1
        
        try:
            # Extract request information
            method = request_data.get("method", "")
            params = request_data.get("params", {})
            request_id = request_data.get("id", "")
            
            logger.info("MCP request received", 
                       method=method, 
                       request_id=request_id,
                       params=params)
            
            # Route request to appropriate handler
            if method == "tools/list":
                result = await self._handle_tools_list(params)
            elif method == "tools/call":
                result = await self._handle_tools_call(params)
            elif method == "tools/get":
                result = await self._handle_tools_get(params)
            elif method == "chat/completions":
                result = await self._handle_chat_completions(params)
            else:
                result = self._create_error_response(
                    "METHOD_NOT_FOUND", 
                    f"Unknown method: {method}",
                    request_id
                )
            
            # Add execution time
            execution_time = time.time() - start_time
            result["execution_time"] = execution_time
            
            logger.info("MCP request completed", 
                       method=method, 
                       request_id=request_id,
                       execution_time=execution_time)
            
            return result
            
        except Exception as e:
            self._error_count += 1
            logger.error("MCP request failed", 
                        request_data=request_data, 
                        error=str(e))
            
            return self._create_error_response(
                "INTERNAL_ERROR",
                f"Request processing failed: {str(e)}",
                request_data.get("id", "")
            )
    
    async def _handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request."""
        try:
            tools = []
            for tool in self.tool_registry.get_all_tools():
                tool_info = {
                    "name": tool.metadata.name,
                    "description": tool.metadata.description,
                    "inputSchema": tool.metadata.input_schema,
                    "category": tool.metadata.category,
                    "tags": tool.metadata.tags,
                    "version": tool.metadata.version
                }
                tools.append(tool_info)
            
            return {
                "jsonrpc": "2.0",
                "id": "tools_list_response",
                "result": {
                    "tools": tools
                }
            }
            
        except Exception as e:
            logger.error("Tools list request failed", error=str(e))
            return self._create_error_response("INTERNAL_ERROR", str(e), "tools_list_response")
    
    async def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        try:
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            session_id = params.get("session_id", "default")
            
            if not tool_name:
                return self._create_error_response(
                    "INVALID_PARAMETERS", 
                    "Tool name is required", 
                    "tools_call_response"
                )
            
            # Create execution context
            context = ToolExecutionContext(
                session_id=session_id,
                parameters=arguments,
                request_id=f"call_{int(time.time() * 1000)}"
            )
            
            # Execute tool
            result = await self.execution_engine.execute_tool(tool_name, context)
            
            if result.status == ToolExecutionStatus.SUCCESS:
                return {
                    "jsonrpc": "2.0",
                    "id": "tools_call_response",
                    "result": {
                        "content": result.data,
                        "content_type": "application/json"
                    }
                }
            else:
                return self._create_error_response(
                    result.error_code.value if result.error_code else "EXECUTION_FAILED",
                    result.error_message or "Tool execution failed",
                    "tools_call_response"
                )
            
        except Exception as e:
            logger.error("Tools call request failed", error=str(e))
            return self._create_error_response("INTERNAL_ERROR", str(e), "tools_call_response")
    
    async def _handle_tools_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/get request."""
        try:
            tool_name = params.get("name")
            
            if not tool_name:
                return self._create_error_response(
                    "INVALID_PARAMETERS", 
                    "Tool name is required", 
                    "tools_get_response"
                )
            
            tool = self.tool_registry.get_tool(tool_name)
            if not tool:
                return self._create_error_response(
                    "RESOURCE_NOT_FOUND", 
                    f"Tool '{tool_name}' not found", 
                    "tools_get_response"
                )
            
            tool_info = {
                "name": tool.metadata.name,
                "description": tool.metadata.description,
                "inputSchema": tool.metadata.input_schema,
                "outputSchema": tool.metadata.output_schema,
                "category": tool.metadata.category,
                "tags": tool.metadata.tags,
                "version": tool.metadata.version,
                "examples": tool.metadata.examples,
                "statistics": tool.get_statistics()
            }
            
            return {
                "jsonrpc": "2.0",
                "id": "tools_get_response",
                "result": tool_info
            }
            
        except Exception as e:
            logger.error("Tools get request failed", error=str(e))
            return self._create_error_response("INTERNAL_ERROR", str(e), "tools_get_response")
    
    async def _handle_chat_completions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle chat/completions request."""
        try:
            # This is a placeholder for chat completions
            # In a real implementation, this would integrate with an LLM service
            
            return {
                "jsonrpc": "2.0",
                "id": "chat_completions_response",
                "result": {
                    "message": "Chat completions not yet implemented",
                    "status": "placeholder"
                }
            }
            
        except Exception as e:
            logger.error("Chat completions request failed", error=str(e))
            return self._create_error_response("INTERNAL_ERROR", str(e), "chat_completions_response")
    
    def _create_error_response(self, code: str, message: str, request_id: str) -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
    
    def get_health_info(self) -> ServerHealthInfo:
        """Get current server health information."""
        uptime = time.time() - (self.start_time or time.time())
        total_requests = max(self._request_count, 1)
        error_rate = self._error_count / total_requests
        
        return ServerHealthInfo(
            status=self.status,
            uptime=uptime,
            tool_count=len(self.tool_registry.get_all_tools()),
            active_connections=0,  # TODO: Implement connection tracking
            total_requests=self._request_count,
            error_rate=error_rate,
            last_health_check=time.time(),
            capabilities=[cap.value for cap in ServerCapability if self.capabilities.get(cap.value, {}).get('enabled', False)]
        )
    
    def get_capabilities(self) -> Dict[str, ServerCapabilityInfo]:
        """Get server capabilities."""
        return self.capabilities.copy()
    
    def enable_capability(self, capability_name: str, enabled: bool = True):
        """Enable or disable a server capability."""
        if capability_name in self.capabilities:
            self.capabilities[capability_name].enabled = enabled
            logger.info(f"Capability '{capability_name}' {'enabled' if enabled else 'disabled'}")
        else:
            logger.warning(f"Unknown capability: {capability_name}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get server statistics."""
        return {
            "status": self.status.value,
            "uptime": time.time() - (self.start_time or time.time()),
            "tool_count": len(self.tool_registry.get_all_tools()),
            "total_requests": self._request_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(self._request_count, 1),
            "capabilities": len([cap for cap in self.capabilities.values() if cap.enabled])
        }


# Global MCP server instance
mcp_server = MCPServer()
