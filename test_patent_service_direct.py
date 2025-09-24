#!/usr/bin/env python3
"""
Test patent search service directly
"""

import sys
import os
import json
import asyncio

# Add the backend to the path to get credentials
sys.path.insert(0, '/Users/Mariam/word-addin-mcp/backend')

from app.services.patent_search_service import PatentSearchService

async def test_patent_service_direct():
    """Test patent search service directly."""
    print("🔍 Testing patent search service directly")
    print("=" * 60)
    
    try:
        # Create patent search service
        service = PatentSearchService()
        print("✅ Patent search service created")
        
        # Test with a simple query that should work
        print("🔍 Testing with '5G network' query...")
        
        search_result, generated_queries = await service.search_patents(
            query="5G network",
            max_results=10
        )
        
        print("✅ Search completed!")
        print(f"📊 Results found: {search_result.get('results_found')}")
        print(f"📊 Patents count: {len(search_result.get('patents', []))}")
        
        # Show patent details
        patents = search_result.get("patents", [])
        if patents:
            print(f"\n📄 Found {len(patents)} patents:")
            for i, patent in enumerate(patents, 1):
                patent_id = patent.get("patent_id", "Unknown")
                title = patent.get("patent_title", "No title")
                date = patent.get("patent_date", "Unknown")
                print(f"  {i}. {patent_id} ({date}): {title[:80]}...")
        
        # Show the report
        report = search_result.get("report")
        if report:
            print(f"\n📏 Report length: {len(report)} characters")
            print(f"\n📄 REAL PATENT SEARCH REPORT:")
            print("="*80)
            print(report)
            print("="*80)
        else:
            print("❌ No report generated")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_patent_service_direct())
