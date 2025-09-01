"""
Base Tool Class for Internal MCP Tools using FastMCP.

This module provides the base class that all internal tools should inherit from,
ensuring consistent interface and behavior that conforms to MCP standards.
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import structlog
import mcp.types
from mcp.types import Tool, TextContent, ContentBlock, ToolAnnotations

logger = structlog.get_logger()


class BaseInternalTool(ABC):
    """Base class for all internal MCP tools conforming to MCP standards."""
    
    def __init__(self, name: str, description: str, version: str = "1.0.0"):
        self.name = name
        self.description = description
        self.version = version
        self.usage_count = 0
        self.last_used = None
        self.total_execution_time = 0.0
        
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with given parameters.
        
        Args:
            parameters: Tool parameters
            
        Returns:
            Tool execution result
        """
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get tool metadata."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "usage_count": self.usage_count,
            "last_used": self.last_used,
            "total_execution_time": self.total_execution_time
        }
    
    def to_mcp_tool(self) -> Tool:
        """Convert to official MCP Tool object."""
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema=self.get_input_schema(),
            annotations=ToolAnnotations(
                name=self.name,
                description=self.description
            )
        )
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Get the input schema for this tool (JSON Schema format)."""
        # Return the input_schema if defined, otherwise default
        if hasattr(self, 'input_schema'):
            return self.input_schema
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    def get_schema(self) -> Dict[str, Any]:
        """Get complete tool schema (for compatibility with tool registry)."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": getattr(self, 'author', 'Word Add-in MCP Project'),
            "tags": getattr(self, 'tags', []),
            "category": getattr(self, 'category', 'general'),
            "input_schema": self.get_input_schema(),
            "output_schema": getattr(self, 'output_schema', {}),
            "examples": getattr(self, 'examples', [])
        }
    
    def update_usage_stats(self, execution_time: float):
        """Update tool usage statistics."""
        self.usage_count += 1
        self.last_used = time.time()
        self.total_execution_time += execution_time
        
    async def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate tool parameters.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Default implementation - override in subclasses for specific validation
        return True, None
    
    def get_health(self) -> Dict[str, Any]:
        """Get tool health status."""
        return {
            "status": "healthy",
            "name": self.name,
            "usage_count": self.usage_count,
            "last_used": self.last_used,
            "total_execution_time": self.total_execution_time
        }
