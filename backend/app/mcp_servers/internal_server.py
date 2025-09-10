"""
Internal MCP Server Implementation using FastMCP.

This server exposes all built-in tools through the standard MCP protocol,
using FastMCP for simple and compliant implementation based on the real FastMCP API.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional

import structlog
from fastmcp import FastMCP

from .tool_registry import InternalToolRegistry

logger = structlog.get_logger()

# Global FastMCP server instance
_global_fastmcp_server = None


def get_global_server():
    """Get or create the global FastMCP server instance."""
    global _global_fastmcp_server
    if _global_fastmcp_server is None:
        _global_fastmcp_server = create_fastmcp_server()
    return _global_fastmcp_server


def create_fastmcp_server():
    """Create and configure a FastMCP server with all internal tools."""
    logger.info("Creating FastMCP server with internal tools")
    
    # Create FastMCP server
    mcp_server = FastMCP("Internal Tools Server")
    
    # Get all internal tools
    tool_registry = InternalToolRegistry()
    tools_dict = tool_registry.tools
    
    logger.info(f"Found {len(tools_dict)} tools to register")
    
    # Register each tool with FastMCP
    for tool_name, tool_instance in tools_dict.items():
        logger.info(f"Registering tool with FastMCP: {tool_name}")
        
        # Create the tool function dynamically
        def create_tool_function(tool_inst):
            async def tool_function():
                """Dynamically created tool function."""
                try:
                    logger.info(f"Executing tool {tool_inst.name}")
                    # Get parameters from the tool's input schema
                    result = await tool_inst.execute({})
                    logger.info(f"Tool {tool_inst.name} completed successfully")
                    return result
                except Exception as e:
                    logger.error(f"Tool execution failed for {tool_inst.name}: {e}")
                    raise
            
            # Set function metadata
            tool_function.__name__ = tool_inst.name
            tool_function.__doc__ = tool_inst.description
            
            return tool_function
        
        # Create and register the tool function
        tool_func = create_tool_function(tool_instance)
        mcp_server.tool()(tool_func)
    
    logger.info(f"FastMCP server created with {len(tools_dict)} tools")
    
    # Add async methods for compatibility with existing code
    mcp_server.is_running = False
    
    async def async_start():
        mcp_server.is_running = True
    
    async def async_list_available_tools():
        return [{"name": name, "description": tool.description} 
                for name, tool in tools_dict.items()]
    
    async def async_stop():
        mcp_server.is_running = False
    
    mcp_server.start = async_start
    mcp_server.list_available_tools = async_list_available_tools
    mcp_server.stop = async_stop
    
    return mcp_server


class InternalMCPServer:
    """
    Compatibility wrapper for the FastMCP server.
    
    This class provides backward compatibility with the existing orchestrator code
    while using the real FastMCP implementation underneath.
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
        """Start the FastMCP server."""
        logger.info("Starting FastMCP server")
        # FastMCP servers don't need explicit starting - they're configuration objects
        # Just mark as running
        self.mcp_server.is_running = True
        logger.info("FastMCP server started successfully")
    
    async def stop(self):
        """Stop the FastMCP server."""
        logger.info("Stopping FastMCP server")
        # FastMCP servers don't need explicit stopping - they're configuration objects
        # Just mark as not running
        self.mcp_server.is_running = False
        logger.info("FastMCP server stopped")
    
    async def list_available_tools(self):
        """List all available tools."""
        # FastMCP servers don't have a list_available_tools method
        # Get tools from our internal registry
        tool_registry = InternalToolRegistry()
        tools_list = await tool_registry.list_all_tools()
        return tools_list
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]):
        """Execute a tool with given parameters."""
        logger.info(f"Executing tool {tool_name} with parameters: {parameters}")
        
        # Get the tool from registry and execute directly
        tool_registry = InternalToolRegistry()
        tools_dict = tool_registry.list_tools()
        
        if tool_name not in tools_dict:
            raise ValueError(f"Tool {tool_name} not found")
        
        tool_instance = tools_dict[tool_name]
        result = await tool_instance.execute(parameters)
        
        logger.info(f"Tool {tool_name} executed successfully")
        return result