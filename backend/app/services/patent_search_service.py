"""
Simplified Patent Search Service

Core Flow:
1. Generate search queries (with fallback)
2. Search patents via PatentsView API
3. Fetch patent claims
4. Generate markdown report
"""

import json
import asyncio
from typing import Dict, List, Any, Tuple, Optional
import httpx
import structlog
from app.core.config import settings
from app.utils.prompt_loader import load_prompt_template

logger = structlog.get_logger(__name__)


class PatentSearchService:
    """Simplified patent search service with core functionality."""
    
    def __init__(self):
        from app.services.llm_client import LLMClient
        self.llm_client = LLMClient(
            azure_openai_api_key=settings.azure_openai_api_key,
            azure_openai_endpoint=settings.azure_openai_endpoint,
            azure_openai_deployment=settings.azure_openai_deployment
        )
        self.api_key = settings.patentsview_api_key
        self.base_url = "https://search.patentsview.org/api/v1"
    
    async def search_patents(
        self, 
        query: str, 
        context: Optional[str] = None, 
        conversation_history: Optional[str] = None,
        max_results: int = 20
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Main patent search function.
        
        Args:
            query: Search query string
            context: Optional context (kept for compatibility)
            conversation_history: Optional conversation history (kept for compatibility)
            max_results: Maximum number of patents to return
            
        Returns:
            Tuple of (search_result_dict, search_queries_list)
        """
        if not query.strip():
            raise ValueError("Query cannot be empty")
        
        try:
            logger.info(f"Starting patent search for: {query}")
            
            # Step 1: Generate search queries
            logger.info("Step 1: Generating search queries...")
            search_queries = await self._generate_queries(query)
            logger.info(f"Step 1 completed: Generated {len(search_queries)} queries")
            
            # Step 2: Search for patents
            logger.info("Step 2: Searching for patents...")
            all_patents = await self._search_all_queries(search_queries)
            logger.info(f"Step 2 completed: Found {len(all_patents)} total patents")
            
            # Step 3: Deduplicate and limit results
            logger.info("Step 3: Deduplicating patents...")
            unique_patents = self._deduplicate(all_patents)[:max_results]
            logger.info(f"Step 3 completed: {len(unique_patents)} unique patents")
            
            # Step 4: Get claims for each patent
            logger.info("Step 4: Fetching patent claims...")
            patents_with_claims = await self._add_claims(unique_patents)
            logger.info(f"Step 4 completed: Added claims to {len(patents_with_claims)} patents")
            
            # Step 5: Generate report
            logger.info("Step 5: Generating report...")
            report = await self._generate_report(query, search_queries, patents_with_claims)
            logger.info(f"Step 5 completed: Generated report of {len(report)} characters")
            
            search_result = {
                "query": query,
                "results_found": len(patents_with_claims),
                "patents": patents_with_claims,
                "report": report,
                "search_summary": f"Found {len(patents_with_claims)} relevant patents using {len(search_queries)} search strategies",
                "search_metadata": {
                    "total_queries": len(search_queries),
                    "total_patents_found": len(all_patents),
                    "unique_patents": len(unique_patents)
                }
            }
            
            return search_result, search_queries
            
        except ValueError as e:
            # Re-raise ValueError with specific error messages
            logger.error(f"Patent search failed with specific error: {e}")
            raise
        except Exception as e:
            logger.error(f"Patent search failed with unexpected error: {e}")
            raise ValueError(f"Patent search failed: {str(e)}")
    
    async def _generate_queries(self, query: str) -> List[Dict[str, Any]]:
        """Generate search queries using LLM with prompt template."""
        try:
            # Load the prompt template with parameters
            logger.info(f"Loading prompt template for query: {query}")
            prompt = load_prompt_template("patent_search_query_generation", 
                                        query=query,
                                        context="",
                                        conversation_history="")
            logger.info(f"Prompt loaded successfully, length: {len(prompt)}")
            
            response = self.llm_client.generate_text(
                prompt=prompt,
                system_message="You are a patent search expert. Generate diverse, effective search queries.",
                max_tokens=1500,
                temperature=0.3
            )
            
            logger.info(f"LLM response: {response}")
            
            if not response.get("success"):
                raise Exception(f"LLM failed: {response.get('error')}")
            
            # Parse LLM response
            text = response["text"].strip()
            logger.info(f"LLM response text: {text[:500]}...")
            
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
            
            logger.info(f"Cleaned text for JSON parsing: {text[:500]}...")
            
            data = json.loads(text)
            queries = data.get("search_queries", [])
            
            if len(queries) < 3:
                raise Exception(f"Too few queries generated: {len(queries)}")
            
            return queries
            
        except json.JSONDecodeError as e:
            logger.error(f"LLM returned invalid JSON: {e}")
            raise ValueError(f"Failed to parse LLM response as JSON. LLM may have returned invalid format: {e}")
        except KeyError as e:
            logger.error(f"LLM response missing required field: {e}")
            raise ValueError(f"LLM response missing required field '{e}'. Please try again.")
        except Exception as e:
            logger.error(f"LLM query generation failed: {e}")
            raise ValueError(f"Failed to generate search queries: {e}")
    
    
    async def _search_all_queries(self, search_queries: List[Dict]) -> List[Dict[str, Any]]:
        """Execute all search queries and collect results."""
        
        all_patents = []
        
        for i, search_query in enumerate(search_queries):
            try:
                query_data = search_query.get("search_query", {})
                patents = await self._search_patents_api(query_data)
                all_patents.extend(patents)
                logger.info(f"Query {i+1} returned {len(patents)} patents")
                
            except Exception as e:
                logger.warning(f"Query {i+1} failed: {e}")
                continue
        
        return all_patents
    
    async def _search_patents_api(self, search_query: Dict) -> List[Dict[str, Any]]:
        """Call PatentsView API to search patents."""
        
        url = f"{self.base_url}/patent/"
        
        payload = {
            "q": search_query,
            "f": ["patent_id", "patent_title", "patent_abstract", "patent_date", 
                  "inventors", "assignees"],
            "s": [{"patent_date": "desc"}],
            "o": {"size": 20}
        }
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        
        logger.info(f"API call - URL: {url}")
        logger.info(f"API call - Payload: {payload}")
        logger.info(f"API call - Headers: {headers}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                logger.info(f"API response status: {response.status_code}")
                logger.info(f"API response text: {response.text[:500]}")
                
                # Handle specific HTTP status codes
                if response.status_code == 400:
                    raise ValueError(f"Bad Request: Invalid search query. API returned: {response.text}")
                elif response.status_code == 401:
                    raise ValueError(f"Unauthorized: Invalid API key. Please check your PatentsView API credentials.")
                elif response.status_code == 403:
                    raise ValueError(f"Forbidden: API access denied. Check your API key permissions.")
                elif response.status_code == 429:
                    raise ValueError(f"Rate Limited: Too many requests. Please wait before trying again.")
                elif response.status_code == 500:
                    raise ValueError(f"Server Error: PatentsView API is experiencing issues. Please try again later.")
                elif response.status_code == 503:
                    raise ValueError(f"Service Unavailable: PatentsView API is temporarily down. Please try again later.")
                elif not response.is_success:
                    raise ValueError(f"API Error {response.status_code}: {response.text}")
                
                data = response.json()
                
                # Handle API-specific errors
                if data.get("error"):
                    error_msg = data.get("error", "Unknown API error")
                    if isinstance(error_msg, dict):
                        error_msg = error_msg.get("message", str(error_msg))
                    raise ValueError(f"PatentsView API Error: {error_msg}")
                
                return data.get("patents", [])
                
        except httpx.TimeoutException:
            raise ValueError("Request Timeout: PatentsView API took too long to respond. Please try again.")
        except httpx.ConnectError:
            raise ValueError("Connection Error: Cannot connect to PatentsView API. Please check your internet connection.")
        except httpx.HTTPError as e:
            raise ValueError(f"HTTP Error: {str(e)}")
        except json.JSONDecodeError:
            raise ValueError("Invalid Response: PatentsView API returned invalid JSON. Please try again.")
        except Exception as e:
            raise ValueError(f"Unexpected Error: {str(e)}")
    
    def _deduplicate(self, patents: List[Dict]) -> List[Dict]:
        """Remove duplicate patents by ID."""
        
        seen = set()
        unique = []
        
        for patent in patents:
            patent_id = patent.get("patent_id")
            if patent_id and patent_id not in seen:
                seen.add(patent_id)
                unique.append(patent)
        
        return unique
    
    async def _add_claims(self, patents: List[Dict]) -> List[Dict]:
        """Add claims data to each patent."""
        
        patents_with_claims = []
        
        for patent in patents:
            patent_id = patent.get("patent_id")
            try:
                claims = await self._fetch_claims(patent_id)
                patent["claims"] = claims
                patents_with_claims.append(patent)
                
            except Exception as e:
                logger.warning(f"Failed to fetch claims for {patent_id}: {e}")
                patent["claims"] = []
                patents_with_claims.append(patent)
        
        return patents_with_claims
    
    async def _fetch_claims(self, patent_id: str) -> List[Dict]:
        """Fetch claims for a specific patent."""
        
        url = f"{self.base_url}/g_claim/"
        
        payload = {
            "q": {"patent_id": patent_id},
            "f": ["claim_sequence", "claim_text", "claim_number", "claim_dependent"],
            "o": {"size": 50},
            "s": [{"claim_sequence": "asc"}]
        }
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                # Handle specific HTTP status codes
                if response.status_code == 400:
                    raise ValueError(f"Bad Request: Invalid patent ID '{patent_id}'. API returned: {response.text}")
                elif response.status_code == 401:
                    raise ValueError(f"Unauthorized: Invalid API key for claims API. Please check your PatentsView API credentials.")
                elif response.status_code == 403:
                    raise ValueError(f"Forbidden: API access denied for claims. Check your API key permissions.")
                elif response.status_code == 404:
                    raise ValueError(f"Not Found: No claims found for patent ID '{patent_id}'.")
                elif response.status_code == 429:
                    raise ValueError(f"Rate Limited: Too many claims requests. Please wait before trying again.")
                elif response.status_code == 500:
                    raise ValueError(f"Server Error: PatentsView claims API is experiencing issues. Please try again later.")
                elif response.status_code == 503:
                    raise ValueError(f"Service Unavailable: PatentsView claims API is temporarily down. Please try again later.")
                elif not response.is_success:
                    raise ValueError(f"Claims API Error {response.status_code}: {response.text}")
                
                data = response.json()
                
                # Handle API-specific errors
                if data.get("error"):
                    error_msg = data.get("error", "Unknown API error")
                    if isinstance(error_msg, dict):
                        error_msg = error_msg.get("message", str(error_msg))
                    raise ValueError(f"PatentsView Claims API Error: {error_msg}")
                
                claims_data = data.get("g_claims", [])
                
                # Parse claims into simple format
                claims = []
                for claim in claims_data:
                    claims.append({
                        "number": claim.get("claim_number", ""),
                        "text": claim.get("claim_text", ""),
                        "type": "dependent" if claim.get("claim_dependent") else "independent"
                    })
                
                return claims
                
        except httpx.TimeoutException:
            raise ValueError(f"Request Timeout: Claims API took too long to respond for patent '{patent_id}'. Please try again.")
        except httpx.ConnectError:
            raise ValueError(f"Connection Error: Cannot connect to PatentsView claims API for patent '{patent_id}'. Please check your internet connection.")
        except httpx.HTTPError as e:
            raise ValueError(f"HTTP Error for patent '{patent_id}': {str(e)}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid Response: PatentsView claims API returned invalid JSON for patent '{patent_id}'. Please try again.")
        except Exception as e:
            raise ValueError(f"Unexpected Error fetching claims for patent '{patent_id}': {str(e)}")
    
    async def _generate_report(self, query: str, search_queries: List[Dict], 
                             patents: List[Dict]) -> str:
        """Generate markdown report using LLM with prompt template."""
        
        # Prepare data for report
        patent_summaries = []
        for patent in patents:
            patent_summaries.append({
                "id": patent.get("patent_id", "Unknown"),
                "title": patent.get("patent_title", "No title"),
                "date": patent.get("patent_date", "Unknown"),
                "abstract": (patent.get("patent_abstract", "")[:200] + "...") if patent.get("patent_abstract") else "No abstract",
                "claims_count": len(patent.get("claims", [])),
                "inventor": self._extract_inventor(patent.get("inventors", [])),
                "assignee": self._extract_assignee(patent.get("assignees", []))
            })
        
        try:
            # Load the system prompt template
            system_prompt = load_prompt_template("prior_art_search_system")
            
            # Load the user prompt template with parameters
            user_prompt = load_prompt_template("prior_art_search_comprehensive",
                                              user_query=query,
                                              conversation_context=f"Search Queries Used:\n{json.dumps(search_queries, indent=2)}\n\nPatents Found:\n{json.dumps(patent_summaries, indent=2)}",
                                              document_reference="Patent Search Results")
            
            response = self.llm_client.generate_text(
                prompt=user_prompt,
                system_message=system_prompt,
                max_tokens=8000,
                temperature=0.3
            )
            
            if response.get("success"):
                return response["text"]
            else:
                raise Exception(f"LLM failed: {response.get('error')}")
                
        except json.JSONDecodeError as e:
            logger.error(f"LLM returned invalid JSON for report generation: {e}")
            raise ValueError(f"Failed to parse LLM response as JSON for report generation: {e}")
        except KeyError as e:
            logger.error(f"LLM response missing required field for report: {e}")
            raise ValueError(f"LLM response missing required field '{e}' for report generation. Please try again.")
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise ValueError(f"Failed to generate report: {e}")
    
    
    def _extract_inventor(self, inventors: List[Dict]) -> str:
        """Extract first inventor name."""
        if not inventors:
            return "Unknown"
        
        first = inventors[0]
        first_name = first.get("inventor_name_first", "")
        last_name = first.get("inventor_name_last", "")
        return f"{first_name} {last_name}".strip() or "Unknown"
    
    def _extract_assignee(self, assignees: List[Dict]) -> str:
        """Extract first assignee organization."""
        if not assignees:
            return "Unknown"
        
        return assignees[0].get("assignee_organization", "Unknown")
    
    def _get_current_date(self) -> str:
        """Get current date string."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")