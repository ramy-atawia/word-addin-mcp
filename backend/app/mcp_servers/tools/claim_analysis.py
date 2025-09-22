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
                logger.error("ClaimAnalysisService not available")
                raise RuntimeError("ClaimAnalysisService not available")
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
    
    def _load_user_prompt(self, claims: List[Dict[str, Any]], analysis_type: str, 
                         focus_areas: Optional[List[str]]) -> str:
        """Load user prompt for claim analysis."""
        try:
            with open("backend/app/prompts/claim_analysis_user.txt", "r") as f:
                template = f.read().strip()
            
            # Format claims for the prompt
            claims_text = ""
            for i, claim in enumerate(claims, 1):
                claims_text += f"Claim {i} ({claim.get('claim_type', 'unknown')}): {claim.get('claim_text', '')}\n\n"
            
            return template.format(
                claims_text=claims_text,
                analysis_type=analysis_type,
                focus_areas=", ".join(focus_areas) if focus_areas else "General patent analysis"
            )
        except FileNotFoundError:
            logger.warning("User prompt file not found, using default")
            # Fallback prompt
            claims_text = ""
            for i, claim in enumerate(claims, 1):
                claims_text += f"Claim {i}: {claim.get('claim_text', '')}\n\n"
            
            return f"""Analyze the following patent claims for validity, quality, and improvement opportunities:

{claims_text}

Analysis Type: {analysis_type}
Focus Areas: {focus_areas or 'General patent analysis'}

Provide comprehensive analysis covering:
1. Claim structure and dependencies
2. Validity assessment (35 USC 101, 112, 103, 102)
3. Quality evaluation (clarity, breadth, defensibility)
4. Improvement recommendations
5. Risk assessment and mitigation strategies"""