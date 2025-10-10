"""
Document Modification Tool for Word Add-in MCP Project.

Handles paragraph-level document modifications with exact text matching,
track changes integration, and Office.js integration.
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from .base import BaseInternalTool

logger = logging.getLogger(__name__)


class ChangeInstruction(BaseModel):
    """Individual change instruction."""
    action: str = Field(..., description="Type of change: replace, insert, or delete")
    exact_find_text: str = Field(..., description="Exact text to find")
    replace_text: str = Field(..., description="Text to replace with")
    reason: str = Field(..., description="Reason for the change")


class DocumentModification(BaseModel):
    """Document modification for a specific paragraph."""
    paragraph_index: int = Field(..., description="Index of paragraph to modify")
    changes: List[ChangeInstruction] = Field(..., description="List of changes to apply")


class DocumentModificationTool(BaseInternalTool):
    """Tool for modifying documents at paragraph level."""
    
    def __init__(self):
        super().__init__(
            name="document_modification_tool",
            description="Modify documents at paragraph level with precise text changes"
        )
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the document modification tool.
        
        Args:
            parameters: Dictionary containing user_request and paragraphs
            
        Returns:
            Modification plan with specific changes to make
        """
        user_request = parameters.get("user_request", "")
        paragraphs = parameters.get("paragraphs", [])
        
        logger.info(f"Document modification tool called with user_request: '{user_request}', paragraphs: {len(paragraphs) if paragraphs else 0}")
        logger.debug(f"Parameters received: {parameters}")
        
        if not user_request.strip():
            logger.error("User request is empty")
            raise ValueError("User request cannot be empty")
        
        if not paragraphs:
            logger.error("Paragraphs array is empty")
            raise ValueError("Document paragraphs cannot be empty")
        
        logger.info(f"Processing modification: {user_request[:100]}...")
        
        # Try LLM-based modification first
        modifications = await self._generate_llm_plan(user_request, paragraphs)
        
        # Fallback to regex-based parsing
        if not modifications:
            logger.warning("LLM failed, using regex fallback")
            modifications = self._generate_regex_plan(user_request, paragraphs)
        
        # If still no modifications, provide helpful error
        if not modifications:
            logger.error(f"No modifications could be generated for request: {user_request}")
            return {
                "modifications": [],
                "summary": f"No modifications found for request: '{user_request}'. Please check the text exists in the document.",
                "error": f"Could not parse modification request: '{user_request}'"
            }
        
        return {
            "modifications": modifications,
            "summary": f"Generated {len(modifications)} modification(s)"
        }
    
    async def _generate_llm_plan(
        self, 
        user_request: str, 
        paragraphs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate modification plan using LLM."""
        try:
            from ...services.llm_client import LLMClient
            from ...utils.prompt_loader import load_prompt
            
            llm_client = LLMClient()
            
            # Prepare document content
            doc_content = "\n\n".join([
                f"Paragraph {i}: {p.get('text', '')}" 
                for i, p in enumerate(paragraphs)
            ])
            
            # Load and format prompts
            system_prompt = load_prompt("document_modification_system")
            user_prompt = load_prompt("document_modification_user").format(
                user_request=user_request,
                paragraphs_json=doc_content
            )
            
            # Get LLM response
            response = await llm_client.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.1
            )
            
            logger.info(f"LLM response received: {len(response)} characters")
            
            # Extract and parse JSON response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end <= json_start:
                logger.warning(f"LLM response contains no valid JSON: {response[:200]}...")
                return []
            
            try:
                plan = json.loads(response[json_start:json_end])
            except json.JSONDecodeError as e:
                logger.error(f"LLM response JSON parsing failed: {e}")
                logger.error(f"Response content: {response[json_start:json_end]}")
                return []
            
            # Convert to internal format
            modifications = []
            for mod in plan.get('modifications', []):
                changes = [
                    {
                        "action": c.get('action', 'replace'),
                        "exact_find_text": c.get('exact_find_text', ''),
                        "replace_text": c.get('replace_text', ''),
                        "reason": c.get('reason', 'LLM modification')
                    }
                    for c in mod.get('changes', [])
                ]
                
                if changes:
                    modifications.append({
                        "paragraph_index": mod.get('paragraph_index', 0),
                        "changes": changes
                    })
            
            return modifications
            
        except ImportError as e:
            logger.error(f"Failed to import LLM dependencies: {e}")
            return []
        except Exception as e:
            logger.error(f"LLM plan generation failed: {e}")
            return []
    
    def _generate_regex_plan(
        self, 
        user_request: str, 
        paragraphs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate modification plan using regex parsing."""
        instruction = self._parse_request(user_request)
        
        if not instruction:
            return []
        
        from_text = instruction['from']
        to_text = instruction['to']
        modifications = []
        
        # Apply changes to matching paragraphs
        for i, paragraph in enumerate(paragraphs):
            text = paragraph.get('text', '')
            change = self._find_and_replace(text, from_text, to_text)
            
            if change:
                modifications.append({
                    "paragraph_index": i,
                    "changes": [change]
                })
        
        return modifications
    
    def _parse_request(self, user_request: str) -> Optional[Dict[str, str]]:
        """Parse user request to extract from/to text."""
        request_lower = user_request.lower()
        
        # Patterns for different modification requests
        patterns = [
            (r"change\s+['\"]?([^'\"]+)['\"]?\s+to\s+['\"]?([^'\"]+)['\"]?", None),
            (r"change\s+['\"]?([^'\"]+)['\"]?\s+with\s+['\"]?([^'\"]+)['\"]?", None),  # Added "change X with Y"
            (r"replace\s+['\"]?([^'\"]+)['\"]?\s+with\s+['\"]?([^'\"]+)['\"]?", None),
            (r"replace\s+['\"]?([^'\"]+)['\"]?\s+to\s+['\"]?([^'\"]+)['\"]?", None),   # Added "replace X to Y"
            (r"modify\s+['\"]?([^'\"]+)['\"]?\s+to\s+['\"]?([^'\"]+)['\"]?", None),
            (r"modify\s+['\"]?([^'\"]+)['\"]?\s+with\s+['\"]?([^'\"]+)['\"]?", None),  # Added "modify X with Y"
            # More flexible patterns for phrases with spaces
            (r"replace\s+([^'\"]+?)\s+in\s+the\s+doc\s+with\s+([^'\"]+)", None),  # "replace X in the doc with Y"
            (r"change\s+([^'\"]+?)\s+in\s+the\s+doc\s+to\s+([^'\"]+)", None),      # "change X in the doc to Y"
            (r"change\s+([^'\"]+?)\s+in\s+the\s+doc\s+with\s+([^'\"]+)", None),   # "change X in the doc with Y"
        ]
        
        for pattern, special_from in patterns:
            match = re.search(pattern, request_lower)
            if match:
                return {
                    "from": match.group(1).strip(), 
                    "to": match.group(2).strip()
                }
        
        return None
    
    def _find_and_replace(
        self, 
        text: str, 
        from_text: str, 
        to_text: str
    ) -> Optional[Dict[str, str]]:
        """Find and create replacement instruction for text."""
        # Case-insensitive search
        pattern = re.compile(re.escape(from_text), re.IGNORECASE)
        match = pattern.search(text)
        
        if match:
            return {
                "action": "replace",
                "exact_find_text": match.group(0),  # Preserve original case
                "replace_text": to_text,
                "reason": f"Changed '{match.group(0)}' to '{to_text}'"
            }
        
        # Try word-by-word match for phrases
        for word in text.split():
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word.lower() == from_text.lower():
                return {
                    "action": "replace",
                    "exact_find_text": word,
                    "replace_text": to_text,
                    "reason": f"Changed '{word}' to '{to_text}'"
                }
        
        return None