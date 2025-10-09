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
        
        if not user_request.strip():
            raise ValueError("User request cannot be empty")
        
        if not paragraphs:
            raise ValueError("Document paragraphs cannot be empty")
        
        logger.info(f"Processing modification: {user_request[:100]}...")
        
        # Try LLM-based modification first
        modifications = await self._generate_llm_plan(user_request, paragraphs)
        
        # Fallback to regex-based parsing
        if not modifications:
            logger.warning("LLM failed, using regex fallback")
            modifications = self._generate_regex_plan(user_request, paragraphs)
        
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
            
            # Extract and parse JSON response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end <= json_start:
                return []
            
            plan = json.loads(response[json_start:json_end])
            
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
            (r"change\s+the\s+author\s+to\s+['\"]?([^'\"]+)['\"]?", "Ramy"),  # Special case
            (r"change\s+['\"]?([^'\"]+)['\"]?\s+to\s+['\"]?([^'\"]+)['\"]?", None),
            (r"replace\s+['\"]?([^'\"]+)['\"]?\s+with\s+['\"]?([^'\"]+)['\"]?", None),
            (r"modify\s+['\"]?([^'\"]+)['\"]?\s+to\s+['\"]?([^'\"]+)['\"]?", None),
        ]
        
        for pattern, special_from in patterns:
            match = re.search(pattern, request_lower)
            if match:
                if special_from:  # Author change special case
                    return {"from": special_from, "to": match.group(1).strip()}
                else:
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
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Get the tool definition for MCP registration."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "user_request": {
                        "type": "string",
                        "description": "Natural language request for modification"
                    },
                    "paragraphs": {
                        "type": "array",
                        "description": "Document paragraphs with formatting",
                        "items": {
                            "type": "object",
                            "properties": {
                                "index": {"type": "integer"},
                                "text": {"type": "string"},
                                "formatting": {"type": "object"}
                            }
                        }
                    }
                },
                "required": ["user_request", "paragraphs"]
            }
        }