"""
MCP (Model Context Protocol) Service Package.

This package provides a unified interface for managing MCP operations including:
- Built-in tool management
- External server management  
- Tool execution orchestration
- Unified tool discovery and execution
"""

from .orchestrator import MCPOrchestrator
from .server_registry import MCPServerRegistry
from .execution_engine import ToolExecutionEngine

__all__ = [
    "MCPOrchestrator",
    "MCPServerRegistry",
    "ToolExecutionEngine"
]
