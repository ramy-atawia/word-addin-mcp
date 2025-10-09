"""
Agent Chat API schemas for Word Add-in MCP Project.

This module defines the request and response models for the agent chat endpoint.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class AgentChatRequest(BaseModel):
    """Request model for agent chat endpoint."""
    
    message: str = Field(
        ..., 
        description="User message to process",
        min_length=1,
        max_length=10000
    )
    
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Context information for the agent (document_content, chat_history, available_tools, session_id)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Hello, can you help me analyze this document?",
                "context": {
                    "document_content": "This is a sample document content...",
                    "chat_history": "user: Hello\nassistant: Hi there! How can I help you?",
                    "available_tools": "web_search_tool, text_analysis_tool, document_analysis_ "
                }
            }
        }


class AgentChatResponse(BaseModel):
    """Response model for agent chat endpoint."""
    
    response: str = Field(
        ..., 
        description="AI response or tool execution result"
    )
    
    intent_type: str = Field(
        ..., 
        description="Detected intent type from user message"
    )
    
    tool_name: Optional[str] = Field(
        None, 
        description="Name of the tool that was executed, if any"
    )
    
    execution_time: float = Field(
        ..., 
        description="Time taken to process the request in seconds"
    )
    
    success: bool = Field(
        ..., 
        description="Whether the request was processed successfully"
    )
    
    error: Optional[str] = Field(
        None,
        description="Error message if something went wrong"
    )
    
    workflow_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadata about workflow execution, including step information and tool results"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "response": "Hello! I'd be happy to help you analyze your document. I can provide insights about structure, content, and key themes.",
                "intent_type": "greeting",
                "tool_name": None,
                "execution_time": 1.23,
                "success": True,
                "error": None
            }
        }
