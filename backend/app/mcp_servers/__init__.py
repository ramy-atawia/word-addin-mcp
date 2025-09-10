"""
Internal MCP Server Package.

This package contains the internal MCP server that exposes
all built-in tools through the standard MCP protocol.
"""

# from .internal_server import InternalMCPServer  # Temporarily disabled
from .tool_registry import InternalToolRegistry

__all__ = [
    # "InternalMCPServer",  # Temporarily disabled
    "InternalToolRegistry"
]
