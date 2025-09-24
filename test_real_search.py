#!/usr/bin/env python3
"""
Test real patent search to show actual limiting factors
"""

import sys
import os
import json
import asyncio

# Add the backend to the path to get credentials
sys.path.insert(0, '/Users/Mariam/word-addin-mcp/backend')

from app.services.patent_search_service import PatentSearchService

async def test_real_search():
    """Test real patent search to show actual limiting factors."""
    print("🔍 Testing real patent search limiting factors")
    print("=" * 60)
    
    try:
        # Create service
        service = PatentSearchService()
        print("✅ PatentSearchService created")
        
        # Test with different query complexities
        queries = [
            "5G",  # Very broad
            "5G AI",  # Medium
            "5G network optimization",  # Specific
            "5G handover management AI",  # Very specific
        ]
        
        for query in queries:
            print(f"\n🔍 Testing query: '{query}'")
            try:
                search_result, generated_queries = await service.search_patents(
                    query=query,
                    max_results=20
                )
                
                print(f"📊 Results found: {search_result.get('results_found')}")
                print(f"📊 Patents count: {len(search_result.get('patents', []))}")
                
                # Show patent IDs
                patents = search_result.get("patents", [])
                if patents:
                    patent_ids = [p.get("patent_id") for p in patents[:5]]  # Show first 5
                    print(f"📄 Sample patent IDs: {patent_ids}")
                
                report = search_result.get("report")
                if report:
                    print(f"📏 Report length: {len(report)} chars")
                    print("✅ Report generated")
                else:
                    print("❌ No report generated")
                    
            except Exception as e:
                print(f"❌ Query failed: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_search())
