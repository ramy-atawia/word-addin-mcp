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
            
            # For now, return a mock response structure
            # In a real implementation, this would call the LLM service
            mock_response = {
                "modifications": [
                    {
                        "paragraph_index": 0,
                        "changes": [
                            {
                                "action": "replace",
                                "exact_find_text": "sample text",
                                "replace_text": "modified text",
                                "reason": "Updated based on user request"
                            }
                        ]
                    }
                ],
                "summary": "Document modification plan generated"
            }
            
            logger.info("Document modification plan generated successfully")
            return mock_response
            
        except Exception as e:
            logger.error(f"Failed to generate modification plan: {str(e)}")
            raise
    
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
