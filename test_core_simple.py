#!/usr/bin/env python3
"""
Simple core test for prior art search components with "prior art search 5G ai"
"""

import asyncio
import sys
import os

# Add the backend to the path
sys.path.insert(0, '/Users/Mariam/word-addin-mcp/backend')

from app.services.patent_search_service import PatentSearchService
from app.mcp_servers.tools.prior_art_search import PriorArtSearchTool

async def test_core_components():
    """Test the core prior art search components directly."""
    print("🔍 Testing Core Prior Art Search Components: 'prior art search 5G ai'")
    print("=" * 70)
    
    try:
        # Test 1: Patent Search Service
        print("🔍 Test 1: Patent Search Service")
        print("-" * 40)
        
        service = PatentSearchService()
        print("✅ Patent search service created")
        
        # Test search patents
        search_result, queries = await service.search_patents(
            query="5G ai",
            max_results=3
        )
        
        print(f"✅ Search completed!")
        print(f"📊 Results found: {search_result.get('results_found', 'N/A')}")
        print(f"📊 Patents count: {len(search_result.get('patents', []))}")
        
        report = search_result.get('report', '')
        if report:
            print(f"📏 Report length: {len(report)}")
            print(f"📄 Report preview: {report[:200]}...")
            
            if len(report) > 100:
                print("✅ Patent search service is generating reports!")
            else:
                print("❌ Patent search service report is too short")
        else:
            print("❌ Patent search service is not generating reports")
        
        print("\n" + "=" * 70)
        
        # Test 2: Prior Art Search Tool
        print("🔍 Test 2: Prior Art Search Tool")
        print("-" * 40)
        
        tool = PriorArtSearchTool()
        print(f"✅ Prior art search tool created: {tool.name}")
        
        # Test tool execution
        tool_result = await tool.execute({
            "query": "5G ai",
            "max_results": 3
        })
        
        print(f"✅ Tool execution completed!")
        print(f"📏 Tool result length: {len(tool_result) if isinstance(tool_result, str) else 'N/A'}")
        
        if isinstance(tool_result, str) and tool_result:
            print(f"📄 Tool result preview: {tool_result[:200]}...")
            
            if len(tool_result) > 100:
                print("✅ Prior art search tool is generating reports!")
            else:
                print("❌ Prior art search tool report is too short")
        else:
            print("❌ Prior art search tool is not generating reports")
        
        print("\n" + "=" * 70)
        print("🏁 Core component testing completed!")
        
        # Summary
        print("\n📊 SUMMARY:")
        print(f"  - Patent Search Service: {'✅ Working' if report and len(report) > 100 else '❌ Not working'}")
        print(f"  - Prior Art Search Tool: {'✅ Working' if isinstance(tool_result, str) and len(tool_result) > 100 else '❌ Not working'}")
        
        if report and len(report) > 100 and isinstance(tool_result, str) and len(tool_result) > 100:
            print("\n🎉 SUCCESS: Both components are working! The model fix should be effective.")
        else:
            print("\n❌ ISSUE: One or both components are not working properly.")
            
    except Exception as e:
        print(f"❌ Error during core testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_core_components())
