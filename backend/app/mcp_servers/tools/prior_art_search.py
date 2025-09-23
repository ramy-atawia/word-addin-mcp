"""
Prior Art Search Tool

Fast-fail patent search tool that:
1. Generates PatentsView API queries using LLM
2. Executes API calls to get patent titles/numbers
3. Fetches patent claims
4. Generates comprehensive markdown report

Fails immediately on any error condition.
"""

import structlog
import time
from typing import Dict, Any
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
        """Execute prior art search with fast-fail behavior."""
        start_time = time.time()
        
        # Strict parameter validation
        query = parameters.get("query")
        if not query:
            raise ValueError("Query parameter is required")
        
        query = query.strip()
        if not query:
            raise ValueError("Query cannot be empty or whitespace only")
        
        if len(query) < 3:
            raise ValueError("Query must be at least 3 characters long")
        
        if len(query) > 1000:
            raise ValueError("Query cannot exceed 1000 characters")
        
        context = parameters.get("context")
        conversation_history = parameters.get("conversation_history")
        max_results = parameters.get("max_results", 20)
        
        if not isinstance(max_results, int):
            raise ValueError("max_results must be an integer")
        
        if max_results < 1 or max_results > 100:
            raise ValueError("max_results must be between 1 and 100")
        
        logger.info(f"Executing prior art search for query: {query}")
        
        # Execute the patent search (will raise exceptions on failure)
        search_result, generated_queries = await self.patent_service.search_patents(
            query=query,
            context=context,
            conversation_history=conversation_history,
            max_results=max_results
        )
        
        # Strict validation of search result
        if not search_result:
            raise ValueError("Patent service returned empty result")
        
        if not isinstance(search_result, dict):
            raise ValueError(f"Invalid search result type: {type(search_result)}")
        
        # Validate required fields in search result
        required_fields = ["query", "results_found", "patents", "report", "search_summary", "search_metadata"]
        for field in required_fields:
            if field not in search_result:
                raise ValueError(f"Search result missing required field: {field}")
        
        report = search_result.get("report")
        if not report:
            raise ValueError("Search result contains empty report")
        
        if not isinstance(report, str):
            raise ValueError(f"Report must be a string, got {type(report)}")
        
        report = report.strip()
        if not report:
            raise ValueError("Search result contains whitespace-only report")
        
        # Validate results count consistency
        results_found = search_result.get("results_found")
        patents = search_result.get("patents", [])
        
        if not isinstance(results_found, int):
            raise ValueError(f"results_found must be an integer, got {type(results_found)}")
        
        if results_found != len(patents):
            raise ValueError(f"Inconsistent results count: reported {results_found}, actual {len(patents)}")
        
        if results_found == 0:
            raise ValueError("No patents found for the given query")
        
        execution_time = time.time() - start_time
        self.update_usage_stats(execution_time)
        
        logger.info(f"Prior art search completed successfully for '{query}' - {results_found} results")
        
        return report