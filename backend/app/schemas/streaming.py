"""
Streaming API schemas for real-time agent progress updates.

This module defines the request and response models for streaming agent responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from enum import Enum
import time


class StreamEventType(str, Enum):
    """Types of streaming events."""
    WORKFLOW_START = "workflow_start"
    INTENT_DETECTED = "intent_detected"
    WORKFLOW_PLANNED = "workflow_planned"
    TOOL_EXECUTION_START = "tool_execution_start"
    TOOL_EXECUTION_PROGRESS = "tool_execution_progress"
    TOOL_EXECUTION_COMPLETE = "tool_execution_complete"
    RESPONSE_GENERATION_START = "response_generation_start"
    RESPONSE_CHUNK = "response_chunk"
    WORKFLOW_COMPLETE = "workflow_complete"
    ERROR = "error"


class StreamEvent(BaseModel):
    """Base streaming event model."""
    
    event_type: StreamEventType = Field(..., description="Type of streaming event")
    timestamp: float = Field(default_factory=time.time, description="Event timestamp")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data")
    
    class Config:
        use_enum_values = True


class WorkflowStartEvent(StreamEvent):
    """Event when workflow starts."""
    
    event_type: Literal[StreamEventType.WORKFLOW_START] = StreamEventType.WORKFLOW_START
    data: Dict[str, Any] = Field(..., description="Workflow initialization data")


class IntentDetectedEvent(StreamEvent):
    """Event when intent is detected."""
    
    event_type: Literal[StreamEventType.INTENT_DETECTED] = StreamEventType.INTENT_DETECTED
    data: Dict[str, Any] = Field(..., description="Intent detection results")


class WorkflowPlannedEvent(StreamEvent):
    """Event when workflow is planned."""
    
    event_type: Literal[StreamEventType.WORKFLOW_PLANNED] = StreamEventType.WORKFLOW_PLANNED
    data: Dict[str, Any] = Field(..., description="Workflow plan details")


class ToolExecutionStartEvent(StreamEvent):
    """Event when tool execution starts."""
    
    event_type: Literal[StreamEventType.TOOL_EXECUTION_START] = StreamEventType.TOOL_EXECUTION_START
    data: Dict[str, Any] = Field(..., description="Tool execution start data")


class ToolExecutionProgressEvent(StreamEvent):
    """Event for tool execution progress updates."""
    
    event_type: Literal[StreamEventType.TOOL_EXECUTION_PROGRESS] = StreamEventType.TOOL_EXECUTION_PROGRESS
    data: Dict[str, Any] = Field(..., description="Tool execution progress data")


class ToolExecutionCompleteEvent(StreamEvent):
    """Event when tool execution completes."""
    
    event_type: Literal[StreamEventType.TOOL_EXECUTION_COMPLETE] = StreamEventType.TOOL_EXECUTION_COMPLETE
    data: Dict[str, Any] = Field(..., description="Tool execution completion data")


class ResponseGenerationStartEvent(StreamEvent):
    """Event when response generation starts."""
    
    event_type: Literal[StreamEventType.RESPONSE_GENERATION_START] = StreamEventType.RESPONSE_GENERATION_START
    data: Dict[str, Any] = Field(..., description="Response generation start data")


class ResponseChunkEvent(StreamEvent):
    """Event for streaming response chunks."""
    
    event_type: Literal[StreamEventType.RESPONSE_CHUNK] = StreamEventType.RESPONSE_CHUNK
    data: Dict[str, Any] = Field(..., description="Response chunk data")


class WorkflowCompleteEvent(StreamEvent):
    """Event when workflow completes."""
    
    event_type: Literal[StreamEventType.WORKFLOW_COMPLETE] = StreamEventType.WORKFLOW_COMPLETE
    data: Dict[str, Any] = Field(..., description="Workflow completion data")


class ErrorEvent(StreamEvent):
    """Event for errors."""
    
    event_type: Literal[StreamEventType.ERROR] = StreamEventType.ERROR
    data: Dict[str, Any] = Field(..., description="Error data")


class StreamingAgentChatRequest(BaseModel):
    """Request model for streaming agent chat endpoint."""
    
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
                "message": "I am writing a technical report on 5g please help me search web then perform prior art search followed by claims and then the final report",
                "context": {
                    "document_content": "",
                    "chat_history": "",
                    "available_tools": "web_search_tool,prior_art_search_tool,claim_drafting_tool,claim_analysis_tool"
                }
            }
        }
