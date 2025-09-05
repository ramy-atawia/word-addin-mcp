"""
Web Search Tool Implementation.

This tool provides web search functionality for the internal MCP server.
"""

import time
import structlog
from typing import Dict, Any
from .base import BaseInternalTool

logger = structlog.get_logger()


class WebSearchTool(BaseInternalTool):
    """Web search tool for finding information on the internet."""
    
    def __init__(self):
        super().__init__(
            name="web_search_tool",
            description="Search the web for information",
            version="1.0.0"
        )
        
        # Tool schema definition
        self.input_schema = {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 10
                }
            },
            "required": ["query"]
        }
        
        self.output_schema = {
            "type": "object",
            "properties": {
                "results": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
        
        self.examples = [
            {
                "input": {"query": "latest AI developments"},
                "output": {"results": ["AI breakthrough in...", "New research shows..."]}
            }
        ]
        
        self.tags = ["web", "search", "information"]
        self.category = "research"
        self.author = "Word Add-in MCP Project"
    
    async def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """Validate web search parameters."""
        query = parameters.get("query", "")
        if not query or not query.strip():
            return False, "Query parameter is required and cannot be empty"
        
        if len(query.strip()) < 2:
            return False, "Query must be at least 2 characters long"
            
        return True, ""
    
    async def execute(self, parameters: Dict[str, Any]) -> str:
        """Execute web search using real Google Search API."""
        start_time = time.time()
        
        try:
            # Validate parameters
            is_valid, error_message = await self.validate_parameters(parameters)
            if not is_valid:
                raise ValueError(error_message)
            
            query = parameters.get("query", "").strip()
            max_results = parameters.get("max_results", 10)
            logger.info(f"Executing web search for query: {query}")
            
            # Use the real web search service
            try:
                from app.services.web_search_service import WebSearchService
                
                async with WebSearchService() as search_service:
                    search_results = await search_service.search_google(
                        query=query, 
                        max_results=max_results,
                        include_abstracts=True
                    )
                
                if search_results:
                    # Format results for MCP response
                    formatted_results = []
                    for result in search_results:
                        formatted_results.append({
                            "title": result.get("title", ""),
                            "url": result.get("link", ""),  # Google API returns 'link' not 'url'
                            "snippet": result.get("snippet", ""),
                            "displayLink": result.get("link", "").replace("https://", "").replace("http://", "").split("/")[0],
                            "source": result.get("source", "Google Search"),
                            "type": result.get("type", "web_page")
                        })
                    
                    execution_time = time.time() - start_time
                    self.update_usage_stats(execution_time)
                    
                    logger.info(f"Google search completed for '{query}' - {len(formatted_results)} results in {execution_time:.3f}s")
                    
                    # Format results as text for simplified response
                    result_text = f"# Web Search Results for: {query}\n\n"
                    for i, result in enumerate(formatted_results, 1):
                        result_text += f"## {i}. {result['title']}\n"
                        result_text += f"**URL**: {result['url']}\n"
                        result_text += f"**Snippet**: {result['snippet']}\n\n"
                    
                    return result_text
                else:
                    # Fallback to placeholder if no results
                    logger.warning(f"No Google search results for query: {query}")
                    execution_time = time.time() - start_time
                    return f"# Web Search Results for: {query}\n\nNo search results found."
                    
            except ImportError:
                logger.error("WebSearchService not available, using placeholder")
                # Fallback to placeholder
                results = [
                    f"Search result for '{query}' - WebSearchService not configured",
                    "Please configure Google Search API credentials"
                ]
                
                execution_time = time.time() - start_time
                self.update_usage_stats(execution_time)
                
                return f"# Web Search Results for: {query}\n\nWebSearchService not configured. Please configure Google Search API credentials."
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Web search failed for query '{parameters.get('query', '')}': {str(e)}")
            return f"# Web Search Results\n\n**Error**: Web search failed: {str(e)}"
    
    def get_schema(self) -> Dict[str, Any]:
        """Get complete tool schema."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
            "category": self.category,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "examples": self.examples
        }
