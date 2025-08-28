"""
File Reader Tool for Word Add-in MCP Project.

This tool implements the MCP tool interface for reading files with:
- Security validation and path restrictions
- File type validation
- Size limit enforcement
- Comprehensive error handling
- File metadata extraction
"""

import os
import mimetypes
from typing import Dict, Any
from pathlib import Path

from backend.app.core.mcp_tool_interface import (
    BaseMCPTool,
    ToolMetadata,
    ToolExecutionContext,
    ToolExecutionResult,
    ToolExecutionStatus,
    ToolErrorCode
)


class FileReaderTool(BaseMCPTool):
    """MCP tool for reading files with security and validation."""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="file_reader",
            description="Read file contents with security validation and metadata extraction",
            version="1.0.0",
            author="Word Add-in MCP Project",
            tags=["file", "io", "security", "validation"],
            category="file_operations",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read",
                        "minLength": 1,
                        "maxLength": 500
                    },
                    "encoding": {
                        "type": "string",
                        "description": "File encoding (default: utf-8)",
                        "enum": ["utf-8", "latin-1", "ascii", "cp1252"],
                        "default": "utf-8"
                    },
                    "max_size_mb": {
                        "type": "number",
                        "description": "Maximum file size in MB (default: 10)",
                        "minimum": 0.1,
                        "maximum": 100,
                        "default": 10
                    }
                },
                "required": ["path"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "file_path": {"type": "string"},
                    "size_bytes": {"type": "integer"},
                    "encoding": {"type": "string"},
                    "mime_type": {"type": "string"},
                    "last_modified": {"type": "string"}
                }
            },
            examples=[
                {
                    "input": {"path": "sample.txt", "encoding": "utf-8"},
                    "output": "File content with metadata"
                }
            ],
            rate_limit=100,  # 100 requests per minute
            timeout=30.0,    # 30 seconds
            requires_auth=False
        )
        super().__init__(metadata)
        
        # Security configuration
        self.allowed_extensions = {'.txt', '.md', '.json', '.xml', '.csv', '.log', '.py', '.js', '.html', '.css'}
        self.max_file_size_mb = 10
        self.allowed_paths = {'.', './data', './uploads', './documents'}
    
    async def execute(self, context: ToolExecutionContext) -> ToolExecutionResult:
        """Execute the file reading operation."""
        try:
            # Extract parameters
            file_path = context.parameters.get("path")
            encoding = context.parameters.get("encoding", "utf-8")
            max_size_mb = context.parameters.get("max_size_mb", self.max_file_size_mb)
            
            # Validate file path
            validation_result = self._validate_file_path(file_path)
            if not validation_result["valid"]:
                return ToolExecutionResult(
                    status=ToolExecutionStatus.FAILED,
                    error_code=ToolErrorCode.INVALID_PARAMETERS,
                    error_message=validation_result["error"],
                    error_details={"file_path": file_path}
                )
            
            # Check file size
            file_size = os.path.getsize(file_path)
            max_size_bytes = max_size_mb * 1024 * 1024
            
            if file_size > max_size_bytes:
                return ToolExecutionResult(
                    status=ToolExecutionStatus.FAILED,
                    error_code=ToolErrorCode.INVALID_PARAMETERS,
                    error_message=f"File size {file_size} bytes exceeds limit of {max_size_bytes} bytes",
                    error_details={"file_size": file_size, "max_size": max_size_bytes}
                )
            
            # Read file content
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()
            
            # Get file metadata
            metadata = self._extract_file_metadata(file_path, encoding, file_size)
            
            return ToolExecutionResult(
                status=ToolExecutionStatus.SUCCESS,
                data={
                    "content": content,
                    "file_path": file_path,
                    "size_bytes": file_size,
                    "encoding": encoding,
                    "mime_type": metadata["mime_type"],
                    "last_modified": metadata["last_modified"]
                }
            )
            
        except UnicodeDecodeError as e:
            return ToolExecutionResult(
                status=ToolExecutionStatus.FAILED,
                error_code=ToolErrorCode.INVALID_PARAMETERS,
                error_message=f"Failed to decode file with encoding '{encoding}': {str(e)}",
                error_details={"encoding": encoding, "error": str(e)}
            )
        except PermissionError:
            return ToolExecutionResult(
                status=ToolExecutionStatus.FAILED,
                error_code=ToolErrorCode.PERMISSION_DENIED,
                error_message="Permission denied accessing file",
                error_details={"file_path": file_path}
            )
        except FileNotFoundError:
            return ToolExecutionResult(
                status=ToolExecutionStatus.FAILED,
                error_code=ToolErrorCode.RESOURCE_NOT_FOUND,
                error_message="File not found",
                error_details={"file_path": file_path}
            )
        except Exception as e:
            return ToolExecutionResult(
                status=ToolExecutionStatus.FAILED,
                error_code=ToolErrorCode.EXECUTION_FAILED,
                error_message=f"File reading failed: {str(e)}",
                error_details={"file_path": file_path, "error": str(e)}
            )
    
    def _validate_file_path(self, file_path: str) -> Dict[str, Any]:
        """Validate file path for security and access."""
        if not file_path:
            return {"valid": False, "error": "File path is required"}
        
        # Convert to absolute path
        try:
            abs_path = os.path.abspath(file_path)
        except Exception:
            return {"valid": False, "error": "Invalid file path format"}
        
        # Check if path is within allowed directories
        path_allowed = False
        for allowed_path in self.allowed_paths:
            try:
                allowed_abs = os.path.abspath(allowed_path)
                if abs_path.startswith(allowed_abs):
                    path_allowed = True
                    break
            except Exception:
                continue
        
        if not path_allowed:
            return {"valid": False, "error": "File path is outside allowed directories"}
        
        # Check file extension
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.allowed_extensions:
            return {"valid": False, "error": f"File extension '{file_ext}' is not allowed"}
        
        # Check if file exists
        if not os.path.isfile(file_path):
            return {"valid": False, "error": "File does not exist or is not a regular file"}
        
        return {"valid": True}
    
    def _extract_file_metadata(self, file_path: str, encoding: str, file_size: int) -> Dict[str, Any]:
        """Extract metadata from the file."""
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"
        
        # Get last modified time
        try:
            last_modified = os.path.getmtime(file_path)
            last_modified_str = str(last_modified)
        except Exception:
            last_modified_str = "unknown"
        
        return {
            "mime_type": mime_type,
            "last_modified": last_modified_str
        }
    
    def get_security_info(self) -> Dict[str, Any]:
        """Get security information for this tool."""
        return {
            "allowed_extensions": list(self.allowed_extensions),
            "max_file_size_mb": self.max_file_size_mb,
            "allowed_paths": list(self.allowed_paths),
            "security_features": [
                "Path validation",
                "File extension restriction",
                "Size limit enforcement",
                "Directory access control"
            ]
        }
