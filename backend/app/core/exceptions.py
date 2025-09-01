"""
Custom exceptions for the MCP system.

This module defines custom exception classes for handling specific error
cases in the MCP system, including external server errors, authentication
failures, and connection issues.
"""


class MCPError(Exception):
    """Base exception for MCP system errors."""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ExternalMCPServerError(MCPError):
    """Exception raised when external MCP server operations fail."""
    
    def __init__(self, message: str, server_id: str = None, tool_name: str = None, details: dict = None):
        super().__init__(message, "EXTERNAL_SERVER_ERROR", details)
        self.server_id = server_id
        self.tool_name = tool_name


class AuthenticationError(MCPError):
    """Exception raised when authentication fails."""
    
    def __init__(self, message: str, auth_type: str = None, details: dict = None):
        super().__init__(message, "AUTHENTICATION_ERROR", details)
        self.auth_type = auth_type


class ConnectionError(MCPError):
    """Exception raised when connection to external server fails."""
    
    def __init__(self, message: str, server_url: str = None, details: dict = None):
        super().__init__(message, "CONNECTION_ERROR", details)
        self.server_url = server_url


class ToolExecutionError(MCPError):
    """Exception raised when tool execution fails."""
    
    def __init__(self, message: str, tool_name: str = None, server_id: str = None, details: dict = None):
        super().__init__(message, "TOOL_EXECUTION_ERROR", details)
        self.tool_name = tool_name
        self.server_id = server_id


class ToolNotFoundError(MCPError):
    """Exception raised when a tool is not found."""
    
    def __init__(self, message: str, tool_name: str = None, available_tools: list = None, details: dict = None):
        super().__init__(message, "TOOL_NOT_FOUND", details)
        self.tool_name = tool_name
        self.available_tools = available_tools or []


class ServerConfigurationError(MCPError):
    """Exception raised when server configuration is invalid."""
    
    def __init__(self, message: str, config_field: str = None, details: dict = None):
        super().__init__(message, "CONFIGURATION_ERROR", details)
        self.config_field = config_field


class HealthCheckError(MCPError):
    """Exception raised when health check fails."""
    
    def __init__(self, message: str, server_id: str = None, health_status: dict = None, details: dict = None):
        super().__init__(message, "HEALTH_CHECK_ERROR", details)
        self.server_id = server_id
        self.health_status = health_status


class WorkflowOrchestrationError(MCPError):
    """Exception raised when workflow orchestration fails."""
    
    def __init__(self, message: str, workflow_id: str = None, step_number: int = None, details: dict = None):
        super().__init__(message, "WORKFLOW_ERROR", details)
        self.workflow_id = workflow_id
        self.step_number = step_number


class ParameterResolutionError(MCPError):
    """Exception raised when parameter resolution fails."""
    
    def __init__(self, message: str, parameter_name: str = None, tool_name: str = None, details: dict = None):
        super().__init__(message, "PARAMETER_ERROR", details)
        self.parameter_name = parameter_name
        self.tool_name = tool_name


class RateLimitError(MCPError):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, message: str, server_id: str = None, retry_after: int = None, details: dict = None):
        super().__init__(message, "RATE_LIMIT_ERROR", details)
        self.server_id = server_id
        self.retry_after = retry_after


class TimeoutError(MCPError):
    """Exception raised when operation times out."""
    
    def __init__(self, message: str, operation: str = None, timeout_seconds: int = None, details: dict = None):
        super().__init__(message, "TIMEOUT_ERROR", details)
        self.operation = operation
        self.timeout_seconds = timeout_seconds


class ValidationError(MCPError):
    """Exception raised when validation fails."""
    
    def __init__(self, message: str, field_name: str = None, value: any = None, details: dict = None):
        super().__init__(message, "VALIDATION_ERROR", details)
        self.field_name = field_name
        self.value = value


# Convenience functions for common error scenarios
def create_server_error(message: str, server_id: str, **kwargs) -> ExternalMCPServerError:
    """Create a server error with standard formatting."""
    return ExternalMCPServerError(
        message=f"Server {server_id}: {message}",
        server_id=server_id,
        **kwargs
    )


def create_tool_error(message: str, tool_name: str, server_id: str = None, **kwargs) -> ToolExecutionError:
    """Create a tool execution error with standard formatting."""
    return ToolExecutionError(
        message=f"Tool '{tool_name}': {message}",
        tool_name=tool_name,
        server_id=server_id,
        **kwargs
    )


def create_auth_error(message: str, auth_type: str = None, **kwargs) -> AuthenticationError:
    """Create an authentication error with standard formatting."""
    return AuthenticationError(
        message=f"Authentication failed: {message}",
        auth_type=auth_type,
        **kwargs
    )


def create_connection_error(message: str, server_url: str, **kwargs) -> ConnectionError:
    """Create a connection error with standard formatting."""
    return ConnectionError(
        message=f"Connection failed to {server_url}: {message}",
        server_url=server_url,
        **kwargs
    )
