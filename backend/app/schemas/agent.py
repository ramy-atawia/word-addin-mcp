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
    
    context: Dict[str, str] = Field(
        default_factory=dict,
        description="Context information for the agent (document_content, chat_history, available_tools)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Hello, can you help me analyze this document?",
                "context": {
                    "document_content": "This is a sample document content...",
                    "chat_history": "user: Hello\nassistant: Hi there! How can I help you?",
                    "available_tools": "web_search_tool, text_analysis_tool, document_analysis_tool"
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
    
    tools_used: List[str] = Field(
        default_factory=list,
        description="List of tools that were executed"
    )
    
    execution_time: float = Field(
        ..., 
        description="Time taken to process the request in seconds"
    )
    
    success: bool = Field(
        ..., 
        description="Whether the request was processed successfully"
    )
    
    reasoning: Optional[str] = Field(
        None,
        description="Reasoning behind the routing decision"
    )
    
    conversation_memory_size: int = Field(
        ..., 
        description="Current size of conversation memory"
    )
    
    error: Optional[str] = Field(
        None,
        description="Error message if something went wrong"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "response": "Hello! I'd be happy to help you analyze your document. I can provide insights about structure, content, and key themes.",
                "intent_type": "greeting",
                "tool_name": None,
                "tools_used": ["llm_chat"],
                "execution_time": 1.23,
                "success": True,
                "reasoning": "User greeted the assistant, so conversational response is appropriate",
                "conversation_memory_size": 2,
                "error": None
            }
        }
