"""
Legal Tools Schemas

Pydantic models for legal tool requests and responses.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class PriorArtSearchRequest(BaseModel):
    """Request model for prior art search tool."""
    
    query: str = Field(
        ..., 
        description="Search query for prior art",
        min_length=3,
        max_length=1000
    )
    
    context: Optional[str] = Field(
        default=None,
        description="Context from Word document"
    )
    
    conversation_history: Optional[str] = Field(
        default=None,
        description="Conversation history context"
    )
    
    max_results: int = Field(
        default=20,
        description="Maximum number of results to return",
        ge=1,
        le=100
    )


class PriorArtSearchResponse(BaseModel):
    """Response model for prior art search tool."""
    
    status: str = Field(..., description="Tool execution status")
    result: str = Field(..., description="Main tool output (comprehensive markdown report)")
    tool_name: str = Field(..., description="Name of the tool executed")
    execution_time: float = Field(..., description="Time taken to execute the tool")
    success: bool = Field(..., description="Whether the tool executed successfully")
    error: Optional[str] = Field(None, description="Error message if execution failed")


class ClaimDraftingRequest(BaseModel):
    """Request model for claim drafting tool."""
    
    invention_description: str = Field(
        ..., 
        description="Detailed description of the invention",
        min_length=10,
        max_length=10000
    )
    
    claim_count: int = Field(
        default=5,
        description="Number of claims to generate",
        ge=1,
        le=20
    )
    
    include_dependent: bool = Field(
        default=True,
        description="Whether to include dependent claims"
    )
    
    technical_focus: Optional[str] = Field(
        default=None,
        description="Specific technical area focus"
    )
    
    conversation_context: Optional[str] = Field(
        default=None,
        description="Additional context from conversation history"
    )
    
    document_reference: Optional[str] = Field(
        default=None,
        description="Reference to existing document content"
    )


class ClaimDraftingResponse(BaseModel):
    """Response model for claim drafting tool."""
    
    status: str = Field(..., description="Tool execution status")
    result: str = Field(..., description="Main tool output (comprehensive drafting report)")
    tool_name: str = Field(..., description="Name of the tool executed")
    execution_time: float = Field(..., description="Time taken to execute the tool")
    success: bool = Field(..., description="Whether the tool executed successfully")
    error: Optional[str] = Field(None, description="Error message if execution failed")


class ClaimAnalysisRequest(BaseModel):
    """Request model for claim analysis tool."""
    
    claims: List[Dict[str, Any]] = Field(
        ...,
        description="List of patent claims to analyze",
        min_items=1,
        max_items=50
    )
    
    analysis_type: str = Field(
        default="comprehensive",
        description="Type of analysis to perform",
        pattern="^(basic|comprehensive|expert)$"
    )
    
    focus_areas: Optional[List[str]] = Field(
        default=None,
        description="Specific areas to focus analysis on",
        max_items=10
    )


class ClaimAnalysisResponse(BaseModel):
    """Response model for claim analysis tool."""
    
    status: str = Field(..., description="Tool execution status")
    result: str = Field(..., description="Main tool output (comprehensive analysis report)")
    tool_name: str = Field(..., description="Name of the tool executed")
    execution_time: float = Field(..., description="Time taken to execute the tool")
    success: bool = Field(..., description="Whether the tool executed successfully")
    error: Optional[str] = Field(None, description="Error message if execution failed")