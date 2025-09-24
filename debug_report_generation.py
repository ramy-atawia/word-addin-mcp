#!/usr/bin/env python3
"""
Debug the report generation issue in patent search service.
"""

import asyncio
import sys
import os
import json

# Add the backend to the path
sys.path.insert(0, '/Users/Mariam/word-addin-mcp/backend')

from app.services.patent_search_service import PatentSearchService

async def debug_report_generation():
    """Debug the report generation step by step."""
    print("🔍 Debugging Report Generation...")
    
    try:
        # Create the service instance
        service = PatentSearchService()
        print("✅ Service created")
        
        # Test the search
        search_result, queries = await service.search_patents(
            query="5g ai",
            max_results=3  # Smaller for debugging
        )
        
        print(f"✅ Search completed!")
        print(f"📊 Results found: {search_result.get('results_found', 'N/A')}")
        print(f"📊 Patents count: {len(search_result.get('patents', []))}")
        
        # Check if report exists
        report = search_result.get('report', '')
        print(f"📏 Report length: {len(report)}")
        
        if not report:
            print("❌ No report generated!")
            
            # Let's debug the report generation step by step
            print("\n🔍 Debugging report generation step by step...")
            
            # Get the patents
            patents = search_result.get('patents', [])
            print(f"📊 Patents for report: {len(patents)}")
            
            if patents:
                # Test claims summarization
                print("🔍 Testing claims summarization...")
                try:
                    claims_summary = await service._summarize_claims(patents)
                    print(f"✅ Claims summary generated: {len(claims_summary)} chars")
                    print(f"📄 Claims preview: {claims_summary[:200]}...")
                except Exception as e:
                    print(f"❌ Claims summarization failed: {e}")
                
                # Test report generation
                print("🔍 Testing report generation...")
                try:
                    query_results = [
                        {"query_text": "Test query 1", "result_count": 3},
                        {"query_text": "Test query 2", "result_count": 2}
                    ]
                    
                    report = await service._generate_report(
                        query="5g ai",
                        query_results=query_results,
                        patents=patents,
                        found_claims_summary=claims_summary if 'claims_summary' in locals() else "Test claims summary"
                    )
                    
                    print(f"✅ Report generated: {len(report)} chars")
                    print(f"📄 Report preview: {report[:300]}...")
                    
                except Exception as e:
                    print(f"❌ Report generation failed: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("❌ No patents to generate report from")
        else:
            print(f"✅ Report exists: {len(report)} characters")
            print(f"📄 Report preview: {report[:300]}...")
            
    except Exception as e:
        print(f"❌ Error during debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_report_generation())
