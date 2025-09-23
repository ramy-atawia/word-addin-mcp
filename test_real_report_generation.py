#!/usr/bin/env python3
"""
Debug script to test real report generation
"""

import asyncio
import json
import sys
import os

# Add the backend directory to the path
sys.path.append('backend')

from app.services.patent_search_service import PatentSearchService

async def test_real_report_generation():
    """Test real report generation with actual patent data"""
    print("🔍 Testing Real Report Generation...")
    
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
        
        print("🔍 Testing report generation with real data...")
        
        # Test report generation directly with real data
        try:
            report = await service._generate_report(
                query=query,
                query_results=query_results,
                patents=patents,
                found_claims_summary="Test claims summary"
            )
            
            print(f"✅ Report generation successful")
            print(f"📏 Report length: {len(report)} characters")
            
            if len(report) > 0:
                print("✅ Report contains content")
                print(f"📄 Report preview: {report[:500]}...")
            else:
                print("❌ Report is empty")
                
                # Debug the prompt template
                print("\n🔍 Debugging prompt template...")
                from app.utils.prompt_loader import load_prompt_template
                
                # Prepare data for report
                patent_summaries = []
                for i, patent in enumerate(patents):
                    claims_text = []
                    for claim in patent.get("claims", []):
                        claim_text = claim.get("text", "")
                        claim_number = claim.get("number", "")
                        if claim_text and claim_number:
                            claims_text.append(f"Claim {claim_number}: {claim_text}")
                    
                    cpc_codes = patent.get("cpc_current", [])
                    
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
                        "is_top_patent": True,
                        "rank": i + 1
                    }
                    patent_summaries.append(patent_summary)
                
                # Format query results
                query_info = []
                for i, result in enumerate(query_results, 1):
                    query_info.append(f"  - {result.get('query_text', 'N/A')} → {result.get('result_count', 0)} patents")
                query_summary = "\n".join(query_info)
                
                # Load prompt template
                user_prompt = load_prompt_template("prior_art_search_comprehensive",
                                                  user_query=query,
                                                  conversation_context=f"Search Queries Used (with result counts):\n{query_summary}\n\nPatents Found:\n{json.dumps(patent_summaries, indent=2)}",
                                                  document_reference="Patent Search Results")
                
                print(f"📝 User prompt length: {len(user_prompt)}")
                print(f"📄 User prompt preview: {user_prompt[:500]}...")
                
                # Test LLM call directly
                print("\n🔍 Testing LLM call directly...")
                response = service.llm_client.generate_text(
                    prompt=user_prompt,
                    system_message="You are a senior patent search specialist with expertise in prior art analysis, patentability assessment, and claim analysis.",
                    max_tokens=6000
                )
                
                print(f"📊 LLM Response: {response}")
                
                if response.get("success"):
                    text = response["text"]
                    print(f"📄 LLM Text: '{text}'")
                    print(f"📏 LLM Text Length: {len(text)}")
                else:
                    print(f"❌ LLM Failed: {response.get('error')}")
                
        except Exception as e:
            print(f"❌ Report generation failed: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_report_generation())
