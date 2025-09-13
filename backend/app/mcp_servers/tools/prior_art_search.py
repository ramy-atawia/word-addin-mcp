"""
Prior Art Search Tool

Simplified patent search tool that:
1. Generates 5 PatentsView API queries using LLM
2. Executes API calls to get patent titles/numbers
3. Fetches patent claims
4. Generates comprehensive markdown report
"""

import structlog
import time
from typing import Dict, Any, List
from .base import BaseInternalTool
from app.services.patent_search_service import PatentSearchService

logger = structlog.get_logger(__name__)


class PriorArtSearchTool(BaseInternalTool):
    """Prior art search tool for finding relevant patents and analyzing patent landscapes."""
    
    def __init__(self):
        super().__init__(
            name="prior_art_search_tool",
            description="Search for prior art patents using PatentsView API with comprehensive markdown report",
            version="2.0.0"
        )
        
        # Tool schema definition
        self.input_schema = {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query describing the invention or technology",
                    "minLength": 3,
                    "maxLength": 1000
                },
                "context": {
                    "type": "string",
                    "description": "Context from Word document"
                },
                "conversation_history": {
                    "type": "string",
                    "description": "Conversation history context"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of patents to return",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100
                }
            },
            "required": ["query"]
        }
        
        self.output_schema = {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "results_found": {"type": "integer"},
                "patents": {
                    "type": "array",
                    "items": {"type": "object"}
                },
                "search_summary": {"type": "string"},
                "search_metadata": {"type": "object"},
                "report": {"type": "string"},
                "generated_search_criteria": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "search_query": {"type": "object"},
                            "reasoning": {"type": "string"}
                        }
                    }
                }
            }
        }
        
        self.examples = [
            {
                "name": "Machine Learning Search",
                "description": "Search for machine learning patents",
                "input": {
                    "query": "machine learning optimization",
                    "context": "Document discusses ML optimization techniques",
                    "max_results": 10
                }
            },
            {
                "name": "Blockchain Smart Contracts",
                "description": "Search for blockchain and smart contract patents",
                "input": {
                    "query": "blockchain smart contracts",
                    "context": "Patent application for decentralized contract execution",
                    "conversation_history": "User mentioned Ethereum and Solidity",
                    "max_results": 15
                }
            }
        ]
        
        self.patent_service = PatentSearchService()
    
    async def execute(self, parameters: Dict[str, Any]) -> str:
        """Execute prior art search with comprehensive report generation."""
        start_time = time.time()
        
        query = parameters.get("query", "")
        context = parameters.get("context")
        conversation_history = parameters.get("conversation_history")
        max_results = parameters.get("max_results", 20)
        
        logger.info(f"Executing prior art search for query: {query}")
        
        try:
            # Execute the patent search
            search_result, generated_queries = await self.patent_service.search_patents(
                query=query,
                context=context,
                conversation_history=conversation_history,
                max_results=max_results
            )
            
            logger.info(f"Prior art search completed for '{query}' - {search_result['results_found']} results")
            
            execution_time = time.time() - start_time
            self.update_usage_stats(execution_time)
            
            # Return just the markdown report
            return search_result["report"]
            
        except ValueError as e:
            execution_time = time.time() - start_time
            logger.error(f"Prior art search failed with specific error for '{query}': {str(e)}")
            # Return specific error as markdown
            return f"# Prior Art Search Report\n\n**Query**: {query}\n\n**Error**: {str(e)}\n\n**Suggestion**: Please check your query and try again, or contact support if the issue persists."
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Prior art search failed with unexpected error for '{query}': {str(e)}")
            # Return generic error as markdown
            return f"# Prior Art Search Report\n\n**Query**: {query}\n\n**Error**: An unexpected error occurred during the search. Please try again.\n\n**Technical Details**: {str(e)}"