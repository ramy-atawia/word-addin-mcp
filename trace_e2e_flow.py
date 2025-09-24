#!/usr/bin/env python3
"""
Trace the end-to-end flow of prior art search to identify any hardcoded or mock data
"""

import sys
import os
import json
import asyncio

# Add the backend to the path to get credentials
sys.path.insert(0, '/Users/Mariam/word-addin-mcp/backend')

from app.services.patent_search_service import PatentSearchService

async def trace_e2e_flow():
    """Trace the end-to-end flow to identify hardcoded or mock data."""
    print("🔍 Tracing E2E Prior Art Search Flow")
    print("=" * 60)
    
    try:
        # Create service
        service = PatentSearchService()
        print("✅ PatentSearchService created")
        
        # Step 1: Query Generation
        print("\n🔍 Step 1: Query Generation")
        print("-" * 40)
        search_queries = await service._generate_queries("5G network")
        print(f"📊 Generated {len(search_queries)} queries")
        for i, query in enumerate(search_queries, 1):
            print(f"  Query {i}: {query.get('reasoning', 'No reasoning')}")
        
        # Step 2: Patent Search
        print("\n🔍 Step 2: Patent Search via PatentsView API")
        print("-" * 40)
        all_patents, query_results = await service._search_all_queries(search_queries)
        print(f"📊 Found {len(all_patents)} total patents")
        print(f"📊 Query results: {query_results}")
        
        # Show sample patent data
        if all_patents:
            sample_patent = all_patents[0]
            print(f"\n📄 Sample patent data (first patent):")
            print(f"  - Patent ID: {sample_patent.get('patent_id')}")
            print(f"  - Title: {sample_patent.get('patent_title')}")
            print(f"  - Date: {sample_patent.get('patent_date')}")
            print(f"  - Abstract: {sample_patent.get('patent_abstract', '')[:100]}...")
            print(f"  - Inventors: {sample_patent.get('inventors', [])}")
            print(f"  - Assignees: {sample_patent.get('assignees', [])}")
            print(f"  - CPC Codes: {sample_patent.get('cpc_current', [])}")
        
        # Step 3: Deduplication
        print("\n🔍 Step 3: Deduplication")
        print("-" * 40)
        unique_patents = service._deduplicate(all_patents)[:10]
        print(f"📊 After deduplication: {len(unique_patents)} unique patents")
        
        # Step 4: Claims Fetching
        print("\n🔍 Step 4: Claims Fetching from PatentsView API")
        print("-" * 40)
        patents_with_claims = await service._add_claims(unique_patents)
        print(f"📊 Patents with claims: {len(patents_with_claims)}")
        
        # Show sample claims data
        if patents_with_claims:
            sample_patent = patents_with_claims[0]
            claims = sample_patent.get("claims", [])
            print(f"\n📄 Sample claims data (first patent):")
            print(f"  - Claims count: {len(claims)}")
            if claims:
                sample_claim = claims[0]
                print(f"  - Sample claim: {sample_claim.get('number')} - {sample_claim.get('text', '')[:100]}...")
        
        # Step 5: Claims Summarization
        print("\n🔍 Step 5: Claims Summarization via LLM")
        print("-" * 40)
        found_claims_summary = await service._summarize_claims(patents_with_claims)
        print(f"📊 Claims summary length: {len(found_claims_summary)} chars")
        print(f"📄 Claims summary preview: {found_claims_summary[:200]}...")
        
        # Step 6: Report Generation Data Preparation
        print("\n🔍 Step 6: Report Generation Data Preparation")
        print("-" * 40)
        
        # Prepare patent summaries
        patent_summaries = []
        for i, patent in enumerate(patents_with_claims):
            patent_id = patent.get("patent_id")
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
                "claims_info": claims_info,
                "inventor": service._extract_inventor(patent.get("inventors", [])),
                "assignee": service._extract_assignee(patent.get("assignees", [])),
                "cpc_codes": patent.get("cpc_current", []),
                "is_top_patent": True,
                "rank": i + 1
            }
            patent_summaries.append(patent_summary)
        
        print(f"📊 Patent summaries prepared: {len(patent_summaries)}")
        print(f"📄 Sample patent summary: {json.dumps(patent_summaries[0], indent=2)}")
        
        # Step 7: Prompt Construction
        print("\n🔍 Step 7: Prompt Construction")
        print("-" * 40)
        
        from app.utils.prompt_loader import load_prompt_template
        
        # Load system prompt
        system_prompt = load_prompt_template("prior_art_search_system")
        print(f"📊 System prompt length: {len(system_prompt)} chars")
        
        # Format query results
        query_info = []
        for i, result in enumerate(query_results, 1):
            query_text = result.get('query_text', f'Query {i}')
            result_count = result.get('result_count', 0)
            query_info.append(f"  - {query_text} → {result_count} patents")
        query_summary = "\n".join(query_info)
        
        claims_context = f"\n\n**Detailed Claims Analysis:**\n{found_claims_summary}"
        document_reference = f"Patents Found:\n{json.dumps(patent_summaries, indent=2)}{claims_context}"
        
        user_prompt = load_prompt_template("prior_art_search_simple",
                                          user_query="5G network",
                                          conversation_context=f"Search Queries Used (with result counts):\n{query_summary}",
                                          document_reference=document_reference)
        
        print(f"📊 User prompt length: {len(user_prompt)} chars")
        print(f"📊 Total prompt size: {len(user_prompt) + len(system_prompt)} chars")
        
        # Step 8: LLM Report Generation
        print("\n🔍 Step 8: LLM Report Generation")
        print("-" * 40)
        
        response = service.report_llm_client.generate_text(
            prompt=user_prompt,
            system_message=system_prompt,
            max_tokens=6000
        )
        
        if response.get('success') and response.get('text'):
            report = response['text']
            print(f"📊 Report generated: {len(report)} chars")
            print(f"📄 Report preview: {report[:300]}...")
            
            # Check for hardcoded values in the report
            print("\n🔍 Checking for hardcoded values in report:")
            print("-" * 40)
            
            # Check for template placeholders that might not be replaced
            hardcoded_checks = [
                ("[current date]", "current date"),
                ("[earliest]", "earliest date"),
                ("[latest]", "latest date"),
                ("[total patents]", "total patents count"),
                ("[databases]", "databases searched"),
                ("[search terms]", "search terms"),
                ("[date range]", "date range"),
            ]
            
            for placeholder, description in hardcoded_checks:
                if placeholder in report:
                    print(f"❌ Found hardcoded placeholder: {placeholder} ({description})")
                else:
                    print(f"✅ No hardcoded placeholder: {placeholder}")
            
            # Check if report contains actual patent data
            if any(patent["id"] in report for patent in patent_summaries):
                print("✅ Report contains actual patent IDs")
            else:
                print("❌ Report missing actual patent IDs")
                
            if any(patent["title"] in report for patent in patent_summaries):
                print("✅ Report contains actual patent titles")
            else:
                print("❌ Report missing actual patent titles")
                
        else:
            print("❌ Report generation failed")
            print(f"📊 Response: {response}")
        
        print("\n" + "="*60)
        print("🏁 E2E Trace Complete")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(trace_e2e_flow())
