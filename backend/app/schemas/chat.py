"""
Chat schemas for Word Add-in MCP Project.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime


class ChatMessage(BaseModel):
    """Schema for a chat message."""
    
    id: str = Field(..., description="Unique message identifier")
    session_id: str = Field(..., description="Chat session identifier")
    content: str = Field(..., description="Message content")
    role: str = Field(..., description="Message role (user/assistant)")
    timestamp: float = Field(..., description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional message metadata")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used")
    model_used: Optional[str] = Field(None, description="AI model used for response")


class ChatRequest(BaseModel):
    """Schema for chat message request."""
    
    message: str = Field(..., description="User message content")
    session_id: str = Field(..., description="Chat session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    options: Optional[Dict[str, Any]] = Field(None, description="Chat options")
    document_context: Optional[Dict[str, Any]] = Field(None, description="Word document context")


class ChatResponse(BaseModel):
    """Schema for chat message response."""
    
    message_id: str = Field(..., description="Unique response message identifier")
    session_id: str = Field(..., description="Chat session identifier")
    response: str = Field(..., description="AI-generated response")
    execution_time: float = Field(..., description="Response generation time in seconds")
    timestamp: float = Field(..., description="Response timestamp")
    model_used: str = Field(..., description="AI model used for response")
    tokens_used: int = Field(..., description="Number of tokens used")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional response metadata")
    suggestions: Optional[List[str]] = Field(None, description="Suggested follow-up questions")
    confidence: Optional[float] = Field(None, description="Response confidence score")


class ChatHistory(BaseModel):
    """Schema for chat session history."""
    
    session_id: str = Field(..., description="Chat session identifier")
    messages: List[ChatMessage] = Field(..., description="List of chat messages")
    total_messages: int = Field(..., description="Total number of messages")
    last_activity: float = Field(..., description="Last activity timestamp")
    created_at: float = Field(..., description="Session creation timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional session metadata")


class ChatSession(BaseModel):
    """Schema for a chat session."""
    
    session_id: str = Field(..., description="Unique session identifier")
    created_at: float = Field(..., description="Session creation timestamp")
    last_activity: float = Field(..., description="Last activity timestamp")
    message_count: int = Field(0, description="Number of messages in session")
    status: str = Field("active", description="Session status")
    user_id: Optional[str] = Field(None, description="User identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional session metadata")
    settings: Optional[Dict[str, Any]] = Field(None, description="Session settings")


class ChatStreamResponse(BaseModel):
    """Schema for streaming chat response."""
    
    type: str = Field(..., description="Response type (partial/complete/error)")
    content: Optional[str] = Field(None, description="Partial response content")
    message_id: Optional[str] = Field(None, description="Message identifier")
    session_id: str = Field(..., description="Chat session identifier")
    timestamp: float = Field(..., description="Response timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    error: Optional[str] = Field(None, description="Error message if type is error")


class ChatOptions(BaseModel):
    """Schema for chat configuration options."""
    
    model: Optional[str] = Field(None, description="AI model to use")
    temperature: Optional[float] = Field(0.7, description="Response creativity (0.0-1.0)")
    max_tokens: Optional[int] = Field(1000, description="Maximum response length")
    stream: Optional[bool] = Field(False, description="Enable streaming responses")
    language: Optional[str] = Field("en", description="Response language")
    tone: Optional[str] = Field("professional", description="Response tone")
    context_window: Optional[int] = Field(4000, description="Context window size")


class DocumentContext(BaseModel):
    """Schema for Word document context in chat."""
    
    document_id: Optional[str] = Field(None, description="Document identifier")
    document_title: Optional[str] = Field(None, description="Document title")
    current_section: Optional[str] = Field(None, description="Current document section")
    selected_text: Optional[str] = Field(None, description="Currently selected text")
    cursor_position: Optional[Dict[str, int]] = Field(None, description="Cursor position")
    document_stats: Optional[Dict[str, Any]] = Field(None, description="Document statistics")
    recent_changes: Optional[List[str]] = Field(None, description="Recent document changes")


class ChatAnalytics(BaseModel):
    """Schema for chat analytics and metrics."""
    
    session_id: str = Field(..., description="Chat session identifier")
    total_messages: int = Field(..., description="Total messages in session")
    user_messages: int = Field(..., description="Number of user messages")
    assistant_messages: int = Field(..., description="Number of assistant messages")
    total_tokens: int = Field(..., description="Total tokens used")
    average_response_time: float = Field(..., description="Average response time in seconds")
    session_duration: float = Field(..., description="Total session duration in seconds")
    topics_discussed: Optional[List[str]] = Field(None, description="Topics discussed")
    sentiment_score: Optional[float] = Field(None, description="Overall conversation sentiment")
    user_satisfaction: Optional[float] = Field(None, description="User satisfaction score")


class ChatFeedback(BaseModel):
    """Schema for chat feedback and ratings."""
    
    message_id: str = Field(..., description="Message identifier")
    session_id: str = Field(..., description="Chat session identifier")
    rating: int = Field(..., description="User rating (1-5)")
    feedback_text: Optional[str] = Field(None, description="User feedback text")
    helpful: Optional[bool] = Field(None, description="Whether response was helpful")
    timestamp: float = Field(..., description="Feedback timestamp")
    user_id: Optional[str] = Field(None, description="User identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional feedback metadata")


class ChatSuggestion(BaseModel):
    """Schema for chat suggestions and prompts."""
    
    id: str = Field(..., description="Suggestion identifier")
    text: str = Field(..., description="Suggestion text")
    category: str = Field(..., description="Suggestion category")
    context: Optional[str] = Field(None, description="When to show suggestion")
    priority: Optional[int] = Field(1, description="Suggestion priority (1-5)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional suggestion metadata")


class ChatCommand(BaseModel):
    """Schema for chat commands and actions."""
    
    command: str = Field(..., description="Command name")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Command parameters")
    session_id: str = Field(..., description="Chat session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    timestamp: float = Field(..., description="Command timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional command metadata")


class ChatError(BaseModel):
    """Schema for chat error responses."""
    
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    session_id: str = Field(..., description="Chat session identifier")
    timestamp: float = Field(..., description="Error timestamp")
    details: Optional[str] = Field(None, description="Detailed error information")
    suggestions: Optional[List[str]] = Field(None, description="Suggested solutions")
    retry_after: Optional[int] = Field(None, description="Retry after seconds")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional error metadata")
