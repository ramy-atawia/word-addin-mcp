#!/usr/bin/env python3
"""
Debug script to test real patent data structure
"""

import asyncio
import json
import sys
import os

# Add the backend directory to the path
sys.path.append('backend')

from app.services.patent_search_service import PatentSearchService

async def test_real_patent_data():
    """Test real patent data structure"""
    print("🔍 Testing Real Patent Data Structure...")
    
    try:
        # Initialize the service
        service = PatentSearchService()
        
        # Test search
        query = "5g ai"
        max_results = 3  # Small number for debugging
        
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
        
        # Show patent data structure
        print("🔍 Patent Data Structure:")
        if search_result['patents']:
            first_patent = search_result['patents'][0]
            print(f"  - Patent ID: {first_patent.get('patent_id', 'N/A')}")
            print(f"  - Title: {first_patent.get('patent_title', 'N/A')[:100]}...")
            print(f"  - Date: {first_patent.get('patent_date', 'N/A')}")
            print(f"  - Claims: {len(first_patent.get('claims', []))}")
            print(f"  - Abstract: {first_patent.get('patent_abstract', 'N/A')[:100]}...")
            print(f"  - Inventors: {first_patent.get('inventors', [])}")
            print(f"  - Assignees: {first_patent.get('assignees', [])}")
            print(f"  - CPC Codes: {first_patent.get('cpc_current', [])}")
            
            # Check if all required fields are present
            required_fields = ['patent_id', 'patent_title', 'patent_date', 'patent_abstract', 'claims', 'inventors', 'assignees', 'cpc_current']
            missing_fields = [field for field in required_fields if field not in first_patent or not first_patent[field]]
            if missing_fields:
                print(f"⚠️  Missing fields: {missing_fields}")
            else:
                print("✅ All required fields present")
        
        print()
        print("📊 Generated Queries:")
        for i, query_info in enumerate(generated_queries, 1):
            print(f"  {i}. {query_info.get('query_text', 'N/A')} → {query_info.get('result_count', 0)} patents")
        
        print()
        print("📄 Report Preview (first 500 chars):")
        print(search_result['report'][:500])
        print("...")
        
        # Check if report contains actual patent data
        report = search_result['report']
        if "Patent ID:" in report and "Assignee:" in report:
            print("✅ Report contains patent-specific data")
        else:
            print("❌ Report appears to be generic - no patent-specific data found")
            
        # Count patent mentions in report
        patent_mentions = report.count("Patent ID:")
        print(f"📊 Patent mentions in report: {patent_mentions}")
        
        if patent_mentions < max_results:
            print(f"⚠️  Warning: Only {patent_mentions} patents mentioned in report, expected {max_results}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_patent_data())
