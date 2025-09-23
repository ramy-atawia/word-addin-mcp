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
            logger.info(f"🔍 Starting patent search for: {query}")
            print(f"🔍 DEBUG: Starting patent search for query: '{query}' with max_results: {max_results}")
            
            # Step 1: Generate search queries
            logger.info("Step 1: Generating search queries...")
            print("🔍 DEBUG: Step 1 - Generating search queries...")
            search_queries = await self._generate_queries(query)
            logger.info(f"Step 1 completed: Generated {len(search_queries)} queries")
            print(f"🔍 DEBUG: Step 1 completed - Generated {len(search_queries)} queries: {search_queries}")
            
            # Step 2: Search for patents
            logger.info("Step 2: Searching for patents...")
            print("🔍 DEBUG: Step 2 - Searching for patents...")
            all_patents, query_results = await self._search_all_queries(search_queries)
            logger.info(f"Step 2 completed: Found {len(all_patents)} total patents")
            print(f"🔍 DEBUG: Step 2 completed - Found {len(all_patents)} total patents")
            
            # Step 3: Deduplicate and limit results
            logger.info("Step 3: Deduplicating patents...")
            print("🔍 DEBUG: Step 3 - Deduplicating patents...")
            unique_patents = self._deduplicate(all_patents)[:max_results]
            logger.info(f"Step 3 completed: {len(unique_patents)} unique patents")
            print(f"🔍 DEBUG: Step 3 completed - {len(unique_patents)} unique patents after deduplication")
            
            # Step 4: Get claims for each patent
            logger.info("Step 4: Fetching patent claims...")
            print("🔍 DEBUG: Step 4 - Fetching patent claims...")
            patents_with_claims = await self._add_claims(unique_patents)
            logger.info(f"Step 4 completed: Added claims to {len(patents_with_claims)} patents")
            print(f"🔍 DEBUG: Step 4 completed - Added claims to {len(patents_with_claims)} patents")
            
            # Step 5: Summarize claims using LLM
            logger.info("Step 5: Summarizing patent claims...")
            print("🔍 DEBUG: Step 5 - Summarizing patent claims...")
            found_claims_summary = await self._summarize_claims(patents_with_claims)
            logger.info(f"Step 5 completed: Generated claims summary of {len(found_claims_summary)} characters")
            print(f"🔍 DEBUG: Step 5 completed - Generated claims summary of {len(found_claims_summary)} characters")
            
            # Step 6: Generate report
            logger.info("Step 6: Generating report...")
            print("🔍 DEBUG: Step 6 - Generating report...")
            report = await self._generate_report(query, query_results, patents_with_claims, found_claims_summary)
            logger.info(f"Step 6 completed: Generated report of {len(report)} characters")
            print(f"🔍 DEBUG: Step 6 completed - Generated report of {len(report)} characters")
            
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
                system_message="You are a patent search expert. Think like a domain expert and analyze query specificity iteratively.",
                max_tokens=4000
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
    
    
    async def _search_all_queries(self, search_queries: List[Dict]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Execute all search queries and collect results."""
        
        all_patents = []
        query_results = []
        
        for i, search_query in enumerate(search_queries):
            try:
                query_data = search_query.get("search_query", {})
                patents = await self._search_patents_api(query_data)
                all_patents.extend(patents)
                
                # Track query results with counts
                query_text = search_query.get("reasoning", f"Query {i+1}")
                query_results.append({
                    "query_text": query_text,
                    "result_count": len(patents)
                })
                
                logger.info(f"Query {i+1} returned {len(patents)} patents")
                
            except Exception as e:
                logger.warning(f"Query {i+1} failed: {e}")
                query_results.append({
                    "query_text": f"Query {i+1} (failed)",
                    "result_count": 0
                })
                continue
        
        return all_patents, query_results
    
    async def _search_patents_api(self, search_query: Dict) -> List[Dict[str, Any]]:
        """Call PatentsView API to search patents."""
        
        url = f"{self.base_url}/patent/"
        
        payload = {
            "q": search_query,
            "f": ["patent_id", "patent_title", "patent_abstract", "patent_date", 
                  "inventors", "assignees", "cpc_current"],
            "s": [{"patent_date": "desc"}],
            "o": {"size": 10}  # Reduced from 20 to 10 for faster processing
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
    
    async def _summarize_claims(self, patents: List[Dict]) -> str:
        """Summarize claims for top patents using LLM with performance optimization."""
        # Performance optimization: Only analyze top 5 most relevant patents
        top_patents = patents[:5] if len(patents) > 5 else patents
        
        claims_summaries = []
        
        # Process patents in parallel for better performance
        import asyncio
        
        async def process_patent_claims(patent):
            patent_id = patent.get("patent_id", "Unknown")
            patent_title = patent.get("patent_title", "No title")
            claims = patent.get("claims", [])
            
            if not claims:
                return f"**Patent {patent_id}: {patent_title}**\n- Claims: Not available\n"
            
            # Prepare claims text for LLM analysis (limit to first 3 claims for performance)
            claims_text = []
            independent_claims = []
            dependent_claims = []
            
            # Limit to first 3 claims to reduce token usage
            limited_claims = claims[:3]
            
            for claim in limited_claims:
                claim_number = claim.get("number", "")
                claim_text = claim.get("text", "")
                claim_type = claim.get("type", "unknown")
                
                if claim_text and claim_number and len(claim_text.strip()) > 10:
                    # Truncate very long claims to reduce token usage
                    truncated_text = claim_text[:500] + "..." if len(claim_text) > 500 else claim_text
                    full_claim = f"Claim {claim_number} ({claim_type}): {truncated_text}"
                    claims_text.append(full_claim)
                    
                    if claim_type == "independent":
                        independent_claims.append(full_claim)
                    else:
                        dependent_claims.append(full_claim)
            
            if not claims_text:
                return f"**Patent {patent_id}: {patent_title}**\n- Claims: No valid claim text found\n"
            
            # Simplified prompt for faster processing
            claims_prompt = f"""
Analyze the patent claims for patent {patent_id} titled "{patent_title}".

**CLAIMS TO ANALYZE:**
{chr(10).join(claims_text)}

**ANALYSIS REQUIREMENTS:**
1. **Technical Summary**: 2-3 sentence summary of the main invention
2. **Key Technical Features**: List 3-4 key technical elements
3. **Claim Structure**: Identify independent vs dependent claims
4. **Technical Scope**: Brief scope and limitations

Format as concise markdown.
"""
            
            try:
                # Reduced token usage for faster processing
                response = self.llm_client.generate_text(
                    prompt=claims_prompt,
                    max_tokens=300  # Further reduced from 600 to 300 for faster processing
                )
                
                if response.get("success"):
                    summary = response["text"]
                    return f"**Patent {patent_id}: {patent_title}**\n{summary}\n"
                else:
                    # Fallback: basic claims listing
                    return (f"**Patent {patent_id}: {patent_title}**\n" + 
                           f"- Claims: {len(claims)} claims found\n" +
                           f"- Independent Claims: {len([c for c in claims if c.get('type') == 'independent'])}\n" +
                           f"- Dependent Claims: {len([c for c in claims if c.get('type') == 'dependent'])}\n")
                    
            except Exception as e:
                logger.warning(f"Failed to summarize claims for patent {patent_id}: {e}")
                # Fallback: basic claims listing
                return (f"**Patent {patent_id}: {patent_title}**\n" + 
                       f"- Claims: {len(claims)} claims found\n" +
                       f"- Independent Claims: {len([c for c in claims if c.get('type') == 'independent'])}\n" +
                       f"- Dependent Claims: {len([c for c in claims if c.get('type') == 'dependent'])}\n")
        
        # Process patents in parallel
        tasks = [process_patent_claims(patent) for patent in top_patents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle results and exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                patent_id = top_patents[i].get("patent_id", "Unknown")
                claims_summaries.append(f"**Patent {patent_id}**: Error processing claims - {str(result)}\n")
            else:
                claims_summaries.append(result)
        
        # Add summary for remaining patents if any
        if len(patents) > 5:
            remaining_count = len(patents) - 5
            claims_summaries.append(f"**Additional Patents**: {remaining_count} more patents found with claims data (not analyzed for performance)\n")
        
        # Combine all summaries into a markdown string
        found_claims_summary = "\n".join(claims_summaries)
        
        logger.info(f"Generated claims summary for {len(top_patents)} patents (optimized for performance)")
        return found_claims_summary
    
    async def _fetch_claims(self, patent_id: str) -> List[Dict]:
        """Fetch claims for a specific patent."""
        
        url = f"{self.base_url}/g_claim/"
        
        payload = {
            "q": {"patent_id": patent_id},
            "f": ["claim_sequence", "claim_text", "claim_number", "claim_dependent"],
            "o": {"size": 100},  # Increased from 50 to 100 for more claims
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
                
                if not claims_data:
                    logger.warning(f"No claims data found for patent {patent_id}")
                    return []
                
                # Parse claims into simple format with validation
                claims = []
                for claim in claims_data:
                    claim_text = claim.get("claim_text", "")
                    claim_number = claim.get("claim_number", "")
                    
                    # Validate that we have meaningful claim text
                    if not claim_text or len(claim_text.strip()) < 10:
                        logger.warning(f"Invalid or truncated claim text for patent {patent_id}, claim {claim_number}")
                        continue
                    
                    claims.append({
                        "number": claim_number,
                        "text": claim_text.strip(),  # Ensure clean text
                        "type": "dependent" if claim.get("claim_dependent") else "independent",
                        "sequence": claim.get("claim_sequence", 0)
                    })
                
                logger.info(f"Successfully fetched {len(claims)} claims for patent {patent_id}")
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
    
    async def _generate_report(self, query: str, query_results: List[Dict], 
                             patents: List[Dict], found_claims_summary: str = "") -> str:
        """Generate markdown report using LLM with prompt template."""
        
        # Prepare data for report with enhanced metadata
        patent_summaries = []
        for i, patent in enumerate(patents):
            # Extract claims text for analysis
            claims_text = []
            for claim in patent.get("claims", []):
                claim_text = claim.get("text", "")  # Fixed: was "claim_text"
                claim_number = claim.get("number", "")  # Fixed: was "claim_number"
                if claim_text and claim_number:
                    claims_text.append(f"Claim {claim_number}: {claim_text}")
            
            # Extract classification codes
            cpc_codes = patent.get("cpc_current", [])
            
            # All patents get detailed analysis
            is_top_patent = True
            
            # Create patent summary for Innovation Summary
            patent_summary = {
                "id": patent.get("patent_id", "Unknown"),
                "title": patent.get("patent_title", "No title"),
                "date": patent.get("patent_date", "Unknown"),
                "abstract": patent.get("patent_abstract", "No abstract"),
                "claims_count": len(patent.get("claims", [])),
                "claims_text": claims_text,
                "inventor": self._extract_inventor(patent.get("inventors", [])),
                "assignee": self._extract_assignee(patent.get("assignees", [])),
                "cpc_codes": cpc_codes,
                "is_top_patent": is_top_patent,
                "rank": i + 1
            }
            
            patent_summaries.append(patent_summary)
        
        try:
            # Load the system prompt template
            system_prompt = load_prompt_template("prior_art_search_system")
            
            # Format query results for the report
            query_info = []
            for i, result in enumerate(query_results, 1):
                # Handle different query result formats
                query_text = result.get('query_text', result.get('reasoning', f'Query {i}'))
                result_count = result.get('result_count', result.get('count', 0))
                query_info.append(f"  - {query_text} → {result_count} patents")
            query_summary = "\n".join(query_info)
            
            # Prepare claims summary for the prompt
            claims_context = f"\n\n**Detailed Claims Analysis:**\n{found_claims_summary}" if found_claims_summary else ""
            
            # Load the user prompt template with parameters
            user_prompt = load_prompt_template("prior_art_search_simple",
                                              user_query=query,
                                              conversation_context=f"Search Queries Used (with result counts):\n{query_summary}",
                                              document_reference=f"Patents Found:\n{json.dumps(patent_summaries, indent=2)}{claims_context}")
            
            response = self.llm_client.generate_text(
                prompt=user_prompt,
                system_message=system_prompt,
                max_tokens=6000  # Increased to 6000 for comprehensive reports
            )
            
            if response.get("success"):
                return response["text"]
            else:
                raise Exception(f"LLM failed: {response.get('error')}")
                
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