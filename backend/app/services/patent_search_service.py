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
        self.llm_client = LLMClient(
            azure_openai_api_key=settings.azure_openai_api_key,
            azure_openai_endpoint=settings.azure_openai_endpoint,
            azure_openai_deployment=settings.azure_openai_deployment
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
        found_claims_summary = await self._summarize_claims(patents_with_claims)
        
        # Step 6: Generate report (fail if cannot generate)
        report = await self._generate_report(query, query_results, patents_with_claims, found_claims_summary)
        
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
        
        # Clean JSON markers
        if text.startswith("```json"):
            text = text[7:-3]
        elif text.startswith("```"):
            text = text[3:-3]
        
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON at position {e.pos}: {e}")
        
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
            
            patents = await self._search_patents_api(query_data)
            all_patents.extend(patents)
            
            query_text = search_query.get("reasoning", f"Query {i+1}")
            query_results.append({
                "query_text": query_text,
                "result_count": len(patents)
            })
            
            logger.info(f"Query {i+1} returned {len(patents)} patents")
        
        return all_patents, query_results
    
    async def _search_patents_api(self, search_query: Dict) -> List[Dict[str, Any]]:
        """Call PatentsView API to search patents with fast-fail."""
        url = f"{self.base_url}/patent/"
        
        payload = {
            "q": search_query,
            "f": ["patent_id", "patent_title", "patent_abstract", "patent_date", 
                  "inventors", "assignees", "cpc_current"],
            "s": [{"patent_date": "desc"}],
            "o": {"size": 10}
        }
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        
        async with httpx.AsyncClient(timeout=60.0) as client:
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
        patents_with_claims = []
        
        for patent in patents:
            patent_id = patent.get("patent_id")
            if not patent_id:
                raise ValueError("Patent missing required 'patent_id' field")
            
            claims = await self._fetch_claims(patent_id)
            patent["claims"] = claims
            patents_with_claims.append(patent)
        
        return patents_with_claims
    
    async def _summarize_claims(self, patents: List[Dict]) -> str:
        """Summarize claims for patents using LLM with strict requirements."""
        if not patents:
            raise ValueError("No patents provided for claims summary")
        
        # Process top 5 patents for performance
        top_patents = patents[:5]
        claims_summaries = []
        
        async def process_patent_claims(patent):
            patent_id = patent.get("patent_id", "Unknown")
            patent_title = patent.get("patent_title", "No title")
            claims = patent.get("claims", [])
            
            if not claims:
                return f"**Patent {patent_id}: {patent_title}**\n- Claims: Not available\n"
            
            # Prepare claims text (first 3 claims only)
            claims_text = []
            for claim in claims[:3]:
                claim_number = claim.get("number")
                claim_text = claim.get("text")
                claim_type = claim.get("type", "unknown")
                
                if not claim_number or not claim_text:
                    continue
                
                if len(claim_text.strip()) < 10:
                    continue
                
                # Truncate very long claims
                truncated_text = claim_text[:500] + "..." if len(claim_text) > 500 else claim_text
                claims_text.append(f"Claim {claim_number} ({claim_type}): {truncated_text}")
            
            if not claims_text:
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
            
            response = self.llm_client.generate_text(
                prompt=claims_prompt,
                max_tokens=300
            )
            
            if not response.get("success"):
                raise ValueError(f"Failed to summarize claims for patent {patent_id}: {response.get('error')}")
            
            summary = response["text"]
            return f"**Patent {patent_id}: {patent_title}**\n{summary}\n"
        
        # Process patents in parallel
        tasks = [process_patent_claims(patent) for patent in top_patents]
        results = await asyncio.gather(*tasks)
        
        claims_summaries.extend(results)
        
        # Add note for remaining patents if any
        if len(patents) > 5:
            remaining_count = len(patents) - 5
            claims_summaries.append(f"**Additional Patents**: {remaining_count} more patents found with claims data\n")
        
        return "\n".join(claims_summaries)
    
    async def _fetch_claims(self, patent_id: str) -> List[Dict]:
        """Fetch claims for a specific patent with strict validation."""
        if not patent_id:
            raise ValueError("Patent ID is required")
        
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
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if not response.is_success:
                response.raise_for_status()
            
            data = response.json()
            
            if data.get("error"):
                raise ValueError(f"PatentsView Claims API Error: {data['error']}")
            
            claims_data = data.get("g_claims", [])
            
            claims = []
            for claim in claims_data:
                claim_text = claim.get("claim_text")
                claim_number = claim.get("claim_number")
                
                if not claim_text or not claim_number:
                    continue
                
                if len(claim_text.strip()) < 10:
                    continue
                
                claims.append({
                    "number": claim_number,
                    "text": claim_text.strip(),
                    "type": "dependent" if claim.get("claim_dependent") else "independent",
                    "sequence": claim.get("claim_sequence", 0)
                })
            
            return claims
    
    async def _generate_report(self, query: str, query_results: List[Dict], 
                             patents: List[Dict], found_claims_summary: str) -> str:
        """Generate markdown report using LLM with strict requirements."""
        if not patents:
            raise ValueError("No patents provided for report generation")
        
        if not found_claims_summary:
            raise ValueError("Claims summary is required for report generation")
        
        # Prepare patent summaries
        patent_summaries = []
        for i, patent in enumerate(patents):
            patent_id = patent.get("patent_id")
            if not patent_id:
                raise ValueError(f"Patent {i} missing required 'patent_id' field")
            
            claims_text = []
            for claim in patent.get("claims", []):
                claim_text = claim.get("text")
                claim_number = claim.get("number")
                if claim_text and claim_number:
                    claims_text.append(f"Claim {claim_number}: {claim_text}")
            
            patent_summary = {
                "id": patent_id,
                "title": patent.get("patent_title", "No title"),
                "date": patent.get("patent_date", "Unknown"),
                "abstract": patent.get("patent_abstract", "No abstract"),
                "claims_count": len(patent.get("claims", [])),
                "claims_text": claims_text,
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
        
        response = self.llm_client.generate_text(
            prompt=user_prompt,
            system_message=system_prompt,
            max_tokens=6000
        )
        
        if not response.get("success"):
            raise ValueError(f"Failed to generate report: {response.get('error')}")
        
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