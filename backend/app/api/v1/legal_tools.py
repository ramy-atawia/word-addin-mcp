"""
Legal Tools API Endpoints

API endpoints for legal-specific tools including patent search, claim drafting, and claim analysis.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import structlog

from app.schemas.legal_tools import (
    PriorArtSearchRequest, PriorArtSearchResponse,
    ClaimDraftingRequest, ClaimDraftingResponse,
    ClaimAnalysisRequest, ClaimAnalysisResponse
)
from app.mcp_servers.tool_registry import InternalToolRegistry

logger = structlog.get_logger()

router = APIRouter(prefix="/legal-tools", tags=["legal-tools"])


def get_tool_registry() -> InternalToolRegistry:
    """Get the tool registry instance."""
    return InternalToolRegistry()


@router.post("/prior-art-search", response_model=PriorArtSearchResponse)
async def prior_art_search(
    request: PriorArtSearchRequest,
    registry: InternalToolRegistry = Depends(get_tool_registry)
) -> PriorArtSearchResponse:
    """
    Search for prior art patents using PatentsView API.
    
    This endpoint provides comprehensive prior art search functionality including:
    - PatentsView API integration
    - LLM-enhanced search strategy generation
    - Relevance scoring and filtering
    - Detailed patent information extraction
    """
    try:
        logger.info(f"Prior art search request: {request.query}")
        
        # Execute the prior art search tool
        result = await registry.execute_tool(
            tool_name="prior_art_search_tool",
            parameters=request.dict()
        )
        
        if result["status"] != "success":
            raise HTTPException(
                status_code=500,
                detail=f"Prior art search failed: {result.get('error', 'Unknown error')}"
            )
        
        # Extract the tool result
        tool_result = result["result"]
        
        return PriorArtSearchResponse(
            query=tool_result["query"],
            results_found=tool_result["results_found"],
            patents=tool_result["patents"],
            search_summary=tool_result["search_summary"],
            search_metadata=tool_result["search_metadata"],
            report=tool_result["report"],
            generated_search_criteria=tool_result.get("generated_search_criteria", [])
        )
        
    except Exception as e:
        logger.error(f"Prior art search API error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Prior art search failed: {str(e)}"
        )


@router.post("/claim-drafting", response_model=ClaimDraftingResponse)
async def claim_drafting(
    request: ClaimDraftingRequest,
    registry: InternalToolRegistry = Depends(get_tool_registry)
) -> ClaimDraftingResponse:
    """
    Draft patent claims based on invention description.
    
    This endpoint provides intelligent claim drafting functionality including:
    - USPTO-compliant claim generation
    - Independent and dependent claim creation
    - Quality scoring and validation
    - Technical terminology optimization
    """
    try:
        logger.info(f"Claim drafting request for invention: {request.invention_description[:100]}...")
        
        # Execute the claim drafting tool
        result = await registry.execute_tool(
            tool_name="claim_drafting_tool",
            parameters=request.dict()
        )
        
        if result["status"] != "success":
            raise HTTPException(
                status_code=500,
                detail=f"Claim drafting failed: {result.get('error', 'Unknown error')}"
            )
        
        # Extract the tool result
        tool_result = result["result"]
        
        return ClaimDraftingResponse(
            invention_description=tool_result["invention_description"],
            claims_generated=tool_result["claims_generated"],
            claims=tool_result["claims"],
            drafting_report=tool_result["drafting_report"],
            drafting_metadata=tool_result["drafting_metadata"],
            generated_drafting_criteria=tool_result.get("generated_drafting_criteria", [])
        )
        
    except Exception as e:
        logger.error(f"Claim drafting API error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Claim drafting failed: {str(e)}"
        )


@router.post("/claim-analysis", response_model=ClaimAnalysisResponse)
async def claim_analysis(
    request: ClaimAnalysisRequest,
    registry: InternalToolRegistry = Depends(get_tool_registry)
) -> ClaimAnalysisResponse:
    """
    Analyze patent claims for validity, quality, and improvement opportunities.
    
    This endpoint provides comprehensive claim analysis functionality including:
    - Validity assessment (35 USC 101, 112, 103, 102)
    - Quality evaluation (clarity, breadth, defensibility)
    - Improvement recommendations
    - Risk assessment and mitigation strategies
    """
    try:
        logger.info(f"Claim analysis request for {len(request.claims)} claims")
        
        # Execute the claim analysis tool
        result = await registry.execute_tool(
            tool_name="claim_analysis_tool",
            parameters=request.dict()
        )
        
        if result["status"] != "success":
            raise HTTPException(
                status_code=500,
                detail=f"Claim analysis failed: {result.get('error', 'Unknown error')}"
            )
        
        # Extract the tool result
        tool_result = result["result"]
        
        return ClaimAnalysisResponse(
            claims_analyzed=tool_result["claims_analyzed"],
            analysis_type=tool_result["analysis_type"],
            analysis=tool_result["analysis"],
            quality_assessment=tool_result["quality_assessment"],
            recommendations=tool_result["recommendations"],
            risk_assessment=tool_result["risk_assessment"],
            analysis_report=tool_result["analysis_report"],
            analysis_metadata=tool_result["analysis_metadata"],
            generated_analysis_criteria=tool_result.get("generated_analysis_criteria", [])
        )
        
    except Exception as e:
        logger.error(f"Claim analysis API error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Claim analysis failed: {str(e)}"
        )