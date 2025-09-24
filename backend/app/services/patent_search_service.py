"""
Fast-Fail Patent Search Service

Core Flow:
1. Generate search queries (strict validation)
2. Search patents via PatentsView API (fail fast)
3. Fetch patent claims (no fallbacks)
4. Generate markdown report (strict requirements)
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
    """Fast-fail patent search service with strict validation."""
    
    def __init__(self):
        # Validate required configuration at startup
        if not settings.azure_openai_api_key:
            raise ValueError("Azure OpenAI API key is required")
        if not settings.azure_openai_endpoint:
            raise ValueError("Azure OpenAI endpoint is required")
        if not settings.azure_openai_deployment:
            raise ValueError("Azure OpenAI deployment is required")
        
        from app.services.llm_client import LLMClient
        # Use gpt-5-nano for query generation (works well)
        self.llm_client = LLMClient(
            azure_openai_api_key=settings.azure_openai_api_key,
            azure_openai_endpoint=settings.azure_openai_endpoint,
            azure_openai_deployment=settings.azure_openai_deployment
        )
        
        # Use same deployment for report generation as main client (consistent with actual deployment)
        self.report_llm_client = LLMClient(
            azure_openai_api_key=settings.azure_openai_api_key,
            azure_openai_endpoint=settings.azure_openai_endpoint,
            azure_openai_deployment=settings.azure_openai_deployment  # Use actual deployed model
        )
        
        # PatentsView API key is optional but validate if provided
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
        Main patent search function with fast-fail behavior.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        if max_results <= 0:
            raise ValueError("max_results must be positive")
        
        logger.info(f"Starting patent search for: {query}")
        
        # Step 1: Generate search queries (fail if insufficient)
        search_queries = await self._generate_queries(query)
        
        # Step 2: Search for patents (fail if no results)
        all_patents, query_results = await self._search_all_queries(search_queries)
        
        if not all_patents:
            raise ValueError("No patents found for any search query")
        
        # Step 3: Deduplicate and limit results
        unique_patents = self._deduplicate(all_patents)[:max_results]
        
        # Step 4: Get claims for each patent (fail if critical patents lack claims)
        patents_with_claims = await self._add_claims(unique_patents)
        
        # Step 5: Summarize claims using LLM (fail if cannot summarize)
        logger.info(f"Starting claims summarization for {len(patents_with_claims)} patents")
        found_claims_summary = await self._summarize_claims(patents_with_claims)
        logger.info(f"Claims summarization completed. Summary length: {len(found_claims_summary)} chars")
        
        # Step 6: Generate report (fail if cannot generate)
        logger.info("Starting final report generation")
        report = await self._generate_report(query, query_results, patents_with_claims, found_claims_summary)
        logger.info(f"Final report generated successfully. Report length: {len(report)} chars")
        
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
    
    async def _generate_queries(self, query: str) -> List[Dict[str, Any]]:
        """Generate search queries using LLM with strict validation."""
        prompt = load_prompt_template("patent_search_query_generation", 
                                    query=query,
                                    context="",
                                    conversation_history="")
        
        response = self.llm_client.generate_text(
            prompt=prompt,
            system_message="You are a patent search expert. Think like a domain expert and analyze query specificity iteratively.",
            max_tokens=4000
        )
        
        if not response.get("success"):
            raise ValueError(f"LLM failed to generate queries: {response.get('error')}")
        
        text = response["text"].strip()

        # Debug logging to see what LLM returned
        logger.debug(f"🔍 PATENT SERVICE DEBUG - Raw LLM response (length: {len(text)}):")
        logger.debug(f"🔍 PATENT SERVICE DEBUG - Response starts with: {text[:200]}...")
        logger.debug(f"🔍 PATENT SERVICE DEBUG - Response ends with: {text[-200:] if len(text) > 200 else text}")

        # Clean JSON markers
        if text.startswith("```json"):
            text = text[7:-3]
        elif text.startswith("```"):
            text = text[3:-3]

        # Debug cleaned text
        logger.debug(f"🔍 PATENT SERVICE DEBUG - After cleaning (length: {len(text)}):")
        logger.debug(f"🔍 PATENT SERVICE DEBUG - Cleaned text: {text[:300]}...")

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"🔍 PATENT SERVICE DEBUG - JSON parsing failed at position {e.pos}: {e}")
            logger.error(f"🔍 PATENT SERVICE DEBUG - Attempting to fix JSON...")
            # Try to fix common JSON issues
            if text.startswith("```"):
                text = text[3:-3]
            text = text.strip()
            if text.startswith("json"):
                text = text[4:].strip()
            try:
                data = json.loads(text)
                logger.info("🔍 PATENT SERVICE DEBUG - JSON fixed successfully")
            except json.JSONDecodeError:
                logger.error(f"🔍 PATENT SERVICE DEBUG - Failed to fix JSON. Raw response: {text}")
                raise ValueError(f"LLM returned invalid JSON at position {e.pos}: {e}. Raw response: {text[:500]}")
        
        queries = data.get("search_queries")
        if not queries:
            raise ValueError("LLM response missing 'search_queries' field")
        
        if len(queries) < 3:
            raise ValueError(f"Insufficient queries generated: {len(queries)} (minimum: 3)")
        
        return queries
    
    async def _search_all_queries(self, search_queries: List[Dict]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Execute all search queries and collect results."""
        all_patents = []
        query_results = []
        
        for i, search_query in enumerate(search_queries):
            query_data = search_query.get("search_query")
            if not query_data:
                raise ValueError(f"Query {i+1} missing 'search_query' field")

            # Add delay between search queries to prevent rate limiting
            if i > 0:
                logger.info("🔍 PATENT SERVICE DEBUG - Adding 3-second delay between search queries...")
                await asyncio.sleep(3)

            logger.info(f"🔍 PATENT SERVICE DEBUG - Searching with query {i+1}/{len(search_queries)}: {query_data}")
            patents = await self._search_patents_api(query_data)
            all_patents.extend(patents)

            query_text = search_query.get("reasoning", f"Query {i+1}")
            query_results.append({
                "query_text": query_text,
                "result_count": len(patents)
            })

            logger.info(f"🔍 PATENT SERVICE DEBUG - Query {i+1} returned {len(patents)} patents")
        
        return all_patents, query_results
    
    async def _search_patents_api(self, search_query: Dict) -> List[Dict[str, Any]]:
        """Call PatentsView API to search patents with fast-fail."""
        url = f"{self.base_url}/patent/"
        
        payload = {
            "q": search_query,
            "f": ["patent_id", "patent_title", "patent_abstract", "patent_date", 
                  "inventors", "assignees", "cpc_current"],
            "s": [{"patent_date": "desc"}],
            "o": {"size": 20}  # Increased from 10 to 20 per query for more diverse results
        }
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
            logger.debug(f"🔍 PATENT SERVICE DEBUG - Using PatentsView API key: {self.api_key[:10]}...")

        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.info(f"🔍 PATENT SERVICE DEBUG - Making PatentsView search API request for: {search_query}")
            response = await client.post(url, json=payload, headers=headers)
            
            if not response.is_success:
                response.raise_for_status()
            
            data = response.json()
            
            if data.get("error"):
                raise ValueError(f"PatentsView API Error: {data['error']}")
            
            return data.get("patents", [])
    
    def _deduplicate(self, patents: List[Dict]) -> List[Dict]:
        """Remove duplicate patents by ID."""
        seen = set()
        unique = []
        
        for patent in patents:
            patent_id = patent.get("patent_id")
            if not patent_id:
                raise ValueError("Patent missing required 'patent_id' field")
            
            if patent_id not in seen:
                seen.add(patent_id)
                unique.append(patent)
        
        return unique
    
    async def _add_claims(self, patents: List[Dict]) -> List[Dict]:
        """Add claims data to each patent with strict validation."""
        logger.info(f"Starting claims fetching for {len(patents)} patents")
        patents_with_claims = []
        
        for i, patent in enumerate(patents, 1):
            patent_id = patent.get("patent_id")
            if not patent_id:
                raise ValueError("Patent missing required 'patent_id' field")

            logger.info(f"🔍 PATENT SERVICE DEBUG - Fetching claims for patent {i}/{len(patents)}: {patent_id}")

            # Add delay between claims requests to prevent rate limiting
            if i > 1:
                logger.info("🔍 PATENT SERVICE DEBUG - Adding 1-second delay between claims requests...")
                await asyncio.sleep(1)

            claims = await self._fetch_claims(patent_id)
            logger.info(f"🔍 PATENT SERVICE DEBUG - Patent {patent_id}: Fetched {len(claims)} claims")
            patent["claims"] = claims
            patents_with_claims.append(patent)
        
        logger.info(f"Claims fetching completed for {len(patents_with_claims)} patents")
        return patents_with_claims
    
    async def _summarize_claims(self, patents: List[Dict]) -> str:
        """Summarize claims for patents using LLM with strict requirements."""
        if not patents:
            raise ValueError("No patents provided for claims summary")
        
        # Process all patents (up to 20 for performance)
        top_patents = patents[:20]
        logger.info(f"Starting claims analysis for {len(top_patents)} patents (out of {len(patents)} total)")
        claims_summaries = []
        
        async def process_patent_claims(patent):
            patent_id = patent.get("patent_id", "Unknown")
            patent_title = patent.get("patent_title", "No title")
            claims = patent.get("claims", [])
            
            logger.info(f"Processing claims for patent {patent_id}: {patent_title[:50]}...")
            logger.info(f"Patent {patent_id} has {len(claims)} claims")
            
            if not claims:
                logger.warning(f"Patent {patent_id} has no claims data")
                return f"**Patent {patent_id}: {patent_title}**\n- Claims: Not available\n"
            
            # Prepare claims text (all claims)
            claims_text = []
            valid_claims_count = 0
            for claim in claims:  # Process all claims, not just first 3
                claim_number = claim.get("number")
                claim_text = claim.get("text")
                claim_type = claim.get("type", "unknown")
                
                if not claim_number or not claim_text:
                    logger.debug(f"Patent {patent_id}: Skipping claim {claim_number} - missing number or text")
                    continue
                
                if len(claim_text.strip()) < 10:
                    logger.debug(f"Patent {patent_id}: Skipping claim {claim_number} - text too short")
                    continue
                
                # Truncate very long claims to 300 chars to fit more claims
                truncated_text = claim_text[:300] + "..." if len(claim_text) > 300 else claim_text
                claims_text.append(f"Claim {claim_number} ({claim_type}): {truncated_text}")
                valid_claims_count += 1
            
            logger.info(f"Patent {patent_id}: Processed {valid_claims_count} valid claims out of {len(claims)} total")
            
            if not claims_text:
                logger.warning(f"Patent {patent_id}: No valid claim text found after processing")
                return f"**Patent {patent_id}: {patent_title}**\n- Claims: No valid claim text found\n"
            
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
            
            logger.info(f"Patent {patent_id}: Sending claims analysis request to LLM (prompt length: {len(claims_prompt)} chars)")
            logger.debug(f"Patent {patent_id}: Claims prompt preview: {claims_prompt[:200]}...")
            
            response = self.llm_client.generate_text(
                prompt=claims_prompt,
                max_tokens=500  # Increased to handle more claims
            )
            
            if not response.get("success"):
                logger.error(f"Patent {patent_id}: LLM claims analysis failed - {response.get('error')}")
                raise ValueError(f"Failed to summarize claims for patent {patent_id}: {response.get('error')}")
            
            summary = response["text"]
            logger.info(f"Patent {patent_id}: Claims analysis completed successfully (response length: {len(summary)} chars)")
            logger.debug(f"Patent {patent_id}: Claims analysis response preview: {summary[:200]}...")
            return f"**Patent {patent_id}: {patent_title}**\n{summary}\n"
        
        # Process patents in parallel
        logger.info(f"Starting parallel processing of {len(top_patents)} patents for claims analysis")
        tasks = [process_patent_claims(patent) for patent in top_patents]
        
        try:
            results = await asyncio.gather(*tasks)
            logger.info(f"Successfully completed claims analysis for {len(results)} patents")
        except Exception as e:
            logger.error(f"Error during parallel claims processing: {str(e)}")
            raise
        
        claims_summaries.extend(results)
        
        # Add note for remaining patents if any
        if len(patents) > 20:
            remaining_count = len(patents) - 20
            logger.info(f"Note: {remaining_count} additional patents found but not analyzed for claims")
            claims_summaries.append(f"**Additional Patents**: {remaining_count} more patents found with claims data\n")
        
        final_summary = "\n".join(claims_summaries)
        logger.info(f"Claims summarization completed. Final summary length: {len(final_summary)} chars")
        return final_summary
    
    async def _fetch_claims(self, patent_id: str) -> List[Dict]:
        """Fetch claims for a specific patent with strict validation."""
        if not patent_id:
            raise ValueError("Patent ID is required")
        
        logger.debug(f"Fetching claims for patent {patent_id}")
        url = f"{self.base_url}/g_claim/"
        
        payload = {
            "q": {"patent_id": patent_id},
            "f": ["claim_sequence", "claim_text", "claim_number", "claim_dependent"],
            "o": {"size": 100},
            "s": [{"claim_sequence": "asc"}]
        }
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
            logger.debug(f"🔍 PATENT SERVICE DEBUG - Using PatentsView API key for claims: {self.api_key[:10]}...")

        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(f"🔍 PATENT SERVICE DEBUG - Making PatentsView claims API request for patent {patent_id}")
            response = await client.post(url, json=payload, headers=headers)
            
            if not response.is_success:
                logger.error(f"PatentsView Claims API call failed for patent {patent_id}: {response.status_code}")
                response.raise_for_status()
            
            data = response.json()
            
            if data.get("error"):
                logger.error(f"PatentsView Claims API error for patent {patent_id}: {data['error']}")
                raise ValueError(f"PatentsView Claims API Error: {data['error']}")
            
            claims_data = data.get("g_claims", [])
            logger.debug(f"Patent {patent_id}: Received {len(claims_data)} raw claims from API")
            
            claims = []
            for claim in claims_data:
                claim_text = claim.get("claim_text")
                claim_number = claim.get("claim_number")
                
                if not claim_text or not claim_number:
                    logger.debug(f"Patent {patent_id}: Skipping claim - missing text or number")
                    continue
                
                if len(claim_text.strip()) < 10:
                    logger.debug(f"Patent {patent_id}: Skipping claim {claim_number} - text too short")
                    continue
                
                claims.append({
                    "number": claim_number,
                    "text": claim_text.strip(),
                    "type": "dependent" if claim.get("claim_dependent") else "independent",
                    "sequence": claim.get("claim_sequence", 0)
                })
            
            logger.info(f"Patent {patent_id}: Processed {len(claims)} valid claims from {len(claims_data)} raw claims")
            return claims
    
    async def _generate_report(self, query: str, query_results: List[Dict], 
                             patents: List[Dict], found_claims_summary: str) -> str:
        """Generate markdown report using LLM with strict requirements."""
        if not patents:
            raise ValueError("No patents provided for report generation")
        
        if not found_claims_summary:
            raise ValueError("Claims summary is required for report generation")
        
        # Prepare patent summaries (without full claims text to reduce prompt size)
        patent_summaries = []
        for i, patent in enumerate(patents):
            patent_id = patent.get("patent_id")
            if not patent_id:
                raise ValueError(f"Patent {i} missing required 'patent_id' field")
            
            # Extract only claim numbers and types (not full text) to reduce prompt size
            claims_info = []
            for claim in patent.get("claims", []):
                claim_number = claim.get("number")
                claim_type = claim.get("type", "unknown")
                if claim_number:
                    claims_info.append(f"Claim {claim_number} ({claim_type})")
            
            patent_summary = {
                "id": patent_id,
                "title": patent.get("patent_title", "No title"),
                "date": patent.get("patent_date", "Unknown"),
                "abstract": patent.get("patent_abstract", "No abstract"),
                "claims_count": len(patent.get("claims", [])),
                "claims_info": claims_info,  # Just claim numbers/types, not full text
                "inventor": self._extract_inventor(patent.get("inventors", [])),
                "assignee": self._extract_assignee(patent.get("assignees", [])),
                "cpc_codes": patent.get("cpc_current", []),
                "is_top_patent": True,
                "rank": i + 1
            }
            patent_summaries.append(patent_summary)
        
        # Load prompt templates
        system_prompt = load_prompt_template("prior_art_search_system")
        
        # Format query results
        query_info = []
        for i, result in enumerate(query_results, 1):
            query_text = result.get('query_text', f'Query {i}')
            result_count = result.get('result_count', 0)
            query_info.append(f"  - {query_text} → {result_count} patents")
        query_summary = "\n".join(query_info)
        
        claims_context = f"\n\n**Detailed Claims Analysis:**\n{found_claims_summary}"
        
        user_prompt = load_prompt_template("prior_art_search_simple",
                                          user_query=query,
                                          conversation_context=f"Search Queries Used (with result counts):\n{query_summary}",
                                          document_reference=f"Patents Found:\n{json.dumps(patent_summaries, indent=2)}{claims_context}")
        
        logger.info(f"Generating final report with prompt length: {len(user_prompt)} chars")
        logger.debug(f"Report generation prompt preview: {user_prompt[:300]}...")
        
        response = self.report_llm_client.generate_text(
            prompt=user_prompt,
            system_message=system_prompt,
            max_tokens=12000  # Conservative limit for gpt-5-nano model
        )
        
        if not response.get("success"):
            logger.error(f"Report generation failed: {response.get('error')}")
            raise ValueError(f"Failed to generate report: {response.get('error')}")
        
        logger.info(f"Report generation completed successfully. Response length: {len(response['text'])} chars")
        return response["text"]
    
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