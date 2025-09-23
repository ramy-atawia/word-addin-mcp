#!/usr/bin/env python3
"""
Debug script to test data passing to prompt template
"""

import asyncio
import json
import sys
import os

# Add the backend directory to the path
sys.path.append('backend')

from app.services.patent_search_service import PatentSearchService
from app.utils.prompt_loader import load_prompt_template

async def test_data_passing():
    """Test data passing to prompt template"""
    print("🔍 Testing Data Passing to Prompt Template...")
    
    try:
        # Initialize the service
        service = PatentSearchService()
        
        # Test search to get real data
        query = "5g ai"
        max_results = 2  # Small number for debugging
        
        print(f"📝 Query: {query}")
        print(f"📊 Max Results: {max_results}")
        print()
        
        # Execute search
        search_result, generated_queries = await service.search_patents(
            query=query,
            max_results=max_results
        )
        
        print("✅ Search completed!")
        print(f"📈 Results found: {search_result['results_found']}")
        print(f"📋 Patents: {len(search_result['patents'])}")
        print()
        
        # Get the real patent data
        patents = search_result['patents']
        query_results = generated_queries
        
        print("🔍 Testing data formatting...")
        
        # Prepare data for report (same as in _generate_report)
        patent_summaries = []
        for i, patent in enumerate(patents):
            # Extract claims text for analysis
            claims_text = []
            for claim in patent.get("claims", []):
                claim_text = claim.get("text", "")
                claim_number = claim.get("number", "")
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
                "inventor": service._extract_inventor(patent.get("inventors", [])),
                "assignee": service._extract_assignee(patent.get("assignees", [])),
                "cpc_codes": cpc_codes,
                "is_top_patent": is_top_patent,
                "rank": i + 1
            }
            
            patent_summaries.append(patent_summary)
        
        # Format query results for the report
        query_info = []
        for i, result in enumerate(query_results, 1):
            # Handle different query result formats
            query_text = result.get('query_text', result.get('reasoning', f'Query {i}'))
            result_count = result.get('result_count', result.get('count', 0))
            query_info.append(f"  - {query_text} → {result_count} patents")
        query_summary = "\n".join(query_info)
        
        # Prepare claims summary for the prompt
        found_claims_summary = "Test claims summary"
        claims_context = f"\n\n**Detailed Claims Analysis:**\n{found_claims_summary}" if found_claims_summary else ""
        
        print(f"📊 Patent Summaries: {len(patent_summaries)}")
        print(f"📊 Query Summary: {len(query_summary)} characters")
        print(f"📊 Claims Context: {len(claims_context)} characters")
        print()
        
        # Show sample patent summary
        if patent_summaries:
            print("🔍 Sample Patent Summary:")
            print(json.dumps(patent_summaries[0], indent=2))
            print()
        
        # Show query summary
        print("🔍 Query Summary:")
        print(query_summary)
        print()
        
        # Load prompt template with parameters
        user_prompt = load_prompt_template("prior_art_search_simple",
                                          user_query=query,
                                          conversation_context=f"Search Queries Used (with result counts):\n{query_summary}\n\nPatents Found:\n{json.dumps(patent_summaries, indent=2)}{claims_context}",
                                          document_reference="Patent Search Results")
        
        print(f"📝 User prompt length: {len(user_prompt)}")
        print(f"📄 User prompt preview: {user_prompt[:1000]}...")
        print()
        
        # Check if patent data is in the prompt
        if "patent_id" in user_prompt and "patent_title" in user_prompt:
            print("✅ Patent data is present in the prompt")
        else:
            print("❌ Patent data is missing from the prompt")
        
        # Count patent mentions in prompt
        patent_id_mentions = user_prompt.count("patent_id")
        patent_title_mentions = user_prompt.count("patent_title")
        print(f"📊 Patent ID mentions in prompt: {patent_id_mentions}")
        print(f"📊 Patent title mentions in prompt: {patent_title_mentions}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_data_passing())
