"""
Internal MCP Server Implementation.

This server exposes all built-in tools through a simple interface
that works without external dependencies.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional

import structlog

from .tool_registry import InternalToolRegistry

logger = structlog.get_logger()

# Global internal server instance
_global_internal_server = None


def get_global_server():
    """Get or create the global internal server instance."""
    global _global_internal_server
    if _global_internal_server is None:
        _global_internal_server = create_internal_server()
    return _global_internal_server


def create_internal_server():
    """Create and configure an internal server with all internal tools."""
    logger.info("Creating internal server with internal tools")
    
    # Get all internal tools
    tool_registry = InternalToolRegistry()
    tools_dict = tool_registry.tools
    
    logger.info(f"Found {len(tools_dict)} tools to register")
    
    # Create a simple server object
    class SimpleInternalServer:
        def __init__(self):
            self.tools_dict = tools_dict
            self.is_running = False
        
        async def start(self):
            self.is_running = True
            logger.info("Internal server started successfully")
        
        async def stop(self):
            self.is_running = False
            logger.info("Internal server stopped")
        
        async def list_available_tools(self):
            return [{"name": name, "description": tool.description} 
                    for name, tool in self.tools_dict.items()]
    
    server = SimpleInternalServer()
    logger.info(f"Internal server created with {len(tools_dict)} tools")
    
    return server


class InternalMCPServer:
    """
    Compatibility wrapper for the internal server.
    
    This class provides backward compatibility with the existing orchestrator code
    while using the simple internal server implementation.
    """
    
    def __init__(self, host: str = "localhost", port: int = 9001):
        """Initialize the internal MCP server."""
        self.host = host
        self.port = port
        self.mcp_server = get_global_server()
        
        logger.info(f"Internal MCP Server wrapper initialized on {self.host}:{self.port}")
    
    @property
    def is_running(self):
        """Check if the server is running."""
        return getattr(self.mcp_server, 'is_running', False)
    
    async def start(self):
        """Start the internal server."""
        logger.info("Starting internal server")
        await self.mcp_server.start()
        logger.info("Internal server started successfully")
    
    async def stop(self):
        """Stop the internal server."""
        logger.info("Stopping internal server")
        await self.mcp_server.stop()
        logger.info("Internal server stopped")
    
    async def list_available_tools(self):
        """List all available tools."""
        return await self.mcp_server.list_available_tools()
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]):
        """Execute a tool with given parameters."""
        logger.info(f"Executing tool {tool_name} with parameters: {parameters}")
        
        # Get the tool from registry and execute directly
        tool_registry = InternalToolRegistry()
        tools_dict = tool_registry.tools
        
        if tool_name not in tools_dict:
            raise ValueError(f"Tool {tool_name} not found")
        
        tool_instance = tools_dict[tool_name]
        result = await tool_instance.execute(parameters)
        
        logger.info(f"Tool {tool_name} executed successfully")
        return result