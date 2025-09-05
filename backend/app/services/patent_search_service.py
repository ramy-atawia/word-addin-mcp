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
from typing import Dict, List, Any, Tuple
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
        context: str = None, 
        conversation_history: str = None,
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
                patents = await self._search_patents_api(search_query["search_query"])
                all_patents.extend(patents)
                query_results.append({
                    "query_index": i + 1,
                    "query": search_query["search_query"],
                    "reasoning": search_query["reasoning"],
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
        context: str = None, 
        conversation_history: str = None
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
                max_tokens=4000
            )
            
            # Extract text from response
            if response.get("success"):
                response_text = response["text"]
            else:
                raise Exception(f"LLM generation failed: {response.get('error', 'Unknown error')}")
            
            # Clean response
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            # Debug: Log the raw LLM response
            logger.info(f"Raw LLM response for search queries: {response_text[:500]}...")
            
            criteria = json.loads(response_text)
            search_queries = criteria.get("search_queries", [])
            
            # Validate we have 3-5 queries (flexible range)
            if len(search_queries) < 3 or len(search_queries) > 5:
                raise Exception(f"Expected 3-5 search queries, but got {len(search_queries)}")
            
            return search_queries
            
        except Exception as e:
            logger.error(f"LLM query generation failed: {e}")
            raise Exception(f"Failed to generate search queries: {e}")
    
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
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("error", False):
                    logger.error(f"PatentsView API error: {data}")
                    raise Exception(f"PatentsView API returned error: {data}")
                
                patents = data.get("patents", [])
                logger.info(f"PatentsView API returned {len(patents)} patents")
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
You are a senior patent attorney generating a comprehensive prior art search report. You MUST follow this exact structure and include ALL specified elements.

## INPUT DATA:

**Original Query**: {query}

**Context from Word Document**: {context or ""}

**Conversation History**: {conversation_history or ""}

**Search Queries Used** (EXACTLY {len(search_queries)} queries generated by LLM):
{json.dumps(search_queries, indent=2)}

**Patents Found** ({len(patent_summaries)} patents):
{json.dumps(patent_summaries, indent=2)}

**CRITICAL INSTRUCTION**: You MUST use the actual patent data provided above. Do NOT generate a generic "no patents found" report. The patents listed above are the REAL results from the search. Use this data to create an accurate report.

## MANDATORY REPORT STRUCTURE - FOLLOW EXACTLY:

# Prior Art Search Report: {query}

## 1. Executive Summary
- **Original Query**: {query}
- **Context**: {context or "Not provided"}
- **Conversation History**: {conversation_history or "Not provided"}
- **Search Strategy**: Used {len(search_queries)} different PatentsView API queries
- **Key Findings**: Found {len(patent_summaries)} relevant patents

## 2. Search Strategy Analysis
**CRITICAL: You MUST include ALL {len(search_queries)} search queries with their reasoning and results**

For each of the {len(search_queries)} search queries, show:
- The exact PatentsView API query object
- The reasoning provided by the LLM
- Number of results returned from this query
- Why this query strategy was chosen

### Search Query 1:
**Query**: {json.dumps(query_results[0]["query"]) if query_results else "N/A"}
**Reasoning**: {query_results[0]["reasoning"] if query_results else "N/A"}
**Results Returned**: {query_results[0]["results_count"] if query_results else 0}
**Strategy**: [Your analysis of why this approach was used]

### Search Query 2:
**Query**: {json.dumps(query_results[1]["query"]) if len(query_results) > 1 else "N/A"}
**Reasoning**: {query_results[1]["reasoning"] if len(query_results) > 1 else "N/A"}
**Results Returned**: {query_results[1]["results_count"] if len(query_results) > 1 else 0}
**Strategy**: [Your analysis of why this approach was used]

### Search Query 3:
**Query**: {json.dumps(query_results[2]["query"]) if len(query_results) > 2 else "N/A"}
**Reasoning**: {query_results[2]["reasoning"] if len(query_results) > 2 else "N/A"}
**Results Returned**: {query_results[2]["results_count"] if len(query_results) > 2 else 0}
**Strategy**: [Your analysis of why this approach was used]

### Search Query 4:
**Query**: {json.dumps(query_results[3]["query"]) if len(query_results) > 3 else "N/A"}
**Reasoning**: {query_results[3]["reasoning"] if len(query_results) > 3 else "N/A"}
**Results Returned**: {query_results[3]["results_count"] if len(query_results) > 3 else 0}
**Strategy**: [Your analysis of why this approach was used]

### Search Query 5:
**Query**: {json.dumps(query_results[4]["query"]) if len(query_results) > 4 else "N/A"}
**Reasoning**: {query_results[4]["reasoning"] if len(query_results) > 4 else "N/A"}
**Results Returned**: {query_results[4]["results_count"] if len(query_results) > 4 else 0}
**Strategy**: [Your analysis of why this approach was used]

### Search Results Summary:
- **Total Queries Executed**: {len(query_results)}
- **Total Patents Found**: {sum(q["results_count"] for q in query_results)}
- **Unique Patents After Deduplication**: {len(patent_summaries)}
- **Patents Filtered Out**: {sum(q["results_count"] for q in query_results) - len(patent_summaries)}
- **Deduplication Rate**: {((sum(q["results_count"] for q in query_results) - len(patent_summaries)) / sum(q["results_count"] for q in query_results) * 100) if sum(q["results_count"] for q in query_results) > 0 else 0:.1f}%

## 3. Key Findings
- **Total Patents Found**: {len(patent_summaries)}
- **Patent List**: [List all patents with brief descriptions]

## 4. Patent Landscape Overview
- **Technology Focus**: [Analyze the current state of the technology]
- **Context Integration**: [Reference the Word document context: {context or "Not provided"}]
- **Conversation Context**: [Reference conversation history: {conversation_history or "Not provided"}]

## 5. Risk Assessment
- **Patent Conflicts**: [Evaluate potential conflicts]
- **Context Requirements**: [Consider the input context and requirements]

## 6. Recommendations
- **Based on Findings**: [Recommendations based on findings and input context]
- **Conversation History**: [Reference conversation history if relevant: {conversation_history or "Not provided"}]

## 7. Detailed Patent Analysis
**CRITICAL: You MUST include claims analysis for each patent**

For each patent, provide:
- **Patent Number**: [Patent ID]
- **Title**: [Patent title]
- **Date**: [Patent date]
- **Abstract**: [Patent abstract]
- **Inventors**: [List of inventors]
- **Claims Summary**: [Summary of all claims for this patent]
- **Key Claims**: [Most important claims and their scope]
- **Patent Link**: [Link to patent details]

### Patent 1: [Patent ID]
**Title**: [Title]
**Date**: [Date]
**Abstract**: [Abstract]
**Inventors**: [Inventors]
**Claims Summary**: [Detailed analysis of all claims]
**Key Claims**: [Most important claims]
**Patent Link**: [Link]

### Patent 2: [Patent ID]
[Continue for all patents...]

## CRITICAL REQUIREMENTS:
1. You MUST show all {len(search_queries)} search queries in section 2 with results counts
2. You MUST include the Word document context in your analysis
3. You MUST reference the conversation history where relevant
4. You MUST show the actual PatentsView API query format
5. You MUST include claims analysis for each patent in section 7
6. You MUST show deduplication statistics
7. You MUST follow this exact structure
8. **MOST IMPORTANT**: You MUST use the actual patent data provided above. There are {len(patent_summaries)} patents found - analyze them, don't say "no patents found"

**FINAL WARNING**: The patents listed in the input data are REAL search results. Use this data to create an accurate report. Do NOT generate a generic "no patents found" report.

Generate the report now following this EXACT structure:
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
    