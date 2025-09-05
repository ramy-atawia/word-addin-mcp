"""
Patent Data Models

Pydantic models for patent-specific data structures.
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class PatentClaim(BaseModel):
    """Model for patent claim data."""
    
    claim_number: str = Field(..., description="Claim number")
    claim_text: str = Field(..., description="Full claim text")
    claim_type: str = Field(..., description="Type: independent or dependent")
    dependency: Optional[str] = Field(None, description="Dependency reference for dependent claims")
    is_exemplary: bool = Field(default=False, description="Whether claim is exemplary")


class PatentData(BaseModel):
    """Model for patent data from search results."""
    
    patent_id: str = Field(..., description="Patent ID")
    title: str = Field(..., description="Patent title")
    abstract: str = Field(..., description="Patent abstract")
    inventors: List[str] = Field(default_factory=list, description="List of inventors")
    assignees: List[str] = Field(default_factory=list, description="List of assignees")
    publication_date: Optional[str] = Field(None, description="Publication date")
    patent_year: Optional[str] = Field(None, description="Patent year")
    
    @field_validator('patent_year', mode='before')
    @classmethod
    def convert_patent_year(cls, v):
        """Convert patent year to string if it's an integer."""
        if v is not None:
            return str(v)
        return v
    claims: List[PatentClaim] = Field(default_factory=list, description="Patent claims")
    relevance_score: float = Field(..., description="Relevance score (0.0-1.0)")
    strategy_name: str = Field(..., description="Search strategy that found this patent")


class SearchStrategy(BaseModel):
    """Model for search strategy configuration."""
    
    name: str = Field(..., description="Strategy name")
    description: str = Field(..., description="Strategy description")
    query: Dict[str, Any] = Field(..., description="Search query parameters")
    expected_results: int = Field(default=10, description="Expected number of results")
    priority: int = Field(default=1, description="Strategy priority")


class SearchResult(BaseModel):
    """Model for complete search results."""
    
    query: str = Field(..., description="Original search query")
    total_found: int = Field(..., description="Total patents found")
    patents: List[PatentData] = Field(..., description="List of patent results")
    search_strategies: List[SearchStrategy] = Field(..., description="Search strategies used")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Search timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ClaimQualityMetrics(BaseModel):
    """Model for claim quality assessment metrics."""
    
    technical_terms_count: int = Field(..., description="Number of technical terms")
    technical_areas: List[str] = Field(..., description="Technical areas covered")
    quality_score: float = Field(..., description="Overall quality score (0.0-1.0)")
    issues: List[str] = Field(default_factory=list, description="Identified issues")
    structure: Dict[str, Any] = Field(..., description="Claim structure analysis")


class PatentRiskAssessment(BaseModel):
    """Model for patent risk assessment."""
    
    overall_risk: str = Field(..., description="Overall risk level: LOW/MEDIUM/HIGH")
    blocking_potential: str = Field(..., description="Blocking potential assessment")
    design_around_feasibility: str = Field(..., description="Design-around feasibility")
    commercial_impact: str = Field(..., description="Commercial impact assessment")
    key_risks: List[str] = Field(..., description="List of key risks identified")
    mitigation_strategies: List[str] = Field(..., description="Recommended mitigation strategies")
