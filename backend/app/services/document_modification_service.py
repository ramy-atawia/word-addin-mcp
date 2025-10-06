"""
Document Modification Service for Word Add-in MCP Project.

This service handles:
- LLM-based document analysis for modifications
- Paragraph-level processing
- Precise text matching and replacement
- Integration with existing LLM client
"""

import json
import logging
from typing import Dict, List, Any, Optional
from ..core.llm_client import LLMClient
from ..utils.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)

class DocumentModificationService:
    """Service for modifying documents at paragraph level using LLM analysis."""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.prompt_loader = PromptLoader()
    
    async def modify_document(
        self, 
        user_request: str, 
        paragraphs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Modify document based on user request using paragraph-level LLM analysis.
        
        Args:
            user_request: Natural language request from user
            paragraphs: List of paragraph objects with index, text, and formatting
            
        Returns:
            Modification plan with specific changes to make
        """
        try:
            logger.info(f"Processing document modification request: {user_request[:100]}...")
            logger.info(f"Document has {len(paragraphs)} paragraphs")
            
            # Load prompts
            system_prompt = self.prompt_loader.load_prompt("document_modification_system")
            user_prompt = self.prompt_loader.load_prompt(
                "document_modification_user",
                user_request=user_request,
                paragraphs=json.dumps(paragraphs, indent=2)
            )
            
            # Call LLM for analysis
            response = await self.llm_client.generate_text(
                prompt=user_prompt,
                system_message=system_prompt,
                max_tokens=4000
            )
            
            # Parse and validate LLM response
            modification_plan = self._parse_llm_response(response.get("text", ""))
            
            # Validate the plan structure
            if not self._validate_modification_plan(modification_plan):
                raise ValueError("Invalid modification plan structure")
            
            logger.info("Document modification plan generated successfully")
            return modification_plan
            
        except Exception as e:
            logger.error(f"Failed to generate modification plan: {str(e)}")
            raise
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response and extract modification plan."""
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in LLM response")
            
            json_str = response[json_start:json_end]
            modification_plan = json.loads(json_str)
            
            return modification_plan
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            raise ValueError(f"Invalid JSON in LLM response: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error parsing LLM response: {str(e)}")
            raise
    
    def _validate_modification_plan(self, plan: Dict[str, Any]) -> bool:
        """Validate the structure of the modification plan."""
        try:
            # Check required top-level keys
            if 'modifications' not in plan:
                return False
            
            if not isinstance(plan['modifications'], list):
                return False
            
            # Validate each modification
            for modification in plan['modifications']:
                if not self._validate_modification(modification):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating modification plan: {str(e)}")
            return False
    
    def _validate_modification(self, modification: Dict[str, Any]) -> bool:
        """Validate individual modification structure."""
        required_fields = ['paragraph_index', 'changes']
        
        for field in required_fields:
            if field not in modification:
                return False
        
        # Validate paragraph_index is integer
        if not isinstance(modification['paragraph_index'], int):
            return False
        
        # Validate changes is list
        if not isinstance(modification['changes'], list):
            return False
        
        # Validate each change
        for change in modification['changes']:
            if not self._validate_change(change):
                return False
        
        return True
    
    def _validate_change(self, change: Dict[str, Any]) -> bool:
        """Validate individual change structure."""
        required_fields = ['action', 'exact_find_text', 'replace_text', 'reason']
        
        for field in required_fields:
            if field not in change:
                return False
            
            if not isinstance(change[field], str):
                return False
        
        # Validate action values
        valid_actions = ['replace', 'insert', 'delete']
        if change['action'] not in valid_actions:
            return False
        
        return True
    
    def get_modification_summary(self, plan: Dict[str, Any]) -> str:
        """Get a human-readable summary of the modification plan."""
        try:
            summary = plan.get('summary', 'No summary provided')
            modification_count = len(plan.get('modifications', []))
            total_changes = sum(len(mod.get('changes', [])) for mod in plan.get('modifications', []))
            
            return f"Modification Summary: {summary}. Paragraphs: {modification_count}. Changes: {total_changes} modifications."
            
        except Exception as e:
            logger.error(f"Error generating modification summary: {str(e)}")
            return "Modification plan generated successfully."
