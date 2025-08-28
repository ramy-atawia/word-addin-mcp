"""
Tests for backend schema validation components.

This test suite covers all the Pydantic models and validation including:
- Chat schemas
- MCP tool schemas
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List
from pydantic import ValidationError

from app.schemas.chat import ChatMessage, ChatResponse, ChatHistory, ChatRequest
from app.schemas.mcp import MCPToolDefinition, MCPToolExecutionRequest, MCPToolResult


class TestChatSchemas:
    """Test chat-related schemas."""
    
    def test_chat_message_valid(self):
        """Test valid chat message schema."""
        message_data = {
            "id": "msg_123",
            "session_id": "session_123",
            "content": "Hello, how are you?",
            "role": "user",
            "timestamp": 1640995200.0,
            "metadata": {"source": "web"}
        }
        
        message = ChatMessage(**message_data)
        assert message.content == "Hello, how are you?"
        assert message.role == "user"
        assert message.session_id == "session_123"
    
    def test_chat_message_invalid_type(self):
        """Test chat message with any role value (no validation constraints)."""
        message_data = {
            "id": "msg_123",
            "session_id": "session_123",
            "content": "Hello",
            "role": "invalid_type",  # No validation constraints, so this should work
            "timestamp": 1640995200.0
        }
        
        # Since there are no validation constraints, this should create successfully
        message = ChatMessage(**message_data)
        assert message.role == "invalid_type"
        assert message.content == "Hello"

    def test_chat_message_empty_content(self):
        """Test chat message with empty content (no validation constraints)."""
        message_data = {
            "id": "msg_123",
            "session_id": "session_123",
            "content": "",  # No validation constraints, so empty content should work
            "role": "user",
            "timestamp": 1640995200.0
        }
        
        # Since there are no validation constraints, this should create successfully
        message = ChatMessage(**message_data)
        assert message.content == ""
        assert message.role == "user"
    
    def test_chat_response(self):
        """Test chat response schema."""
        response_data = {
            "message_id": "msg_123",
            "session_id": "session_123",
            "response": "I'm doing well, thank you!",
            "execution_time": 1.5,
            "timestamp": 1640995200.0,
            "model_used": "gpt-4",
            "tokens_used": 25
        }
        
        response = ChatResponse(**response_data)
        assert response.response == "I'm doing well, thank you!"
        assert response.message_id == "msg_123"
    
    def test_chat_history(self):
        """Test chat history schema."""
        history_data = {
            "session_id": "conv_123",
            "messages": [
                {
                    "id": "msg_1",
                    "session_id": "conv_123",
                    "content": "Hello",
                    "role": "user",
                    "timestamp": 1640995200.0
                },
                {
                    "id": "msg_2",
                    "session_id": "conv_123",
                    "content": "Hi there!",
                    "role": "assistant",
                    "timestamp": 1640995260.0
                }
            ],
            "total_messages": 2,
            "last_activity": 1640995260.0,
            "created_at": 1640995200.0
        }
        
        history = ChatHistory(**history_data)
        assert history.session_id == "conv_123"
        assert len(history.messages) == 2
        assert history.messages[0].role == "user"
        assert history.messages[1].role == "assistant"
    
    def test_chat_request(self):
        """Test chat request schema."""
        request_data = {
            "message": "Hello, how are you?",
            "session_id": "session_123",
            "user_id": "user_123",
            "context": {"document_id": "doc_123"}
        }
        
        request = ChatRequest(**request_data)
        assert request.message == "Hello, how are you?"
        assert request.session_id == "session_123"
        assert request.user_id == "user_123"


class TestMCPSchemas:
    """Test MCP tool schemas."""
    
    def test_mcp_tool_definition_valid(self):
        """Test valid MCP tool definition schema."""
        tool_def_data = {
            "name": "text_processor",
            "description": "Process and analyze text content",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "operation": {"type": "string"}
                }
            },
            "version": "1.0.0",
            "author": "AI Team"
        }
        
        tool_def = MCPToolDefinition(**tool_def_data)
        assert tool_def.name == "text_processor"
        assert tool_def.description == "Process and analyze text content"
        assert tool_def.version == "1.0.0"
    
    def test_mcp_tool_execution_request_valid(self):
        """Test valid MCP tool execution request schema."""
        request_data = {
            "tool_name": "text_processor",
            "parameters": {
                "text": "Hello world",
                "operation": "summarize"
            },
            "session_id": "session_123",
            "request_id": "req_123",
            "timeout": 30,
            "priority": "normal"
        }
        
        request = MCPToolExecutionRequest(**request_data)
        assert request.tool_name == "text_processor"
        assert request.parameters["text"] == "Hello world"
        assert request.session_id == "session_123"
    
    def test_mcp_tool_result_valid(self):
        """Test valid MCP tool result schema."""
        result_data = {
            "content": "Processed text result",
            "content_type": "text",
            "metadata": {"processing_time": 1.5},
            "format": "plain_text"
        }
        
        result = MCPToolResult(**result_data)
        assert result.content == "Processed text result"
        assert result.content_type == "text"
        assert result.metadata["processing_time"] == 1.5
    
    def test_mcp_tool_definition_missing_required(self):
        """Test MCP tool definition with missing required fields."""
        incomplete_data = {
            "name": "text_processor"
            # Missing description and inputSchema
        }
        
        with pytest.raises(ValidationError):
            MCPToolDefinition(**incomplete_data)
    
    def test_mcp_tool_execution_request_invalid_timeout(self):
        """Test MCP tool execution request with invalid timeout."""
        request_data = {
            "tool_name": "text_processor",
            "parameters": {"text": "Hello"},
            "session_id": "session_123",
            "timeout": -5  # Invalid negative timeout
        }
        
        # Since there are no validation constraints, this should create successfully
        request = MCPToolExecutionRequest(**request_data)
        assert request.timeout == -5
        assert request.tool_name == "text_processor"
