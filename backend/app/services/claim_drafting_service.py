"""
Claim Drafting Service

Service for drafting patent claims using LLM integration.
"""

import asyncio
import json
import time
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import os

from app.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


class ClaimDraftingService:
    """Service for drafting patent claims using LLM."""
    
    def __init__(self):
        # Get LLM configuration from settings
        from app.core.config import settings
        self.llm_client = LLMClient(
            azure_openai_api_key=settings.azure_openai_api_key,
            azure_openai_endpoint=settings.azure_openai_endpoint,
            azure_openai_deployment=settings.azure_openai_deployment
        )
        
        # Configuration
        self.default_max_claims = 10
        self.timeout = 120.0
        
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass
    
    async def draft_claims(self, user_query: str, conversation_context: Optional[str] = None, 
                          document_reference: Optional[str] = None) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Draft patent claims based on user query."""
        try:
            logger.info(f"Starting claim drafting for query: {user_query[:100]}...")
            
            # Draft claims using LLM - return simple markdown
            claims_markdown = await self._draft_claims_with_llm_simple(
                user_query, conversation_context, document_reference
            )
            
            # Create simple result
            result = {
                "user_query": user_query,
                "drafting_report": claims_markdown,
                "drafting_metadata": {
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            logger.info(f"Claim drafting completed: markdown report generated")
            
            # Return empty criteria list
            return result, []
            
        except Exception as e:
            logger.error(f"Claim drafting failed for query '{user_query[:50]}': {str(e)}")
            raise
    
    async def _draft_claims_with_llm_simple(self, user_query: str, conversation_context: Optional[str], 
                                          document_reference: Optional[str]) -> str:
        """Draft claims using LLM and return simple markdown string."""
        try:
            # Load prompts
            system_prompt = self._load_system_prompt()
            user_prompt = self._load_user_prompt()
            
            # Format user prompt with parameters
            formatted_user_prompt = user_prompt.format(
                user_query=user_query,
                conversation_context=conversation_context or "",
                document_reference=document_reference or ""
            )
            
            # Call LLM
            response_data = self.llm_client.generate_text(
                prompt=formatted_user_prompt,
                system_message=system_prompt,
                max_tokens=4000,
                temperature=0.3
            )
            
            # Return raw response as markdown
            return response_data.get("text", "Error: No response from LLM")
            
        except Exception as e:
            logger.error(f"Simple LLM claim drafting failed: {e}")
            return f"# Patent Claims\n\nError generating claims: {str(e)}"
    
    def _load_system_prompt(self) -> str:
        """Load system prompt for claim drafting."""
        try:
            with open("backend/app/prompts/claim_drafting_system.txt", "r") as f:
                return f.read()
        except FileNotFoundError:
            logger.warning("System prompt file not found, using default")
            return """You are a patent claim specialist. Generate high-quality patent claims in markdown format.

OUTPUT FORMAT:
Generate a markdown document with this structure:

# Patent Claims

## Claim 1 (Independent)
[Independent claim text describing the main invention with technical details]

## Claim 2 (Dependent)
The [system/method/apparatus] of claim 1, wherein [specific additional feature]

## Claim 3 (Dependent)
The [system/method/apparatus] of claim 1, further comprising [additional component]

[Continue with additional dependent claims as needed]

RULES:
- Use proper patent terminology (comprising, configured to, wherein, etc.)
- Make claims specific and technically detailed
- Ensure dependent claims properly reference their parent claims
- Focus on the novel and non-obvious aspects of the invention
- Use clear, unambiguous language
- Include technical details that make the invention unique"""
    
    def _load_user_prompt(self) -> str:
        """Load user prompt for claim drafting."""
        try:
            with open("backend/app/prompts/claim_drafting_user.txt", "r") as f:
                return f.read()
        except FileNotFoundError:
            logger.warning("User prompt file not found, using default")
            return """USER QUERY:
{user_query}

CONVERSATION CONTEXT:
{conversation_context}

DOCUMENT REFERENCE:
{document_reference}

TASK: Draft patent claims based on the user query above.

Generate a markdown document with patent claims that:
- Cover the invention described in the user query
- Use proper patent terminology and structure
- Include both independent and dependent claims
- Focus on technical details and novel aspects

Return the complete markdown document."""