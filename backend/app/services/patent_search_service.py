"""
Simplified Patent Search Service

Flow:
1. LLM generates 5 PatentsView API queries with reasoning
2. Execute 5 API calls to get patent titles/numbers
3. Execute 5 API calls to get patent claims
4. LLM generates comprehensive markdown report
"""

import json
import asyncio
from typing import Dict, List, Any, Tuple, Optional
import httpx
import structlog
from app.core.config import settings
from app.services.llm_client import LLMClient
from app.utils.prompt_loader import load_prompt_template

logger = structlog.get_logger(__name__)


class PatentSearchService:
    """Simplified patent search service."""
    
    def __init__(self):
        self.llm_client = LLMClient(
            azure_openai_api_key=settings.azure_openai_api_key,
            azure_openai_endpoint=settings.azure_openai_endpoint,
            azure_openai_deployment=settings.azure_openai_deployment_name
        )
        self.patentsview_base_url = "https://search.patentsview.org/api/v1"
        self.api_key = settings.patentsview_api_key
    
    async def search_patents(
        self, 
        query: str, 
        context: Optional[str] = None, 
        conversation_history: Optional[str] = None,
        max_results: int = 20
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Main patent search flow.
        
        Returns:
            - search_result: Dict with patents, report, metadata
            - generated_queries: List of 5 search queries with reasoning
        """
        # Validate inputs
        if not query or not query.strip():
            raise ValueError("Query is required and cannot be empty")
        if max_results <= 0:
            raise ValueError("max_results must be greater than 0")
        if max_results > 100:
            raise ValueError("max_results cannot exceed 100")
        
        try:
            logger.info(f"Starting patent search for: {query}")
            
            # Step 1: Generate 5 PatentsView API queries
            search_queries = await self._generate_search_queries(
                query, context, conversation_history
            )
            logger.info(f"Generated {len(search_queries)} search queries")
            
            # Step 2: Execute 5 API calls for patent titles/numbers
            all_patents = []
            query_results = []  # Track results per query
            for i, search_query in enumerate(search_queries):
                # Handle both 'query' and 'search_query' fields
                query_field = "query" if "query" in search_query else "search_query"
                query_data = search_query[query_field]
                
                patents = await self._search_patents_api(query_data)
                all_patents.extend(patents)
                query_results.append({
                    "query_index": i + 1,
                    "query": query_data,
                    "reasoning": search_query.get("reasoning", "No reasoning provided"),
                    "results_count": len(patents)
                })
                logger.info(f"Query {i+1} returned {len(patents)} patents")
                if not patents:
                    logger.warning(f"Query {i+1} returned no patents - this may indicate an issue with the search query")

            # Validate that we found some patents
            if not all_patents:
                raise Exception("No patents found with any of the generated search queries. This may indicate an issue with the search strategy or PatentsView API.")
                
            # Remove duplicates and limit results
            unique_patents = self._deduplicate_patents(all_patents)
            top_patents = unique_patents[:max_results]
            logger.info(f"Total patents found: {len(all_patents)}, unique patents: {len(unique_patents)}, returning top {len(top_patents)}")
            
            # Debug: Check first few patents
            if all_patents:
                logger.info(f"Sample patent IDs: {[p.get('patent_id', 'NO_ID') for p in all_patents[:3]]}")
            
            # Step 3: Get claims for each patent
            patents_with_claims = await self._get_patent_claims(top_patents)
            
            # Step 4: Generate comprehensive markdown report
            report = await self._generate_report(
                query, context, conversation_history, 
                search_queries, patents_with_claims, query_results
            )
            
            # Prepare result
            search_result = {
                "query": query,
                "results_found": len(patents_with_claims),
                "patents": patents_with_claims,
                "search_summary": f"Found {len(patents_with_claims)} relevant patents using 5 search strategies",
                "search_metadata": {
                    "total_queries": len(search_queries),
                    "total_patents_found": len(all_patents),
                    "unique_patents": len(unique_patents)
                },
                "report": report
            }
            
            logger.info(f"Patent search completed: {len(patents_with_claims)} results")
            return search_result, search_queries
            
        except Exception as e:
            logger.error(f"Patent search failed: {str(e)}")
            raise
    
    async def _generate_search_queries(
        self, 
        query: str, 
        context: Optional[str] = None, 
        conversation_history: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate 5 PatentsView API queries using LLM with chain-of-thought reasoning."""
        
        # Validate required inputs
        if not query or not query.strip():
            raise ValueError("Query is required and cannot be empty")
        
        # Load the prompt template and format it with the input variables
        prompt = load_prompt_template(
            "patent_search_query_generation",
            query=query,
            context=context or "",
            conversation_history=conversation_history or "",
            max_results=20
        )
        
        try:
            response = self.llm_client.generate_text(
                prompt=prompt,
                system_message="You are a senior patent search expert with deep knowledge of PatentsView API. Use chain-of-thought reasoning to generate sophisticated search queries that balance exploration and exploitation.",
                max_tokens=6000
            )
            
            # Extract text from response
            if response.get("success"):
                response_text = response["text"]
            else:
                logger.error(f"LLM generation failed: {response.get('error', 'Unknown error')}")
                raise Exception(f"LLM generation failed: {response.get('error', 'Unknown error')}")
            
            # Clean response
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            # Try to fix common JSON issues
            if response_text.startswith('"') and response_text.endswith('"'):
                response_text = response_text[1:-1]  # Remove outer quotes
            if response_text.startswith("'") and response_text.endswith("'"):
                response_text = response_text[1:-1]  # Remove outer single quotes
            
            # Ensure response starts with { for JSON object
            if not response_text.strip().startswith('{'):
                logger.warning(f"LLM response doesn't start with {{: {response_text[:100]}")
                raise Exception("LLM response is not a JSON object")
            
            try:
                criteria = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed: {e}")
                logger.error(f"Raw response: {response_text}")
                logger.error(f"Response length: {len(response_text)}")
                raise Exception(f"Failed to parse LLM response as JSON: {e}. Response: {response_text[:200]}...")
            except Exception as e:
                logger.error(f"Unexpected error during JSON parsing: {e}")
                logger.error(f"Raw response: {response_text}")
                raise Exception(f"Unexpected error during JSON parsing: {e}. Response: {response_text[:200]}...")
            
            # Extract and validate search queries
            search_queries = criteria.get("search_queries", [])
            logger.info(f"Generated {len(search_queries)} search queries")
            
            # Validate search queries structure
            for i, q in enumerate(search_queries):
                if not isinstance(q, dict):
                    raise Exception(f"Search query {i+1} is not a dictionary: {q}")
                
                # Check for either 'query' or 'search_query' field
                query_field = None
                if "query" in q:
                    query_field = "query"
                elif "search_query" in q:
                    query_field = "search_query"
                else:
                    raise Exception(f"Search query {i+1} missing 'query' or 'search_query' field: {q}")
                
                if not isinstance(q[query_field], dict):
                    raise Exception(f"Search query {i+1} '{query_field}' field is not a dictionary: {q[query_field]}")
            
            # Validate we have 3-5 queries (flexible range)
            if len(search_queries) < 3 or len(search_queries) > 5:
                raise Exception(f"Expected 3-5 search queries, but got {len(search_queries)}")
            
            return search_queries
            
        except Exception as e:
            logger.error(f"LLM query generation failed: {e}")
            
            # Fallback: Generate simple queries if LLM fails
            logger.warning("Falling back to simple query generation")
            
            # Split query into words for broader search
            query_words = query.split()
            if len(query_words) > 1:
                # Multi-word query - create broader searches
                fallback_queries = [
                    {
                        "query": {"patent_abstract": query},
                        "reasoning": f"Simple abstract search for: {query}",
                        "strategy": "fallback"
                    },
                    {
                        "query": {"patent_title": query},
                        "reasoning": f"Simple title search for: {query}",
                        "strategy": "fallback"
                    },
                    {
                        "query": {"_or": [{"patent_abstract": query}, {"patent_title": query}]},
                        "reasoning": f"Combined abstract and title search for: {query}",
                        "strategy": "fallback"
                    },
                    {
                        "query": {"patent_abstract": query_words[0]},
                        "reasoning": f"First word search: {query_words[0]}",
                        "strategy": "fallback"
                    },
                    {
                        "query": {"patent_abstract": query_words[-1]},
                        "reasoning": f"Last word search: {query_words[-1]}",
                        "strategy": "fallback"
                    }
                ]
            else:
                # Single word query
                fallback_queries = [
                    {
                        "query": {"patent_abstract": query},
                        "reasoning": f"Abstract search for: {query}",
                        "strategy": "fallback"
                    },
                    {
                        "query": {"patent_title": query},
                        "reasoning": f"Title search for: {query}",
                        "strategy": "fallback"
                    },
                    {
                        "query": {"_or": [{"patent_abstract": query}, {"patent_title": query}]},
                        "reasoning": f"Combined search for: {query}",
                        "strategy": "fallback"
                    }
                ]
            
            return fallback_queries
    
    async def _search_patents_api(self, search_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute PatentsView API call for patent titles/numbers."""
        
        url = f"{self.patentsview_base_url}/patent/"
        
        payload = {
            "q": search_query,
            "f": [
                "patent_id", "patent_title", "patent_abstract", 
                "patent_date", "patent_year", "inventors", "assignees"
            ],
            "s": [{"patent_date": "desc"}],
            "o": {"size": 20}
        }
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        
        try:
            # Debug: Log the API request
            logger.info(f"PatentsView API request: {json.dumps(payload, indent=2)}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("error", False):
                    logger.error(f"PatentsView API error: {data}")
                    raise Exception(f"PatentsView API returned error: {data}")
                
                patents = data.get("patents", [])
                logger.info(f"PatentsView API returned {len(patents)} patents")
                
                # Debug: Log sample patents if any found
                if patents:
                    logger.info(f"Sample patent: {json.dumps(patents[0], indent=2)[:500]}...")
                else:
                    logger.warning(f"No patents found for query: {json.dumps(payload, indent=2)}")
                
                return patents
                
        except Exception as e:
            logger.error(f"PatentsView API call failed: {e}")
            raise Exception(f"PatentsView API call failed: {e}")
    
    async def _get_patent_claims(self, patents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get claims for each patent."""
        
        patents_with_claims = []
        
        for patent in patents:
            patent_id = patent.get("patent_id")
            if not patent_id:
                raise ValueError(f"Patent missing required patent_id: {patent}")
            
            claims = await self._fetch_patent_claims(patent_id)
            
            patent_with_claims = patent.copy()
            patent_with_claims["claims"] = claims
            patents_with_claims.append(patent_with_claims)
        
        return patents_with_claims
    
    async def _fetch_patent_claims(self, patent_id: str) -> List[Dict[str, Any]]:
        """Fetch claims for a specific patent."""
        
        url = f"{self.patentsview_base_url}/g_claim/"
        
        payload = {
            "f": [
                "patent_id", "claim_sequence", "claim_text",
                "claim_number", "claim_dependent", "exemplary"
            ],
            "o": {"size": 100},
            "q": {"_and": [{"patent_id": patent_id}]},
            "s": [
                {"patent_id": "asc"}, 
                {"claim_sequence": "asc"}
            ]
        }
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                claims_data = data.get("g_claims", [])
                return self._parse_claims(claims_data)
                
        except Exception as e:
            logger.error(f"Failed to fetch claims for patent {patent_id}: {e}")
            raise Exception(f"Failed to fetch claims for patent {patent_id}: {e}")
    
    def _parse_claims(self, claims_data: List[Dict]) -> List[Dict[str, Any]]:
        """Parse claims data into structured format."""
        claims = []
        
        for claim_info in claims_data:
            try:
                claim_text = claim_info.get("claim_text", "")
                if not claim_text:
                    continue
                
                claim_sequence = claim_info.get("claim_sequence", 0)
                claim_number = claim_info.get("claim_number", "")
                claim_dependent = claim_info.get("claim_dependent", "")
                
                if not claim_number:
                    claim_number = str(claim_sequence + 1)
                
                claim_type = "dependent" if claim_dependent else "independent"
                
                claim = {
                    "claim_number": claim_number,
                    "claim_text": claim_text,
                    "claim_type": claim_type,
                    "dependency": claim_dependent if claim_dependent else None,
                    "is_exemplary": bool(claim_info.get("exemplary", ""))
                }
                
                claims.append(claim)
                
            except Exception as e:
                logger.warning(f"Error parsing claim: {e}")
                continue
        
        return claims
    
    async def _generate_report(
        self,
        query: str,
        context: str,
        conversation_history: str,
        search_queries: List[Dict[str, Any]],
        patents: List[Dict[str, Any]],
        query_results: List[Dict[str, Any]]
    ) -> str:
        """Generate comprehensive markdown report using LLM."""
        
        # Prepare patent data for LLM with validation
        patent_summaries = []
        for patent in patents:
            # Validate required fields
            if not patent.get("patent_id"):
                raise ValueError(f"Patent missing required patent_id: {patent}")
            if not patent.get("patent_title"):
                raise ValueError(f"Patent missing required patent_title: {patent}")
            
            summary = {
                "patent_number": patent["patent_id"],  # PatentsView uses patent_id as the patent number
                "title": patent["patent_title"],
                "date": patent.get("patent_date", "Unknown"),
                "inventor": patent.get("inventors", [{}])[0].get("inventor_name_first", "") + " " + patent.get("inventors", [{}])[0].get("inventor_name_last", "") if patent.get("inventors") else "Unknown",
                "assignee": patent.get("assignees", [{}])[0].get("assignee_organization") if patent.get("assignees") else "Unknown",
                "abstract": patent.get("patent_abstract", "No abstract available"),
                "claims_count": len(patent.get("claims", []))
            }
            patent_summaries.append(summary)
        
        prompt = f"""
Generate a prior art search report for: {query}

**Search Queries** ({len(search_queries)}):
{json.dumps(search_queries, indent=2)}

**Patents Found** ({len(patent_summaries)}):
{json.dumps(patent_summaries, indent=2)}

**CRITICAL**: Use the actual patent data provided. Do NOT generate generic reports.

## REPORT STRUCTURE:

# Prior Art Search Report: {query}

## 1. Executive Summary
- **Query**: {query}
- **Results**: Found {len(patent_summaries)} relevant patents
- **Search Strategy**: {len(search_queries)} PatentsView API queries

## 2. Search Strategy Analysis
{chr(10).join([f"""
### Query {i+1}:
**Query**: {json.dumps(qr["query"]) if i < len(query_results) else "N/A"}
**Reasoning**: {qr["reasoning"] if i < len(query_results) else "N/A"}
**Results**: {qr["results_count"] if i < len(query_results) else 0}
""" for i, qr in enumerate(query_results)])}

## 3. Key Findings
- **Total Patents**: {len(patent_summaries)}
- **Top Patents**: {chr(10).join([f"• {p['patent_number']}: {p['title'][:60]}..." for p in patent_summaries[:5]])}

## 4. Detailed Patent Analysis
{chr(10).join([f"""
### Patent {i+1}: {p['patent_number']}
**Title**: {p['title']}
**Date**: {p['date']}
**Abstract**: {p['abstract'][:100]}...
**Inventors**: {p['inventor']}
**Assignee**: {p['assignee']}
**Relevance**: [Brief analysis]
""" for i, p in enumerate(patent_summaries)])}

## 5. Risk Assessment & Recommendations
- **Patent Conflicts**: [Identify potential conflicts]
- **Recommendations**: [Based on findings]

Generate the complete report using the provided patent data.
"""
        
        try:
            # Debug: Log the prompt being sent to LLM
            logger.info(f"Report generation prompt length: {len(prompt)} characters")
            logger.info(f"Report generation prompt preview: {prompt[:500]}...")
            
            response = self.llm_client.generate_text(
                prompt=prompt,
                system_message="You are a senior patent attorney. You MUST follow the exact report structure provided and include ALL required elements, especially the 5 search queries with their reasoning.",
                max_tokens=16000
            )
            
            if response.get("success"):
                return response["text"]
            else:
                raise Exception(f"Report generation failed: {response.get('error', 'Unknown error')}")
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return f"# Prior Art Search Report\n\n**Query**: {query}\n\n**Error**: Failed to generate report - {str(e)}"
    
    def _deduplicate_patents(self, patents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate patents based on patent ID."""
        seen = set()
        unique_patents = []
        
        for patent in patents:
            patent_id = patent.get("patent_id")
            if patent_id and patent_id not in seen:
                seen.add(patent_id)
                unique_patents.append(patent)
        
        return unique_patents
    