"""
Internal Tool Registry for Internal MCP Server.

This registry manages all built-in tools and exposes them
through the internal MCP server interface.
"""

import time
from typing import Dict, List, Any, Optional

import structlog

from .tools import (
    WebSearchTool,
    PriorArtSearchTool,
    ClaimDraftingTool,
    ClaimAnalysisTool
)

logger = structlog.get_logger()


class InternalToolRegistry:
    """
    Registry for all internal tools.
    
    This registry manages the lifecycle of all built-in tools
    and provides a unified interface for tool discovery and execution.
    """
    
    def __init__(self):
        """Initialize the internal tool registry."""
        self.tools: Dict[str, Any] = {}
        self.tool_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Register all built-in tools
        self._register_builtin_tools()
        
        logger.info(f"Internal tool registry initialized with {len(self.tools)} tools")
    
    def _register_builtin_tools(self):
        """Register all built-in tools."""
        try:
            # Create tool instances
            web_search_tool = WebSearchTool()
            prior_art_search_tool = PriorArtSearchTool()
            claim_drafting_tool = ClaimDraftingTool()
            claim_analysis_tool = ClaimAnalysisTool()
            
            # Register tools
            self._register_tool(web_search_tool)
            self._register_tool(prior_art_search_tool)
            self._register_tool(claim_drafting_tool)
            self._register_tool(claim_analysis_tool)
            
            logger.info(f"Successfully registered {len(self.tools)} built-in tools")
            
        except Exception as e:
            logger.error(f"Failed to register built-in tools: {str(e)}")
            # Continue with empty tools rather than crashing
    
    def _register_tool(self, tool):
        """Register a tool instance."""
        tool_name = tool.name
        
        # Store tool instance
        self.tools[tool_name] = tool
        
        # Store tool metadata from schema
        self.tool_metadata[tool_name] = tool.get_schema()
        
        logger.info(f"Registered internal tool: {tool_name}")
    
    async def list_all_tools(self) -> List[Dict[str, Any]]:
        """List all available tools with MCP-compliant format."""
        tools = []
        for tool_name, tool in self.tools.items():
            # Convert to proper MCP Tool object
            mcp_tool = tool.to_mcp_tool()
            
            # Return MCP-compliant tool format
            tools.append({
                "name": tool_name,
                "description": mcp_tool.description,
                "input_schema": mcp_tool.inputSchema,
                "version": tool.version,
                "usage_count": tool.usage_count,
                "last_used": tool.last_used,
                "total_execution_time": tool.total_execution_time
            })
        
        logger.info(f"Listed {len(tools)} internal tools")
        return tools

    async def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get tool information in MCP-compliant format."""
        if tool_name not in self.tools:
            logger.warning(f"Tool '{tool_name}' not found")
            return None
        
        tool = self.tools[tool_name]
        mcp_tool = tool.to_mcp_tool()
        
        # Return MCP-compliant tool info
        tool_info = {
            "name": tool_name,
            "description": mcp_tool.description,
            "input_schema": mcp_tool.inputSchema,
            "version": tool.version,
            "usage_count": tool.usage_count,
            "last_used": tool.last_used,
            "total_execution_time": tool.total_execution_time
        }
        
        logger.info(f"Retrieved tool info for '{tool_name}'")
        return tool_info

    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return MCP-compliant result."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        try:
            start_time = time.time()
            
            # Get tool instance
            tool = self.tools[tool_name]
            
            # Execute the tool
            result = await tool.execute(parameters)
            
            execution_time = time.time() - start_time
            
            # Return MCP-compliant result
            return {
                "status": "success",
                "result": result,
                "tool_name": tool_name,
                "execution_time": execution_time,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Tool execution failed for '{tool_name}': {str(e)}")
            raise
    
    async def get_health(self) -> Dict[str, Any]:
        """Get health status of the tool registry."""
        tool_health = {}
        for tool_name, tool in self.tools.items():
            tool_health[tool_name] = tool.get_health()
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "tool_count": len(self.tools),
            "registered_tools": list(self.tools.keys()),
            "tool_health": tool_health
        }
