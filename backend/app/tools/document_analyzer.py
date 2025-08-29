"""
Document Analyzer Tool for Word Add-in MCP Project.

This tool implements the MCP tool interface for document analysis.
"""

from typing import Dict, Any
from app.core.mcp_tool_interface import (
    BaseMCPTool,
    ToolMetadata,
    ToolExecutionContext,
    ToolExecutionResult,
    ToolExecutionStatus,
    ToolErrorCode
)


class DocumentAnalyzerTool(BaseMCPTool):
    """MCP tool for document analysis."""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="document_analyzer",
            description="Analyze documents for structure, content, and insights",
            version="1.0.0",
            author="Word Add-in MCP Project",
            tags=["document", "analysis", "insights"],
            category="document_processing",
            input_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Document content to analyze"},
                    "analysis_type": {"type": "string", "enum": ["structure", "content", "insights"], "default": "content"}
                },
                "required": ["content"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "analysis_type": {"type": "string"},
                    "summary": {"type": "string"},
                    "metrics": {"type": "object"},
                    "suggestions": {"type": "array"}
                }
            }
        )
        super().__init__(metadata)
    
    async def execute(self, context: ToolExecutionContext) -> ToolExecutionResult:
        """Execute document analysis."""
        try:
            content = context.parameters.get("content", "")
            analysis_type = context.parameters.get("analysis_type", "content")
            
            if not content:
                return ToolExecutionResult(
                    status=ToolExecutionStatus.FAILED,
                    error_code=ToolErrorCode.INVALID_PARAMETERS,
                    error_message="Document content is required"
                )
            
            # Perform analysis based on type
            if analysis_type == "structure":
                result = self._analyze_structure(content)
            elif analysis_type == "content":
                result = self._analyze_content(content)
            elif analysis_type == "insights":
                result = self._analyze_insights(content)
            else:
                return ToolExecutionResult(
                    status=ToolExecutionStatus.FAILED,
                    error_code=ToolErrorCode.INVALID_PARAMETERS,
                    error_message=f"Unknown analysis type: {analysis_type}"
                )
            
            return ToolExecutionResult(
                status=ToolExecutionStatus.SUCCESS,
                data={
                    "analysis_type": analysis_type,
                    "summary": result["summary"],
                    "metrics": result["metrics"],
                    "suggestions": result["suggestions"]
                }
            )
            
        except Exception as e:
            return ToolExecutionResult(
                status=ToolExecutionStatus.FAILED,
                error_code=ToolErrorCode.EXECUTION_FAILED,
                error_message=str(e)
            )
    
    def _analyze_structure(self, content: str) -> Dict[str, Any]:
        """Analyze document structure."""
        lines = content.split('\n')
        paragraphs = content.split('\n\n')
        
        return {
            "summary": f"Document has {len(lines)} lines and {len(paragraphs)} paragraphs",
            "metrics": {
                "line_count": len(lines),
                "paragraph_count": len(paragraphs),
                "average_line_length": sum(len(line) for line in lines) / max(len(lines), 1)
            },
            "suggestions": ["Consider adding headers for better structure", "Use consistent paragraph spacing"]
        }
    
    def _analyze_content(self, content: str) -> Dict[str, Any]:
        """Analyze document content."""
        words = content.split()
        sentences = content.split('. ')
        
        return {
            "summary": f"Document contains {len(words)} words in {len(sentences)} sentences",
            "metrics": {
                "word_count": len(words),
                "sentence_count": len(sentences),
                "average_sentence_length": len(words) / max(len(sentences), 1)
            },
            "suggestions": ["Vary sentence lengths for better readability", "Use active voice when possible"]
        }
    
    def _analyze_insights(self, content: str) -> Dict[str, Any]:
        """Analyze document for insights."""
        # Simple insight generation
        insights = []
        if len(content) > 1000:
            insights.append("Document is comprehensive and detailed")
        if content.count('.') > content.count('!'):
            insights.append("Document uses mostly declarative sentences")
        
        return {
            "summary": f"Generated {len(insights)} insights about the document",
            "metrics": {"insight_count": len(insights)},
            "suggestions": insights
        }
