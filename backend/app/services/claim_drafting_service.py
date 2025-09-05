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
            azure_openai_deployment=settings.azure_openai_deployment_name
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
    
    async def draft_claims(self, invention_description: str, claim_count: int = 5, 
                          include_dependent: bool = True, technical_focus: Optional[str] = None,
                          conversation_context: Optional[str] = None, 
                          document_reference: Optional[str] = None) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Draft patent claims based on invention description."""
        try:
            logger.info(f"Starting claim drafting for invention: {invention_description[:100]}...")
            
            # Generate LLM drafting criteria
            llm_criteria = await self._generate_llm_drafting_criteria(
                invention_description, claim_count, include_dependent, 
                technical_focus, conversation_context, document_reference
            )
            
            # Draft claims using LLM
            claims_result = await self._draft_claims_with_llm(
                invention_description, claim_count, include_dependent,
                technical_focus, conversation_context, document_reference
            )
            
            # Generate drafting report
            drafting_report = await self._generate_drafting_report(claims_result, invention_description)
            
            # Create result
            result = {
                "invention_description": invention_description,
                "claims_generated": len(claims_result.get("claims", [])),
                "claims": claims_result.get("claims", []),
                "drafting_report": drafting_report,
                "drafting_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "claim_count": claim_count,
                    "include_dependent": include_dependent,
                    "technical_focus": technical_focus,
                    "execution_time": time.time()
                }
            }
            
            logger.info(f"Claim drafting completed: {len(claims_result.get('claims', []))} claims generated")
            
            # Prepare LLM criteria for return
            generated_criteria = [llm_criteria]
            logger.info(f"Returning drafting result with {len(generated_criteria)} generated criteria")
            
            return result, generated_criteria
            
        except Exception as e:
            logger.error(f"Claim drafting failed for invention '{invention_description[:50]}': {str(e)}")
            raise
    
    async def _generate_llm_drafting_criteria(self, invention_description: str, claim_count: int,
                                            include_dependent: bool, technical_focus: Optional[str],
                                            conversation_context: Optional[str], 
                                            document_reference: Optional[str]) -> Dict[str, Any]:
        """Generate sophisticated drafting criteria using LLM."""
        try:
            prompt = f"""
You are a patent claim drafting expert. Given an invention description, generate optimized drafting criteria for patent claims.

Invention Description: "{invention_description}"

Parameters:
- Claim Count: {claim_count}
- Include Dependent Claims: {include_dependent}
- Technical Focus: {technical_focus or 'General'}
- Conversation Context: {conversation_context or 'None'}
- Document Reference: {document_reference or 'None'}

Generate drafting strategy considering:
1. Key technical elements to claim
2. Novel and non-obvious aspects
3. Claim structure and dependencies
4. Technical terminology optimization
5. USPTO compliance requirements

Return a JSON response with these fields:
{{
    "key_technical_elements": ["element1", "element2", "element3"],
    "novel_aspects": ["aspect1", "aspect2", "aspect3"],
    "claim_structure": {{
        "independent_claims": ["structure1", "structure2"],
        "dependent_claims": ["dependency1", "dependency2"]
    }},
    "technical_terminology": ["term1", "term2", "term3"],
    "drafting_strategy": "brief explanation of the drafting approach",
    "reasoning": "detailed reasoning for the drafting strategy"
}}

Focus on creating strong, defensible patent claims that cover the invention comprehensively.
"""
            
            response_data = self.llm_client.generate_text(
                prompt=prompt,
                max_tokens=800,
                temperature=0.3
            )
            response = response_data.get("text", "")
            
            # Parse the JSON response (handle markdown-wrapped responses)
            try:
                # Remove markdown code blocks if present
                if response.startswith("```json"):
                    response = response.replace("```json", "").replace("```", "").strip()
                elif response.startswith("```"):
                    response = response.replace("```", "").strip()
                
                criteria = json.loads(response)
                logger.info(f"Generated LLM drafting criteria: {criteria.get('reasoning', 'No reasoning provided')}")
                return criteria
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM response as JSON: {response}")
                return self._fallback_drafting_criteria(invention_description)
                
        except Exception as e:
            logger.error(f"LLM drafting criteria generation failed: {e}")
            return self._fallback_drafting_criteria(invention_description)
    
    def _fallback_drafting_criteria(self, invention_description: str) -> Dict[str, Any]:
        """Fallback drafting criteria when LLM generation fails."""
        return {
            "key_technical_elements": ["system", "method", "apparatus"],
            "novel_aspects": ["innovation", "improvement", "novelty"],
            "claim_structure": {
                "independent_claims": ["system claim", "method claim"],
                "dependent_claims": ["dependent system claim", "dependent method claim"]
            },
            "technical_terminology": ["device", "process", "technique"],
            "drafting_strategy": "Standard patent claim structure with system and method claims",
            "reasoning": "Fallback to standard drafting approach due to LLM generation failure"
        }
    
    async def _draft_claims_with_llm(self, invention_description: str, claim_count: int,
                                   include_dependent: bool, technical_focus: Optional[str],
                                   conversation_context: Optional[str], 
                                   document_reference: Optional[str]) -> Dict[str, Any]:
        """Draft claims using LLM integration."""
        try:
            # Load prompts
            system_prompt = self._load_system_prompt()
            user_prompt = self._load_user_prompt(
                invention_description, conversation_context, document_reference
            )
            
            # Define function schema for structured output
            functions = [{
                "type": "function",
                "function": {
                    "name": "draft_claims",
                    "description": "Draft patent claims based on invention description",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "claims": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "claim_number": {"type": "string"},
                                        "claim_text": {"type": "string"},
                                        "claim_type": {"type": "string", "enum": ["independent", "dependent"]},
                                        "dependency": {"type": "string", "description": "For dependent claims, which claim this depends on"},
                                        "technical_focus": {"type": "string", "description": "Main technical aspect of this claim"}
                                    },
                                    "required": ["claim_number", "claim_text", "claim_type"]
                                }
                            },
                            "drafting_notes": {"type": "string", "description": "Notes about the drafting approach"},
                            "quality_assessment": {"type": "string", "description": "Assessment of claim quality and strength"}
                        },
                        "required": ["claims", "drafting_notes", "quality_assessment"]
                    }
                }
            }]
            
            # Call LLM with function calling
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Use function calling for structured output
            response_data = self.llm_client.generate_text(
                prompt=user_prompt,
                system_message=system_prompt,
                max_tokens=4000,
                temperature=0.3
            )
            
            # Parse response
            response_text = response_data.get("text", "")
            
            # Try to parse as JSON first (for structured responses)
            try:
                if response_text.startswith("```json"):
                    response_text = response_text.replace("```json", "").replace("```", "").strip()
                elif response_text.startswith("```"):
                    response_text = response_text.replace("```", "").strip()
                
                result = json.loads(response_text)
            except json.JSONDecodeError:
                # If not JSON, parse as natural language patent claims
                result = self._parse_natural_language_claims(response_text, invention_description, claim_count)
            
            # Validate and clean claims
            if not result.get("claims") or not isinstance(result["claims"], list):
                result = self._create_fallback_claims(invention_description, claim_count)
            
            # Ensure we have the required fields
            if "drafting_notes" not in result:
                result["drafting_notes"] = "Claims drafted based on invention description"
            if "quality_assessment" not in result:
                result["quality_assessment"] = "Standard quality assessment pending detailed review"
            
            return result
            
        except Exception as e:
            logger.error(f"LLM claim drafting failed: {e}")
            return self._create_fallback_claims(invention_description, claim_count)
    
    def _parse_natural_language_claims(self, response_text: str, invention_description: str, claim_count: int) -> Dict[str, Any]:
        """Parse natural language patent claims from LLM response."""
        import re
        
        claims = []
        lines = response_text.split('\n')
        current_claim = None
        claim_counter = 1
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for claim patterns
            if re.match(r'^\d+\.', line) or 'claim' in line.lower():
                # Save previous claim if exists
                if current_claim:
                    claims.append(current_claim)
                    claim_counter += 1
                
                # Start new claim
                claim_text = re.sub(r'^\d+\.\s*', '', line)
                current_claim = {
                    "claim_number": str(claim_counter),
                    "claim_text": claim_text,
                    "claim_type": "independent" if claim_counter == 1 else "dependent",
                    "technical_focus": "system architecture" if claim_counter == 1 else "additional features"
                }
                
                if claim_counter > 1:
                    current_claim["dependency"] = "1"
            elif current_claim and line:
                # Continue building current claim
                current_claim["claim_text"] += " " + line
        
        # Add the last claim
        if current_claim:
            claims.append(current_claim)
        
        # If no claims found, try to extract from the text
        if not claims:
            # Look for any sentence that starts with "A" or "The" and contains technical terms
            sentences = re.split(r'[.!?]+', response_text)
            for sentence in sentences:
                sentence = sentence.strip()
                if (sentence.startswith(('A ', 'The ', 'An ')) and 
                    len(sentence) > 20 and 
                    any(term in sentence.lower() for term in ['system', 'method', 'apparatus', 'device', 'process'])):
                    claims.append({
                        "claim_number": str(len(claims) + 1),
                        "claim_text": sentence,
                        "claim_type": "independent" if len(claims) == 0 else "dependent",
                        "technical_focus": "system architecture" if len(claims) == 0 else "additional features"
                    })
                    if len(claims) > 1:
                        claims[-1]["dependency"] = "1"
        
        # Limit to requested count
        claims = claims[:claim_count]
        
        return {
            "claims": claims,
            "drafting_notes": "Claims parsed from natural language LLM response",
            "quality_assessment": "Claims generated using LLM with natural language processing"
        }
    
    def _create_fallback_claims(self, invention_description: str, claim_count: int) -> Dict[str, Any]:
        """Create fallback claims when LLM fails."""
        claims = []
        
        # Create basic independent claim
        claims.append({
            "claim_number": "1",
            "claim_text": f"A system for {invention_description[:100]}...",
            "claim_type": "independent",
            "technical_focus": "system architecture"
        })
        
        # Create dependent claims if requested
        if claim_count > 1:
            for i in range(2, min(claim_count + 1, 6)):
                claims.append({
                    "claim_number": str(i),
                    "claim_text": f"The system of claim 1, further comprising...",
                    "claim_type": "dependent",
                    "dependency": "1",
                    "technical_focus": "additional features"
                })
        
        return {
            "claims": claims,
            "drafting_notes": "Fallback claims generated due to LLM processing issues",
            "quality_assessment": "Basic claims structure - requires manual review and refinement"
        }
    
    def _load_system_prompt(self) -> str:
        """Load system prompt for claim drafting."""
        try:
            with open("backend/app/prompts/claim_drafting_system.txt", "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return """You are a patent claim specialist. Draft clear, concise, and technically accurate patent claims that follow USPTO requirements and best practices."""
    
    def _load_user_prompt(self, invention_description: str, conversation_context: Optional[str], 
                         document_reference: Optional[str]) -> str:
        """Load and format user prompt for claim drafting."""
        try:
            with open("backend/app/prompts/claim_drafting_user.txt", "r") as f:
                template = f.read().strip()
            
            return template.format(
                user_query=invention_description,
                conversation_context=conversation_context or "No additional context provided",
                document_reference=document_reference or "No document reference provided"
            )
        except FileNotFoundError:
            return f"""Draft patent claims for the following invention:

{invention_description}

Context: {conversation_context or "No additional context"}
Document Reference: {document_reference or "No document reference"}

Generate clear, technically accurate patent claims following USPTO requirements."""
    
    async def _generate_drafting_report(self, claims_result: Dict[str, Any], invention_description: str) -> str:
        """Generate comprehensive drafting report."""
        try:
            claims = claims_result.get("claims", [])
            drafting_notes = claims_result.get("drafting_notes", "")
            quality_assessment = claims_result.get("quality_assessment", "")
            
            report = f"# Patent Claim Drafting Report\n\n"
            
            # Executive Summary
            report += f"## 1. Executive Summary\n"
            report += f"Successfully drafted {len(claims)} patent claims for the invention: '{invention_description[:100]}...'\n\n"
            
            # Claims Overview
            report += f"## 2. Claims Overview\n"
            independent_claims = [c for c in claims if c.get("claim_type") == "independent"]
            dependent_claims = [c for c in claims if c.get("claim_type") == "dependent"]
            
            report += f"- **Independent Claims**: {len(independent_claims)}\n"
            report += f"- **Dependent Claims**: {len(dependent_claims)}\n"
            report += f"- **Total Claims**: {len(claims)}\n\n"
            
            # Individual Claims Analysis
            report += f"## 3. Individual Claims Analysis\n"
            for claim in claims:
                report += f"**Claim {claim.get('claim_number', 'N/A')}** ({claim.get('claim_type', 'unknown')})\n"
                report += f"- Technical Focus: {claim.get('technical_focus', 'Not specified')}\n"
                if claim.get('dependency'):
                    report += f"- Depends on: Claim {claim.get('dependency')}\n"
                report += f"- Text: {claim.get('claim_text', '')[:200]}...\n\n"
            
            # Quality Assessment
            report += f"## 4. Quality Assessment\n"
            report += f"{quality_assessment}\n\n"
            
            # Drafting Notes
            report += f"## 5. Drafting Notes\n"
            report += f"{drafting_notes}\n\n"
            
            # Recommendations
            report += f"## 6. Recommendations\n"
            report += f"- Review all claims for clarity and technical accuracy\n"
            report += f"- Ensure proper claim dependencies for dependent claims\n"
            report += f"- Verify USPTO compliance and formatting\n"
            report += f"- Consider additional dependent claims for comprehensive coverage\n"
            report += f"- Conduct prior art search to validate novelty\n\n"
            
            # Metadata
            report += f"---\n"
            report += f"**Drafting Metadata:**\n"
            report += f"- Invention: {invention_description[:100]}...\n"
            report += f"- Claims generated: {len(claims)}\n"
            report += f"- Generated: {datetime.now().isoformat()}\n"
            report += f"- Quality level: {'High' if len(independent_claims) >= 2 else 'Standard'}\n"
            
            return report
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return f"Claim drafting completed for: {invention_description[:100]}... Generated {len(claims_result.get('claims', []))} claims."
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status and configuration."""
        return {
            "service": "ClaimDraftingService",
            "llm_configured": bool(self.llm_client),
            "status": "active"
        }
