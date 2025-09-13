"""
Tool Execution Engine.

This module handles the orchestration of tool execution including:
- Parameter validation
- Execution coordination
- Result processing and formatting
- Error handling and recovery
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass

import structlog

from app.core.exceptions import (
    ValidationError,
    ToolExecutionError,
    ParameterResolutionError
)
from app.services.validation_service import validation_service

logger = structlog.get_logger()


@dataclass
class ExecutionContext:
    """Context information for tool execution."""
    
    tool_name: str
    parameters: Dict[str, Any]
    source: str  # 'built-in' or 'external'
    server_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Post-initialization setup."""
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ExecutionResult:
    """Result of tool execution."""
    
    success: bool
    result: Any
    execution_time: float
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Post-initialization setup."""
        if self.metadata is None:
            self.metadata = {}


class ToolExecutionEngine:
    """
    Handles tool execution orchestration.
    
    This class provides:
    - Parameter validation
    - Execution coordination
    - Result processing
    - Error handling
    """
    
    def __init__(self):
        """Initialize the tool execution engine."""
        self.validation_service = validation_service
        
        # Performance metrics
        self.request_count = 0
        self.error_count = 0
        self.total_execution_time = 0.0
        self.validation_errors = 0
        self.execution_errors = 0
        
        logger.info("Tool Execution Engine initialized")
    
    async def initialize(self) -> None:
        """Initialize the tool execution engine."""
        try:
            logger.info("Initializing Tool Execution Engine...")
            
            # Initialize validation service if needed
            if hasattr(self.validation_service, 'initialize'):
                await self.validation_service.initialize()
            
            logger.info("Tool Execution Engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Tool Execution Engine: {str(e)}")
            raise
    
    async def validate_parameters(self, tool_name: str, parameters: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate tool parameters.
        
        Args:
            tool_name: Name of the tool to validate parameters for
            parameters: Parameters to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        start_time = time.time()
        self.request_count += 1
        
        try:
            logger.info(f"Validating parameters for tool: {tool_name}", parameters=parameters)
            
            # Get tool schema for validation
            tool_schema = await self._get_tool_schema(tool_name)
            if not tool_schema:
                logger.warning(f"No schema found for tool '{tool_name}', skipping validation")
                return True, []
            
            # Validate parameters using validation service
            validation_result = await self._validate_against_schema(parameters, tool_schema)
            
            execution_time = time.time() - start_time
            self.total_execution_time += execution_time
            
            if not validation_result[0]:
                self.validation_errors += 1
                logger.warning(f"Parameter validation failed for tool '{tool_name}'", 
                             errors=validation_result[1],
                             execution_time=execution_time)
            else:
                logger.info(f"Parameter validation successful for tool '{tool_name}'",
                           execution_time=execution_time)
            
            return validation_result
            
        except Exception as e:
            self.error_count += 1
            execution_time = time.time() - start_time
            logger.error(f"Parameter validation error for tool '{tool_name}': {str(e)}",
                        execution_time=execution_time)
            return False, [f"Validation error: {str(e)}"]
    
    async def format_result(self, result: Any, tool_name: str) -> Dict[str, Any]:
        """
        Format tool execution result.
        
        Args:
            result: Raw result from tool execution
            tool_name: Name of the tool that produced the result
            
        Returns:
            Formatted result dictionary
        """
        start_time = time.time()
        self.request_count += 1
        
        try:
            logger.info(f"Formatting result for tool: {tool_name}")
            
            # Standardize result format
            formatted_result = await self._standardize_result(result, tool_name)
            
            # Add metadata
            formatted_result.update({
                "tool_name": tool_name,
                "formatted_at": time.time(),
                "result_type": type(result).__name__
            })
            
            execution_time = time.time() - start_time
            self.total_execution_time += execution_time
            
            logger.info(f"Result formatted successfully for tool '{tool_name}'",
                       execution_time=execution_time)
            
            return formatted_result
            
        except Exception as e:
            self.error_count += 1
            execution_time = time.time() - start_time
            logger.error(f"Result formatting error for tool '{tool_name}': {str(e)}",
                        execution_time=execution_time)
            
            # Return error result
            return {
                "status": "error",
                "error_message": f"Result formatting failed: {str(e)}",
                "error_type": "formatting_error",
                "tool_name": tool_name,
                "formatted_at": time.time()
            }
    
    async def execute_with_retry(self, execution_func, *args, max_retries: int = 3, 
                                retry_delay: float = 1.0, **kwargs) -> ExecutionResult:
        """
        Execute a function with retry logic.
        
        Args:
            execution_func: Function to execute
            *args: Positional arguments for the function
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            **kwargs: Keyword arguments for the function
            
        Returns:
            ExecutionResult instance
        """
        start_time = time.time()
        self.request_count += 1
        
        last_error = None
        attempt = 0
        
        while attempt <= max_retries:
            try:
                attempt += 1
                logger.info(f"Executing function (attempt {attempt}/{max_retries + 1})")
                
                # Execute the function
                result = await execution_func(*args, **kwargs)
                
                execution_time = time.time() - start_time
                self.total_execution_time += execution_time
                
                logger.info(f"Function executed successfully on attempt {attempt}",
                           execution_time=execution_time)
                
                return ExecutionResult(
                    success=True,
                    result=result,
                    execution_time=execution_time,
                    metadata={"attempts": attempt}
                )
                
            except Exception as e:
                last_error = e
                self.execution_errors += 1
                
                if attempt <= max_retries:
                    logger.warning(f"Execution failed on attempt {attempt}, retrying in {retry_delay}s: {str(e)}")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Execution failed after {max_retries + 1} attempts: {str(e)}")
        
        # All retries exhausted
        execution_time = time.time() - start_time
        self.total_execution_time += execution_time
        
        return ExecutionResult(
            success=False,
            result=None,
            execution_time=execution_time,
            error_message=str(last_error),
            error_type=type(last_error).__name__,
            metadata={"attempts": attempt}
        )
    
    async def get_health(self) -> Dict[str, Any]:
        """
        Get health status of the tool execution engine.
        
        Returns:
            Health status dictionary
        """
        try:
            # Check validation service health
            validation_health = "healthy"
            if hasattr(self.validation_service, 'get_health'):
                try:
                    validation_health = await self.validation_service.get_health()
                except Exception:
                    validation_health = "unhealthy"
            
            health_info = {
                "status": "healthy" if validation_health == "healthy" else "degraded",
                "timestamp": time.time(),
                "components": {
                    "validation_service": validation_health
                },
                "metrics": {
                    "request_count": self.request_count,
                    "error_count": self.error_count,
                    "total_execution_time": self.total_execution_time,
                    "average_execution_time": (
                        self.total_execution_time / max(self.request_count, 1)
                    ),
                    "validation_errors": self.validation_errors,
                    "execution_errors": self.execution_errors
                }
            }
            
            return health_info
            
        except Exception as e:
            logger.error(f"Failed to get health status: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def _get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the schema for a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool schema or None if not found
        """
        try:
            # This would typically come from the tool registry
            # For now, return a basic schema
            return {
                "type": "object",
                "properties": {},
                "required": []
            }
        except Exception as e:
            logger.debug(f"Failed to get schema for tool '{tool_name}': {str(e)}")
            return None
    
    async def _validate_against_schema(self, parameters: Dict[str, Any], 
                                     schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate parameters against a schema.
        
        Args:
            parameters: Parameters to validate
            schema: Schema to validate against
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            # Use validation service if available
            if hasattr(self.validation_service, 'validate_parameters'):
                return await self.validation_service.validate_parameters(parameters, schema)
            
            # Basic validation as fallback
            errors = []
            
            # Check required fields
            required_fields = schema.get("required", [])
            for field in required_fields:
                if field not in parameters:
                    errors.append(f"Required field '{field}' is missing")
            
            # Check field types (basic)
            properties = schema.get("properties", {})
            for field_name, field_value in parameters.items():
                if field_name in properties:
                    field_schema = properties[field_name]
                    expected_type = field_schema.get("type")
                    
                    if expected_type == "string" and not isinstance(field_value, str):
                        errors.append(f"Field '{field_name}' must be a string")
                    elif expected_type == "integer" and not isinstance(field_value, int):
                        errors.append(f"Field '{field_name}' must be an integer")
                    elif expected_type == "boolean" and not isinstance(field_value, bool):
                        errors.append(f"Field '{field_name}' must be a boolean")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            logger.error(f"Schema validation error: {str(e)}")
            return False, [f"Schema validation error: {str(e)}"]
    
    async def _standardize_result(self, result: Any, tool_name: str) -> Dict[str, Any]:
        """
        Standardize tool execution result format.
        
        Args:
            result: Raw result from tool execution
            tool_name: Name of the tool
            
        Returns:
            Standardized result dictionary
        """
        try:
            # Handle different result formats
            if isinstance(result, dict):
                # Check if this is an MCP response format
                if "content" in result and "isError" in result:
                    # MCP response format - extract the actual content
                    content = result.get("content", [])
                    is_error = result.get("isError", False)
                    
                    # Extract text content from MCP content array
                    text_content = ""
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "text":
                                text_content += item.get("text", "")
                    
                    return {
                        "status": "error" if is_error else "success",
                        "result": text_content,
                        "timestamp": time.time(),
                        "mcp_response": result  # Keep original MCP response for debugging
                    }
                else:
                    # Regular dictionary, ensure it has required fields
                    standardized = result.copy()
                    
                    # Ensure status field exists
                    if "status" not in standardized:
                        standardized["status"] = "success"
                    
                    # Ensure timestamp exists
                    if "timestamp" not in standardized:
                        standardized["timestamp"] = time.time()
                    
                    return standardized
                
            elif isinstance(result, str):
                # String result
                return {
                    "status": "success",
                    "result": result,
                    "timestamp": time.time()
                }
                
            elif result is None:
                # None result
                return {
                    "status": "success",
                    "result": None,
                    "timestamp": time.time()
                }
                
            else:
                # Other types, convert to string representation
                return {
                    "status": "success",
                    "result": str(result),
                    "timestamp": time.time(),
                    "result_type": type(result).__name__
                }
                
        except Exception as e:
            logger.error(f"Result standardization error for tool '{tool_name}': {str(e)}")
            return {
                "status": "error",
                "error_message": f"Result standardization failed: {str(e)}",
                "error_type": "standardization_error",
                "timestamp": time.time()
            }
    
    async def shutdown(self) -> None:
        """Shutdown the tool execution engine gracefully."""
        try:
            logger.info("Shutting down Tool Execution Engine...")
            
            # Clean up validation service if needed
            if hasattr(self.validation_service, 'shutdown'):
                try:
                    await self.validation_service.shutdown()
                    logger.info("Validation service shutdown completed")
                except Exception as e:
                    logger.error(f"Error shutting down validation service: {str(e)}")
            
            # Clear references
            self.validation_service = None
            
            logger.info("Tool Execution Engine shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during execution engine shutdown: {str(e)}")
