"""
MCP Tool Interface for Word Add-in MCP Project.

This module provides a clean, extensible interface for MCP tools including:
- Tool interface contracts
- Parameter validation
- Tool result handling
- Tool error management
- Tool metadata management
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import structlog
from pydantic import BaseModel, ValidationError

logger = structlog.get_logger()


class ToolExecutionStatus(Enum):
    """Tool execution status enumeration."""
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ToolErrorCode(Enum):
    """Standard tool error codes."""
    INVALID_PARAMETERS = "INVALID_PARAMETERS"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    TIMEOUT = "TIMEOUT"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


@dataclass
class ToolMetadata:
    """Metadata for MCP tools."""
    name: str
    description: str
    version: str = "1.0.0"
    author: str = "Word Add-in MCP Project"
    tags: List[str] = field(default_factory=list)
    category: str = "general"
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    rate_limit: Optional[int] = None  # requests per minute
    timeout: Optional[float] = None  # seconds
    requires_auth: bool = False
    deprecated: bool = False


@dataclass
class ToolExecutionResult:
    """Result of tool execution."""
    status: ToolExecutionStatus
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[ToolErrorCode] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0
    metadata: Optional[Dict[str, Any]] = None
    warnings: List[str] = field(default_factory=list)


@dataclass
class ToolExecutionContext:
    """Context for tool execution."""
    session_id: str
    user_id: Optional[str] = None
    request_id: str = ""
    timestamp: float = field(default_factory=time.time)
    parameters: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    environment: str = "production"


class ToolParameterValidator:
    """Base class for tool parameter validation."""
    
    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema
    
    def validate(self, parameters: Dict[str, Any]) -> List[str]:
        """Validate tool parameters against schema."""
        errors = []
        
        # Check required fields
        required_fields = self.schema.get("required", [])
        for field_name in required_fields:
            if field_name not in parameters:
                errors.append(f"Required field '{field_name}' is missing")
        
        # Check field types and constraints
        for field_name, field_spec in self.schema.get("properties", {}).items():
            if field_name in parameters:
                value = parameters[field_name]
                field_errors = self._validate_field(field_name, value, field_spec)
                errors.extend(field_errors)
        
        return errors
    
    def _validate_field(self, field_name: str, value: Any, field_spec: Dict[str, Any]) -> List[str]:
        """Validate a single field."""
        errors = []
        
        # Type validation
        expected_type = field_spec.get("type")
        if expected_type:
            if expected_type == "string" and not isinstance(value, str):
                errors.append(f"Field '{field_name}' must be a string")
            elif expected_type == "integer" and not isinstance(value, int):
                errors.append(f"Field '{field_name}' must be an integer")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                errors.append(f"Field '{field_name}' must be a number")
            elif expected_type == "boolean" and not isinstance(value, bool):
                errors.append(f"Field '{field_name}' must be a boolean")
            elif expected_type == "array" and not isinstance(value, list):
                errors.append(f"Field '{field_name}' must be an array")
            elif expected_type == "object" and not isinstance(value, dict):
                errors.append(f"Field '{field_name}' must be an object")
        
        # Pattern validation for strings
        if isinstance(value, str) and "pattern" in field_spec:
            import re
            if not re.match(field_spec["pattern"], value):
                errors.append(f"Field '{field_name}' does not match required pattern")
        
        # Range validation for numbers
        if isinstance(value, (int, float)):
            if "minimum" in field_spec and value < field_spec["minimum"]:
                errors.append(f"Field '{field_name}' must be at least {field_spec['minimum']}")
            if "maximum" in field_spec and value > field_spec["maximum"]:
                errors.append(f"Field '{field_name}' must be at most {field_spec['maximum']}")
        
        # Length validation for strings and arrays
        if "minLength" in field_spec:
            if isinstance(value, str) and len(value) < field_spec["minLength"]:
                errors.append(f"Field '{field_name}' must be at least {field_spec['minLength']} characters")
            elif isinstance(value, list) and len(value) < field_spec["minLength"]:
                errors.append(f"Field '{field_name}' must have at least {field_spec['minLength']} items")
        
        if "maxLength" in field_spec:
            if isinstance(value, str) and len(value) > field_spec["maxLength"]:
                errors.append(f"Field '{field_name}' must be at most {field_spec['maxLength']} characters")
            elif isinstance(value, list) and len(value) > field_spec["maxLength"]:
                errors.append(f"Field '{field_name}' must have at most {field_spec['maxLength']} items")
        
        # Enum validation
        if "enum" in field_spec and value not in field_spec["enum"]:
            errors.append(f"Field '{field_name}' must be one of: {', '.join(map(str, field_spec['enum']))}")
        
        return errors


class BaseMCPTool(ABC):
    """Base class for all MCP tools."""
    
    def __init__(self, metadata: ToolMetadata):
        self.metadata = metadata
        self.validator = ToolParameterValidator(metadata.input_schema)
        self._execution_count = 0
        self._total_execution_time = 0.0
        self._error_count = 0
    
    @abstractmethod
    async def execute(self, context: ToolExecutionContext) -> ToolExecutionResult:
        """Execute the tool with the given context."""
        pass
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """Validate tool parameters."""
        return self.validator.validate(parameters)
    
    def get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return self.metadata
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get tool execution statistics."""
        avg_time = self._total_execution_time / max(self._execution_count, 1)
        return {
            "execution_count": self._execution_count,
            "total_execution_time": self._total_execution_time,
            "average_execution_time": avg_time,
            "error_count": self._error_count,
            "success_rate": (self._execution_count - self._error_count) / max(self._execution_count, 1)
        }
    
    def _record_execution(self, execution_time: float, success: bool):
        """Record execution statistics."""
        self._execution_count += 1
        self._total_execution_time += execution_time
        if not success:
            self._error_count += 1


class ToolRegistry:
    """Registry for managing MCP tools."""
    
    def __init__(self):
        self._tools: Dict[str, BaseMCPTool] = {}
        self._categories: Dict[str, List[str]] = {}
    
    def register_tool(self, tool: BaseMCPTool):
        """Register a tool in the registry."""
        tool_name = tool.metadata.name
        
        if tool_name in self._tools:
            logger.warning(f"Tool '{tool_name}' is already registered, overwriting")
        
        self._tools[tool_name] = tool
        
        # Add to category
        category = tool.metadata.category
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(tool_name)
        
        logger.info(f"Tool '{tool_name}' registered in category '{category}'")
    
    def unregister_tool(self, tool_name: str):
        """Unregister a tool from the registry."""
        if tool_name in self._tools:
            tool = self._tools[tool_name]
            category = tool.metadata.category
            
            # Remove from category
            if category in self._categories and tool_name in self._categories[category]:
                self._categories[category].remove(tool_name)
                if not self._categories[category]:
                    del self._categories[category]
            
            # Remove tool
            del self._tools[tool_name]
            logger.info(f"Tool '{tool_name}' unregistered")
    
    def get_tool(self, tool_name: str) -> Optional[BaseMCPTool]:
        """Get a tool by name."""
        return self._tools.get(tool_name)
    
    def list_tools(self, category: Optional[str] = None) -> List[str]:
        """List available tools, optionally filtered by category."""
        if category:
            return self._categories.get(category, [])
        return list(self._tools.keys())
    
    def get_tool_metadata(self, tool_name: str) -> Optional[ToolMetadata]:
        """Get metadata for a specific tool."""
        tool = self.get_tool(tool_name)
        return tool.metadata if tool else None
    
    def get_category_tools(self, category: str) -> List[BaseMCPTool]:
        """Get all tools in a specific category."""
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]
    
    def get_all_tools(self) -> List[BaseMCPTool]:
        """Get all registered tools."""
        return list(self._tools.values())
    
    def get_categories(self) -> List[str]:
        """Get all available categories."""
        return list(self._categories.keys())
    
    def search_tools(self, query: str) -> List[str]:
        """Search tools by name, description, or tags."""
        query_lower = query.lower()
        results = []
        
        for tool_name, tool in self._tools.items():
            # Search in name
            if query_lower in tool_name.lower():
                results.append(tool_name)
                continue
            
            # Search in description
            if query_lower in tool.metadata.description.lower():
                results.append(tool_name)
                continue
            
            # Search in tags
            for tag in tool.metadata.tags:
                if query_lower in tag.lower():
                    results.append(tool_name)
                    break
        
        return results


class ToolExecutionEngine:
    """Engine for executing MCP tools."""
    
    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry
        self._execution_history: List[Dict[str, Any]] = []
        self._max_history_size = 1000
    
    async def execute_tool(self, tool_name: str, context: ToolExecutionContext) -> ToolExecutionResult:
        """Execute a tool by name."""
        start_time = time.time()
        
        try:
            # Get tool
            tool = self.tool_registry.get_tool(tool_name)
            if not tool:
                return ToolExecutionResult(
                    status=ToolExecutionStatus.FAILED,
                    error_code=ToolErrorCode.RESOURCE_NOT_FOUND,
                    error_message=f"Tool '{tool_name}' not found",
                    execution_time=time.time() - start_time
                )
            
            # Validate parameters
            validation_errors = tool.validate_parameters(context.parameters)
            if validation_errors:
                return ToolExecutionResult(
                    status=ToolExecutionStatus.FAILED,
                    error_code=ToolErrorCode.INVALID_PARAMETERS,
                    error_message="Parameter validation failed",
                    error_details={"validation_errors": validation_errors},
                    execution_time=time.time() - start_time
                )
            
            # Execute tool
            result = await tool.execute(context)
            result.execution_time = time.time() - start_time
            
            # Record execution
            self._record_execution(tool_name, context, result)
            
            # Update tool statistics
            tool._record_execution(result.execution_time, result.status == ToolExecutionStatus.SUCCESS)
            
            return result
            
        except asyncio.TimeoutError:
            return ToolExecutionResult(
                status=ToolExecutionStatus.TIMEOUT,
                error_code=ToolErrorCode.TIMEOUT,
                error_message="Tool execution timed out",
                execution_time=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"Tool execution failed - Tool: {tool_name}, Error: {str(e)}")
            return ToolExecutionResult(
                status=ToolExecutionStatus.FAILED,
                error_code=ToolErrorCode.EXECUTION_FAILED,
                error_message="Tool execution failed",
                error_details={"exception": str(e)},
                execution_time=time.time() - start_time
            )
    
    def _record_execution(self, tool_name: str, context: ToolExecutionContext, result: ToolExecutionResult):
        """Record tool execution in history."""
        execution_record = {
            "tool_name": tool_name,
            "session_id": context.session_id,
            "user_id": context.user_id,
            "request_id": context.request_id,
            "timestamp": context.timestamp,
            "status": result.status.value,
            "execution_time": result.execution_time,
            "error_code": result.error_code.value if result.error_code else None,
            "parameters": context.parameters
        }
        
        self._execution_history.append(execution_record)
        
        # Maintain history size
        if len(self._execution_history) > self._max_history_size:
            self._execution_history.pop(0)
    
    def get_execution_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get tool execution history."""
        if limit:
            return self._execution_history[-limit:]
        return self._execution_history.copy()
    
    def get_tool_execution_history(self, tool_name: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get execution history for a specific tool."""
        tool_history = [record for record in self._execution_history if record["tool_name"] == tool_name]
        if limit:
            return tool_history[-limit:]
        return tool_history


# Global instances
tool_registry = ToolRegistry()
tool_execution_engine = ToolExecutionEngine(tool_registry)
