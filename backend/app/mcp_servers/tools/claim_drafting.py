"""
Claim Drafting Tool

MCP tool for drafting patent claims using LLM integration.
"""

import time
import logging
from typing import Dict, Any, List, Optional

from app.mcp_servers.tools.base import BaseInternalTool

logger = logging.getLogger(__name__)


class ClaimDraftingTool(BaseInternalTool):
    """Tool for drafting patent claims."""
    
    def __init__(self):
        super().__init__(
            name="claim_drafting_tool",
            description="Draft patent claims based on invention description using LLM",
            version="1.0.0"
        )
        
        # Input schema
        self.input_schema = {
            "type": "object",
            "properties": {
                "invention_description": {
                    "type": "string",
                    "description": "Detailed description of the invention to draft claims for",
                    "minLength": 10,
                    "maxLength": 10000
                },
                "claim_count": {
                    "type": "integer",
                    "description": "Number of claims to generate",
                    "minimum": 1,
                    "maximum": 20,
                    "default": 5
                },
                "include_dependent": {
                    "type": "boolean",
                    "description": "Whether to include dependent claims",
                    "default": True
                },
                "technical_focus": {
                    "type": "string",
                    "description": "Specific technical area focus",
                    "maxLength": 500
                },
                "conversation_context": {
                    "type": "string",
                    "description": "Additional context from conversation history",
                    "maxLength": 2000
                },
                "document_reference": {
                    "type": "string",
                    "description": "Reference to existing document content",
                    "maxLength": 5000
                }
            },
            "required": ["invention_description"]
        }
        
        # Output schema
        self.output_schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "invention_description": {"type": "string"},
                "claims_generated": {"type": "integer"},
                "claims": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "claim_number": {"type": "string"},
                            "claim_text": {"type": "string"},
                            "claim_type": {"type": "string"},
                            "dependency": {"type": "string"},
                            "technical_focus": {"type": "string"}
                        }
                    }
                },
                "drafting_report": {"type": "string"},
                "drafting_metadata": {
                    "type": "object",
                    "properties": {
                        "timestamp": {"type": "string"},
                        "claim_count": {"type": "integer"},
                        "include_dependent": {"type": "boolean"},
                        "technical_focus": {"type": "string"},
                        "execution_time": {"type": "number"}
                    }
                },
                "generated_drafting_criteria": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "key_technical_elements": {"type": "array", "items": {"type": "string"}},
                            "novel_aspects": {"type": "array", "items": {"type": "string"}},
                            "claim_structure": {"type": "object"},
                            "technical_terminology": {"type": "array", "items": {"type": "string"}},
                            "drafting_strategy": {"type": "string"},
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
        """Execute claim drafting tool."""
        start_time = time.time()
        self.usage_count += 1
        
        try:
            # Extract parameters
            invention_description = parameters.get("invention_description", "")
            claim_count = parameters.get("claim_count", 5)
            include_dependent = parameters.get("include_dependent", True)
            technical_focus = parameters.get("technical_focus")
            conversation_context = parameters.get("conversation_context")
            document_reference = parameters.get("document_reference")
            
            logger.info(f"Executing claim drafting tool for invention: {invention_description[:100]}...")
            
            # Validate parameters
            if not invention_description or len(invention_description.strip()) < 10:
                execution_time = time.time() - start_time
                return "Error: Invalid invention description - must be at least 10 characters long"
            
            # Use the claim drafting service
            try:
                from app.services.claim_drafting_service import ClaimDraftingService
                
                async with ClaimDraftingService() as drafting_service:
                    drafting_result, generated_criteria = await drafting_service.draft_claims(
                        invention_description=invention_description,
                        claim_count=claim_count,
                        include_dependent=include_dependent,
                        technical_focus=technical_focus,
                        conversation_context=conversation_context,
                        document_reference=document_reference
                    )
                    
                    logger.info(f"Received {len(generated_criteria)} generated criteria from drafting service")
                    logger.info(f"Generated criteria content: {generated_criteria}")
                    
                    # Return just the markdown report
                    execution_time = time.time() - start_time
                    self.update_usage_stats(execution_time)
                    
                    logger.info(f"Returning response with generated_drafting_criteria: {generated_criteria}")
                    return drafting_result["drafting_report"]
                    
            except ImportError:
                logger.error("ClaimDraftingService not available, using placeholder")
                execution_time = time.time() - start_time
                self.update_usage_stats(execution_time)
                
                return f"# Claim Drafting Report\n\n**Invention**: {invention_description}\n\n**Error**: ClaimDraftingService not configured. Please configure LLM credentials."
                
        except Exception as e:
            logger.error(f"Claim drafting tool execution failed: {e}")
            execution_time = time.time() - start_time
            self.update_usage_stats(execution_time)
            
            return f"# Claim Drafting Report\n\n**Error**: Claim drafting failed: {str(e)}"
    
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
