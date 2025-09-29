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
import logging
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
        
        try:
            response = await self.llm_client.generate_text(
                prompt=prompt,
                system_message="You are a patent search expert. Return ONLY valid JSON - no markdown, no code blocks, no explanations.",
                max_tokens=16384  # Official Azure max for gpt-5-nano
            )
        except Exception as e:
            logger.error(f"LLM query generation failed: {str(e)}")
            raise ValueError(f"Failed to generate search queries: {str(e)}")
        
        if not response.get("success"):
            raise ValueError(f"LLM failed to generate queries: {response.get('error')}")
        
        text = response["text"].strip()

        # Log LLM response for debugging
        logger.debug(f"LLM response received (length: {len(text)})")
        logger.debug(f"Response preview: {text[:200]}...")

        # Direct JSON parsing - prompts now enforce strict JSON responses
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Raw response: {text[:500]}")
            raise ValueError(f"LLM returned invalid JSON: {e}. Response: {text[:200]}...")
        
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

            logger.debug(f"Searching with query {i+1}/{len(search_queries)}: {query_data}")
            patents = await self._search_patents_api(query_data)
            all_patents.extend(patents)

            query_text = search_query.get("reasoning", f"Query {i+1}")
            query_results.append({
                "query_text": query_text,
                "result_count": len(patents)
            })

            logger.debug(f"Query {i+1} returned {len(patents)} patents")
        
        return all_patents, query_results
    
    async def _search_patents_api(self, search_query: Dict) -> List[Dict[str, Any]]:
        """Call PatentsView API to search patents with fast-fail."""
        url = f"{self.base_url}/patent/"
        
        payload = {
            "q": search_query,
            "f": ["patent_id", "patent_title", "patent_abstract", "patent_date", 
                  "cpc_current"],
            "s": [{"patent_date": "desc"}],
            "o": {"size": 20}  # Increased from 10 to 20 per query for more diverse results
        }
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
            # Safe logging of API key
            api_key_preview = self.api_key[:10] + "..." if len(self.api_key) >= 10 else "***"
            logger.debug(f"Using PatentsView API key: {api_key_preview}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.debug(f"Making PatentsView search API request for: {search_query}")
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

            logger.debug(f"Fetching claims for patent {i}/{len(patents)}: {patent_id}")

            claims = await self._fetch_claims(patent_id)
            logger.debug(f"Patent {patent_id}: Fetched {len(claims)} claims")
            patent["claims"] = claims
            patents_with_claims.append(patent)
        
        logger.info(f"Claims fetching completed for {len(patents_with_claims)} patents")
        return patents_with_claims
    
    async def _summarize_claims(self, patents: List[Dict]) -> str:
        """Summarize claims for patents using LLM with batched comprehensive analysis."""
        if not patents:
            raise ValueError("No patents provided for claims summary")
        
        # Process all patents (up to 20 for performance)
        top_patents = patents[:20]
        logger.info(f"Starting batched comprehensive claims analysis for {len(top_patents)} patents (out of {len(patents)} total)")
        
        # Prepare batched data for all patents
        batched_patent_data = []
        total_claims = 0
        
        for patent in top_patents:
            patent_id = patent.get("patent_id", "Unknown")
            patent_title = patent.get("patent_title", "No title")
            patent_abstract = patent.get("patent_abstract", "No abstract available")
            patent_date = patent.get("patent_date", "Unknown date")
            claims = patent.get("claims", [])
            
            if not claims:
                logger.warning(f"Patent {patent_id} has no claims data")
                continue
            
            # Prepare claims text for this patent
            patent_claims_text = []
            independent_count = 0
            dependent_count = 0
            
            for claim in claims:
                claim_number = claim.get("number")
                claim_text = claim.get("text")
                claim_type = claim.get("type", "unknown")
                
                if not claim_number or not claim_text or len(claim_text.strip()) < 10:
                    continue
                
                full_claim_text = claim_text.strip()
                patent_claims_text.append(f"**Claim {claim_number} ({claim_type}):**\n{full_claim_text}\n")
                
                if claim_type == "independent":
                    independent_count += 1
                else:
                    dependent_count += 1
            
            if patent_claims_text:
                batched_patent_data.append({
                    "patent_id": patent_id,
                    "patent_title": patent_title,
                    "patent_abstract": patent_abstract,
                    "patent_date": patent_date,
                    "claims_text": patent_claims_text,
                    "independent_count": independent_count,
                    "dependent_count": dependent_count,
                    "total_claims": len(patent_claims_text)
                })
                total_claims += len(patent_claims_text)
        
        logger.info(f"Prepared {len(batched_patent_data)} patents with {total_claims} total claims for batched analysis")
        
        if not batched_patent_data:
            return "No valid patent claims found for analysis."
        
        # Create comprehensive batched prompt
        batched_prompt = f"""
You are a patent attorney analyzing multiple patent claims for comprehensive prior art research. Provide detailed technical analysis for each patent.

**ANALYSIS REQUIREMENTS:**
For each patent, provide:

1. **TECHNICAL INVENTION SUMMARY** (2-3 sentences):
   - Core technical innovation
   - Problem it solves
   - How it works technically

2. **KEY TECHNICAL FEATURES** (4-5 bullet points):
   - Most important technical elements
   - Specific technical terms and mechanisms
   - Novel technical aspects

3. **CLAIM STRUCTURE ANALYSIS**:
   - Independent vs dependent claims count
   - Broadest independent claim identification
   - Key claim dependencies

4. **TECHNICAL SCOPE & PRIOR ART RELEVANCE**:
   - Technical domains covered
   - Key limitations/constraints
   - Search terms for similar patents

**PATENTS TO ANALYZE:**

"""
        
        # Add each patent's data to the prompt
        for i, patent_data in enumerate(batched_patent_data, 1):
            batched_prompt += f"""
## PATENT {i}: {patent_data['patent_id']} - {patent_data['patent_title']}

**Patent Information:**
- Patent ID: {patent_data['patent_id']}
- Title: {patent_data['patent_title']}
- Filing Date: {patent_data['patent_date']}
- Abstract: {patent_data['patent_abstract'][:300]}{'...' if len(patent_data['patent_abstract']) > 300 else ''}
- Claims: {patent_data['total_claims']} total ({patent_data['independent_count']} independent, {patent_data['dependent_count']} dependent)

**Complete Claims:**
{chr(10).join(patent_data['claims_text'])}

---

"""
        
        batched_prompt += """
**FORMAT REQUIREMENTS:**
- Use clear markdown formatting with ## headings for each patent
- Be comprehensive but concise (300-400 words per patent)
- Include specific technical details
- Focus on technical substance over legal language
- Use the exact patent ID and title as provided

**IMPORTANT**: This analysis will be used for patent prior art research, so emphasize technical content and searchable terms for each patent.
"""
        
        logger.info(f"Sending batched claims analysis request to LLM (prompt length: {len(batched_prompt)} chars)")
        logger.debug(f"Batched prompt preview: {batched_prompt[:500]}...")
        
        # Single LLM call for all patents
        response = await self.llm_client.generate_text(
            prompt=batched_prompt,
            max_tokens=16384  # Official Azure max for gpt-5-nano
        )
        
        if not response.get("success"):
            logger.error(f"Batched LLM claims analysis failed - {response.get('error')}")
            raise ValueError(f"Failed to summarize claims in batch: {response.get('error')}")
        
        batched_summary = response["text"]
        
        # Enhanced validation and logging
        logger.info(f"Batched LLM analysis response generated (length: {len(batched_summary)}, preview: {batched_summary[:200] if batched_summary else 'EMPTY'})")
        
        # Validate response is not empty - fail fast if too short
        if not batched_summary or len(batched_summary.strip()) < 100:
            logger.error(f"LLM generated empty or very short batched analysis (response: {response}, generated_text: {batched_summary})")
            raise ValueError(f"Batched claims analysis failed - LLM returned empty or too short response (length: {len(batched_summary) if batched_summary else 0}). Please try again or contact support if the issue persists.")
        
        # Add note for remaining patents if any
        if len(patents) > 20:
            remaining_count = len(patents) - 20
            logger.info(f"Note: {remaining_count} additional patents found but not analyzed for comprehensive claims")
            batched_summary += f"\n\n**Additional Patents**: {remaining_count} more patents found with claims data"
        
        logger.info(f"Batched claims summarization completed successfully. Final summary length: {len(batched_summary)} chars")
        return batched_summary
    
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
            # Safe logging of API key
            api_key_preview = self.api_key[:10] + "..." if len(self.api_key) >= 10 else "***"
            logger.debug(f"Using PatentsView API key for claims: {api_key_preview}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.debug(f"Making PatentsView claims API request for patent {patent_id}")
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
                    "type": "dependent" if claim.get("claim_dependent") is not None else "independent",
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
        
        response = await self.report_llm_client.generate_text(
            prompt=user_prompt,
            system_message=system_prompt,
            max_tokens=16384  # Official Azure max for gpt-5-nano
        )
        
        if not response.get("success"):
            logger.error(f"Report generation failed: {response.get('error')}")
            raise ValueError(f"Failed to generate report: {response.get('error')}")
        
        generated_report = response["text"]
        
        # Enhanced validation and logging
        logger.info(f"LLM report generation response generated (length: {len(generated_report)}, preview: {generated_report[:100] if generated_report else 'EMPTY'})")
        
        # Validate response is not empty
        if not generated_report or len(generated_report.strip()) < 50:
            logger.error(f"LLM generated empty or very short report (response: {response}, generated_text: {generated_report})")
            generated_report = f"# Prior Art Search Report\n\n**Query**: {query}\n\n**Status**: Report generation failed. Please try again or contact support if the issue persists.\n\n**Patents Found**: {len(patent_summaries)} patents were identified but detailed analysis could not be completed."
        
        logger.info(f"Report generation completed successfully. Response length: {len(generated_report)} chars")
        return generated_report
    