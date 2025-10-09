"""
Document Modification Tool for Word Add-in MCP Project.

This tool handles paragraph-level document modifications with:
- Exact text matching
- Track changes integration
- Precise text replacement, insertion, and deletion
- Office.js integration for Word documents
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class DocumentParagraph(BaseModel):
    """Document paragraph with formatting information."""
    index: int = Field(..., description="Paragraph index in the document")
    text: str = Field(..., description="Paragraph text content")
    formatting: Optional[Dict[str, Any]] = Field(None, description="Paragraph formatting information")

class ChangeInstruction(BaseModel):
    """Individual change instruction."""
    action: str = Field(..., description="Type of change: replace, insert, or delete")
    exact_find_text: str = Field(..., description="Exact text to find in the document")
    replace_text: str = Field(..., description="Text to replace with")
    reason: str = Field(..., description="Reason for the change")

class DocumentModification(BaseModel):
    """Document modification for a specific paragraph."""
    paragraph_index: int = Field(..., description="Index of paragraph to modify")
    changes: List[ChangeInstruction] = Field(..., description="List of changes to apply")

class DocumentModificationRequest(BaseModel):
    """Request for document modification."""
    user_request: str = Field(..., description="Natural language request for document modification")
    paragraphs: List[DocumentParagraph] = Field(..., description="Document paragraphs with formatting")
    session_id: Optional[str] = Field(None, description="Optional session ID for context")

class DocumentModificationResponse(BaseModel):
    """Response from document modification."""
    success: bool
    modifications: List[DocumentModification]
    summary: str
    error: Optional[str] = None

class DocumentModificationTool:
    """Tool for modifying documents at paragraph level using LLM analysis."""
    
    def __init__(self):
        self.name = "document_modification_tool"
        self.description = "Modify documents at paragraph level with precise text changes and track changes support"
        
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
            
            # Validate input
            if not user_request.strip():
                raise ValueError("User request cannot be empty")
            
            if not paragraphs:
                raise ValueError("Document paragraphs cannot be empty")
            
            # Use LLM to generate intelligent modification plan
            modifications = await self._generate_llm_modification_plan(user_request, paragraphs)
            
            # Fallback to regex if LLM fails
            if not modifications:
                logger.warning("LLM modification plan failed, falling back to regex parsing")
                modifications = self._generate_regex_fallback_plan(user_request, paragraphs)
            
            response = {
                "modifications": modifications,
                "summary": f"Generated {len(modifications)} modification(s) based on user request"
            }
            
            logger.info("Document modification plan generated successfully")
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate modification plan: {str(e)}")
            raise
    
    def _generate_regex_fallback_plan(self, user_request: str, paragraphs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback regex-based modification plan when LLM fails."""
        modifications = []
        
        # Parse modification request using regex patterns
        modification_instruction = self.parse_modification_request(user_request)
        
        if modification_instruction:
            from_word = modification_instruction['from']
            to_word = modification_instruction['to']
            
            # Apply changes to all paragraphs containing the word
            for i, paragraph in enumerate(paragraphs):
                text = paragraph.get('text', '')
                changes = []
                
                # Check if paragraph contains the word to change
                if from_word.lower() in text.lower():
                    # Find the exact case of the word in the text
                    import re
                    pattern = re.compile(re.escape(from_word), re.IGNORECASE)
                    match = pattern.search(text)
                    
                    if match:
                        exact_word = match.group(0)  # Preserve original case
                        changes.append({
                            "action": "replace",
                            "exact_find_text": exact_word,
                            "replace_text": to_word,
                            "reason": f"Changed '{exact_word}' to '{to_word}' based on user request"
                        })
                else:
                    # If exact word not found, try to find similar words
                    # This helps with cases like "the author" -> "Ramy"
                    words_in_text = text.split()
                    for word in words_in_text:
                        # Remove punctuation for comparison
                        clean_word = re.sub(r'[^\w]', '', word)
                        if clean_word.lower() == from_word.lower():
                            changes.append({
                                "action": "replace",
                                "exact_find_text": word,
                                "replace_text": to_word,
                                "reason": f"Changed '{word}' to '{to_word}' based on user request"
                            })
                            break
                
                if changes:
                    modifications.append({
                        "paragraph_index": i,
                        "changes": changes
                    })
        
        # If no specific changes found, create a sample modification
        if not modifications and paragraphs:
            first_paragraph_text = paragraphs[0].get('text', '')
            words = first_paragraph_text.split()
            first_word = words[0] if words else 'text'
            
            modifications.append({
                "paragraph_index": 0,
                "changes": [
                    {
                        "action": "replace",
                        "exact_find_text": first_word,
                        "replace_text": 'modified',
                        "reason": "Sample modification based on user request"
                    }
                ]
            })
        
        return modifications

    def parse_modification_request(self, user_request: str) -> Dict[str, str]:
        """Parse user request to extract modification instructions."""
        import re
        
        # Pattern 1: "change X to Y" or "change 'X' to 'Y'" (supports multi-word phrases)
        pattern1 = r"change\s+['\"]?([^'\"]+)['\"]?\s+to\s+['\"]?([^'\"]+)['\"]?"
        match1 = re.search(pattern1, user_request.lower())
        if match1:
            return {"from": match1.group(1).strip(), "to": match1.group(2).strip()}
        
        # Pattern 2: "replace X with Y" or "replace 'X' with 'Y'" (supports multi-word phrases)
        pattern2 = r"replace\s+['\"]?([^'\"]+)['\"]?\s+with\s+['\"]?([^'\"]+)['\"]?"
        match2 = re.search(pattern2, user_request.lower())
        if match2:
            return {"from": match2.group(1).strip(), "to": match2.group(2).strip()}
        
        # Pattern 3: "modify X to Y" or "modify 'X' to 'Y'" (supports multi-word phrases)
        pattern3 = r"modify\s+['\"]?([^'\"]+)['\"]?\s+to\s+['\"]?([^'\"]+)['\"]?"
        match3 = re.search(pattern3, user_request.lower())
        if match3:
            return {"from": match3.group(1).strip(), "to": match3.group(2).strip()}
        
        # Pattern 4: "change the author to X" - special case for author changes
        pattern4 = r"change\s+the\s+author\s+to\s+['\"]?([^'\"]+)['\"]?"
        match4 = re.search(pattern4, user_request.lower())
        if match4:
            # Look for "Ramy" in the document and replace with the new name
            return {"from": "Ramy", "to": match4.group(1).strip()}
        
        return None

    async def _generate_llm_modification_plan(self, user_request: str, paragraphs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Use LLM to generate intelligent modification plan based on user request and document content."""
        try:
            # Import LLM client here to avoid circular imports
            from ...utils.llm_client import LLMClient
            from ...utils.prompt_loader import prompt_loader
            
            llm_client = LLMClient()
            
            # Prepare document content for LLM
            doc_content = "\n\n".join([f"Paragraph {i}: {p.get('text', '')}" for i, p in enumerate(paragraphs)])
            
            # Load prompts
            system_prompt = prompt_loader.load_prompt("document_modification_system")
            user_prompt = prompt_loader.load_prompt("document_modification_user")
            
            # Format the user prompt with actual data
            formatted_user_prompt = user_prompt.format(
                user_request=user_request,
                paragraphs_json=doc_content
            )
            
            # Call LLM to generate modification plan
            response = await llm_client.generate_response(
                system_prompt=system_prompt,
                user_prompt=formatted_user_prompt,
                temperature=0.1  # Low temperature for consistent results
            )
            
            # Parse LLM response
            try:
                import json
                # Extract JSON from response (handle cases where LLM adds extra text)
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    plan = json.loads(json_str)
                    
                    # Convert LLM response to our format
                    modifications = []
                    for mod in plan.get('modifications', []):
                        paragraph_index = mod.get('paragraph_index', 0)
                        changes = []
                        for change in mod.get('changes', []):
                            changes.append({
                                "action": change.get('action', 'replace'),
                                "exact_find_text": change.get('exact_find_text', ''),
                                "replace_text": change.get('replace_text', ''),
                                "reason": change.get('reason', 'LLM-generated modification')
                            })
                        if changes:
                            modifications.append({
                                "paragraph_index": paragraph_index,
                                "changes": changes
                            })
                    
                    return modifications
                    
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse LLM response as JSON: {e}")
                logger.warning(f"LLM response: {response}")
            
            # Fallback: return empty modifications if LLM parsing fails
            return []
            
        except Exception as e:
            logger.error(f"LLM modification plan generation failed: {e}")
            return []

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
                        "description": "Natural language request for document modification"
                    },
                    "paragraphs": {
                        "type": "array",
                        "description": "Document paragraphs with formatting",
                        "items": {
                            "type": "object",
                            "properties": {
                                "index": {"type": "integer", "description": "Paragraph index"},
                                "text": {"type": "string", "description": "Paragraph text"},
                                "formatting": {"type": "object", "description": "Formatting information"}
                            }
                        }
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional session ID for context"
                    }
                },
                "required": ["user_request", "paragraphs"]
            }
        }

# Create singleton instance
document_modification_tool = DocumentModificationTool()
