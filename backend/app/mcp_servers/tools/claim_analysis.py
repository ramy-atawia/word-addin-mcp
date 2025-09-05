"""
Claim Analysis Tool

MCP tool for analyzing patent claims for validity, quality, and improvement opportunities.
"""

import time
import logging
from typing import Dict, Any, List, Optional

from app.mcp_servers.tools.base import BaseInternalTool

logger = logging.getLogger(__name__)


class ClaimAnalysisTool(BaseInternalTool):
    """Tool for analyzing patent claims."""
    
    def __init__(self):
        super().__init__(
            name="claim_analysis_tool",
            description="Analyze patent claims for validity, quality, and improvement opportunities using LLM",
            version="1.0.0"
        )
        
        # Input schema
        self.input_schema = {
            "type": "object",
            "properties": {
                "claims": {
                    "type": "array",
                    "description": "List of patent claims to analyze",
                    "minItems": 1,
                    "maxItems": 50,
                    "items": {
                        "type": "object",
                        "properties": {
                            "claim_number": {"type": "string"},
                            "claim_text": {"type": "string"},
                            "claim_type": {"type": "string", "enum": ["independent", "dependent"]},
                            "dependency": {"type": "string"},
                            "technical_focus": {"type": "string"}
                        },
                        "required": ["claim_text"]
                    }
                },
                "analysis_type": {
                    "type": "string",
                    "description": "Type of analysis to perform",
                    "enum": ["basic", "comprehensive", "expert"],
                    "default": "comprehensive"
                },
                "focus_areas": {
                    "type": "array",
                    "description": "Specific areas to focus analysis on",
                    "items": {"type": "string"},
                    "maxItems": 10
                }
            },
            "required": ["claims"]
        }
        
        # Output schema
        self.output_schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "claims_analyzed": {"type": "integer"},
                "analysis_type": {"type": "string"},
                "analysis": {
                    "type": "object",
                    "properties": {
                        "quality_assessment": {"type": "object"},
                        "recommendations": {"type": "object"},
                        "risk_assessment": {"type": "object"}
                    }
                },
                "quality_assessment": {"type": "object"},
                "recommendations": {"type": "object"},
                "risk_assessment": {"type": "object"},
                "analysis_report": {"type": "string"},
                "analysis_metadata": {
                    "type": "object",
                    "properties": {
                        "timestamp": {"type": "string"},
                        "analysis_type": {"type": "string"},
                        "focus_areas": {"type": "array"},
                        "execution_time": {"type": "number"}
                    }
                },
                "generated_analysis_criteria": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "analysis_framework": {"type": "object"},
                            "focus_areas": {"type": "array"},
                            "analysis_priorities": {"type": "array"},
                            "expected_issues": {"type": "array"},
                            "analysis_strategy": {"type": "string"},
                            "reasoning": {"type": "string"}
                        }
                    }
                }
            }
        }
        
        # Usage statistics
        self.usage_count = 0
        self.total_execution_time = 0.0
        self.last_used = None
    
    async def execute(self, parameters: Dict[str, Any]) -> str:
        """Execute claim analysis tool."""
        start_time = time.time()
        self.usage_count += 1
        
        try:
            # Extract parameters
            claims = parameters.get("claims", [])
            analysis_type = parameters.get("analysis_type", "comprehensive")
            focus_areas = parameters.get("focus_areas", [])
            
            logger.info(f"Executing claim analysis tool for {len(claims)} claims")
            
            # Validate parameters
            if not claims or not isinstance(claims, list):
                execution_time = time.time() - start_time
                return "Error: Invalid claims input - claims must be a non-empty list"
            
            # Use the claim analysis service
            try:
                from app.services.claim_analysis_service import ClaimAnalysisService
                
                async with ClaimAnalysisService() as analysis_service:
                    analysis_result, generated_criteria = await analysis_service.analyze_claims(
                        claims=claims,
                        analysis_type=analysis_type,
                        focus_areas=focus_areas
                    )
                    
                    logger.info(f"Received {len(generated_criteria)} generated criteria from analysis service")
                    logger.info(f"Generated criteria content: {generated_criteria}")
                    
                    # Return just the markdown report
                    execution_time = time.time() - start_time
                    self.update_usage_stats(execution_time)
                    
                    logger.info(f"Returning response with generated_analysis_criteria: {generated_criteria}")
                    return analysis_result["analysis_report"]
                    
            except ImportError:
                logger.error("ClaimAnalysisService not available, using placeholder")
                execution_time = time.time() - start_time
                self.update_usage_stats(execution_time)
                
                return f"# Claim Analysis Report\n\n**Claims**: {len(claims)} claims\n\n**Error**: ClaimAnalysisService not configured. Please configure LLM credentials."
                
        except Exception as e:
            logger.error(f"Claim analysis tool execution failed: {e}")
            execution_time = time.time() - start_time
            self.update_usage_stats(execution_time)
            
            return f"# Claim Analysis Report\n\n**Error**: Claim analysis failed: {str(e)}"
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Get tool information."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "usage_count": self.usage_count,
            "total_execution_time": self.total_execution_time,
            "last_used": self.last_used,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema
        }
    
    def update_usage_stats(self, execution_time: float):
        """Update usage statistics."""
        self.total_execution_time += execution_time
        self.last_used = time.time()
