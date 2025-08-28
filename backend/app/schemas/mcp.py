"""
MCP protocol schemas for Word Add-in MCP Project.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime


class MCPToolDefinition(BaseModel):
    """Schema for MCP tool definition."""
    
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    inputSchema: Dict[str, Any] = Field(..., description="Tool input schema")
    version: Optional[str] = Field(None, description="Tool version")
    author: Optional[str] = Field(None, description="Tool author")


class MCPToolListResponse(BaseModel):
    """Schema for MCP tools list response."""
    
    tools: List[MCPToolDefinition] = Field(..., description="List of available tools")
    total_count: int = Field(..., description="Total number of tools")
    protocol_version: str = Field(..., description="MCP protocol version")
    server_capabilities: Dict[str, Any] = Field(..., description="Server capabilities")
    timestamp: Optional[datetime] = Field(None, description="Response timestamp")


class MCPToolExecutionRequest(BaseModel):
    """Schema for MCP tool execution request."""
    
    tool_name: str = Field(..., description="Name of the tool to execute")
    parameters: Dict[str, Any] = Field(..., description="Tool execution parameters")
    session_id: str = Field(..., description="User session ID")
    request_id: Optional[str] = Field(None, description="Unique request ID")
    timeout: Optional[int] = Field(30, description="Execution timeout in seconds")
    priority: Optional[str] = Field("normal", description="Execution priority")


class MCPToolResult(BaseModel):
    """Schema for MCP tool execution result."""
    
    content: Union[str, Dict[str, Any]] = Field(..., description="Tool execution result content")
    content_type: str = Field("text", description="Type of result content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional result metadata")
    format: Optional[str] = Field(None, description="Result format specification")


class MCPError(BaseModel):
    """Schema for MCP tool execution error."""
    
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Detailed error information")
    suggestions: Optional[List[str]] = Field(None, description="Suggested solutions")
    retry_after: Optional[int] = Field(None, description="Retry after seconds")


class MCPToolExecutionResponse(BaseModel):
    """Schema for MCP tool execution response."""
    
    tool_name: str = Field(..., description="Name of the executed tool")
    session_id: str = Field(..., description="User session ID")
    result: Optional[MCPToolResult] = Field(None, description="Tool execution result")
    error: Optional[MCPError] = Field(None, description="Tool execution error")
    execution_time: float = Field(..., description="Execution time in seconds")
    status: str = Field(..., description="Execution status (success/error)")
    mcp_protocol_version: str = Field(..., description="MCP protocol version")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    timestamp: Optional[datetime] = Field(None, description="Response timestamp")


class MCPConnectionStatus(BaseModel):
    """Schema for MCP server connection status."""
    
    status: str = Field(..., description="Connection status")
    server_url: str = Field(..., description="MCP server URL")
    protocol_version: str = Field(..., description="MCP protocol version")
    last_heartbeat: float = Field(..., description="Last heartbeat timestamp")
    connection_health: str = Field(..., description="Connection health status")
    available_tools: int = Field(..., description="Number of available tools")
    server_capabilities: Dict[str, Any] = Field(..., description="Server capabilities")
    error_message: Optional[str] = Field(None, description="Error message if connection failed")


class MCPToolExecutionLog(BaseModel):
    """Schema for MCP tool execution logging."""
    
    tool_name: str = Field(..., description="Tool name")
    session_id: str = Field(..., description="User session ID")
    request_id: str = Field(..., description="Request ID")
    parameters: Dict[str, Any] = Field(..., description="Execution parameters")
    start_time: datetime = Field(..., description="Execution start time")
    end_time: Optional[datetime] = Field(None, description="Execution end time")
    execution_time: Optional[float] = Field(None, description="Total execution time")
    status: str = Field(..., description="Execution status")
    error: Optional[MCPError] = Field(None, description="Execution error if any")
    result_size: Optional[int] = Field(None, description="Result size in bytes")
    user_agent: Optional[str] = Field(None, description="User agent string")
    ip_address: Optional[str] = Field(None, description="Client IP address")


class MCPToolMetrics(BaseModel):
    """Schema for MCP tool performance metrics."""
    
    tool_name: str = Field(..., description="Tool name")
    total_executions: int = Field(0, description="Total number of executions")
    successful_executions: int = Field(0, description="Number of successful executions")
    failed_executions: int = Field(0, description="Number of failed executions")
    average_execution_time: float = Field(0.0, description="Average execution time in seconds")
    total_execution_time: float = Field(0.0, description="Total execution time in seconds")
    last_execution: Optional[datetime] = Field(None, description="Last execution timestamp")
    error_rate: float = Field(0.0, description="Error rate percentage")
    throughput: float = Field(0.0, description="Executions per minute")


class MCPToolCapability(BaseModel):
    """Schema for MCP tool capability information."""
    
    name: str = Field(..., description="Capability name")
    description: str = Field(..., description="Capability description")
    enabled: bool = Field(True, description="Whether capability is enabled")
    version: Optional[str] = Field(None, description="Capability version")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Capability parameters")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Capability constraints")


class MCPToolRegistry(BaseModel):
    """Schema for MCP tool registry."""
    
    tools: List[MCPToolDefinition] = Field(..., description="Registered tools")
    capabilities: List[MCPToolCapability] = Field(..., description="Available capabilities")
    protocol_version: str = Field(..., description="MCP protocol version")
    server_info: Dict[str, Any] = Field(..., description="Server information")
    last_updated: datetime = Field(..., description="Last registry update timestamp")
    registry_version: str = Field(..., description="Registry version")


class MCPToolExecutionQueue(BaseModel):
    """Schema for MCP tool execution queue."""
    
    queue_id: str = Field(..., description="Queue identifier")
    tool_name: str = Field(..., description="Tool name")
    session_id: str = Field(..., description="User session ID")
    request_id: str = Field(..., description="Request ID")
    priority: str = Field("normal", description="Execution priority")
    queued_at: datetime = Field(..., description="Queue timestamp")
    estimated_wait_time: Optional[int] = Field(None, description="Estimated wait time in seconds")
    queue_position: Optional[int] = Field(None, description="Position in queue")
    status: str = Field("queued", description="Queue status")


class MCPToolExecutionPolicy(BaseModel):
    """Schema for MCP tool execution policy."""
    
    tool_name: str = Field(..., description="Tool name")
    max_concurrent_executions: int = Field(1, description="Maximum concurrent executions")
    rate_limit_per_minute: int = Field(60, description="Rate limit per minute")
    rate_limit_per_hour: int = Field(1000, description="Rate limit per hour")
    timeout_seconds: int = Field(30, description="Execution timeout in seconds")
    retry_count: int = Field(3, description="Maximum retry attempts")
    retry_delay_seconds: int = Field(5, description="Delay between retries")
    priority_levels: List[str] = Field(["low", "normal", "high"], description="Available priority levels")
    resource_limits: Optional[Dict[str, Any]] = Field(None, description="Resource usage limits")
