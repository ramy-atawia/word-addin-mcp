#!/usr/bin/env python3
"""
Direct test of prior art search functionality to verify the status field fix.
This bypasses authentication and tests the core logic directly.
"""

import asyncio
import sys
import os

# Add the backend to the path
sys.path.insert(0, '/Users/Mariam/word-addin-mcp/backend')

from app.services.patent_search_service import PatentSearchService
from app.mcp_servers.tools.prior_art_search import PriorArtSearchTool

async def test_prior_art_search():
    """Test the prior art search tool directly."""
    print("🔍 Testing Prior Art Search Tool Directly...")
    
    try:
        # Create the tool instance
        tool = PriorArtSearchTool()
        print(f"✅ Tool created: {tool.name}")
        
        # Test parameters
        test_params = {
            "query": "5g ai",
            "max_results": 10
        }
        
        print(f"📝 Testing with parameters: {test_params}")
        
        # Execute the tool
        result = await tool.execute(test_params)
        
        print(f"✅ Tool execution completed!")
        print(f"📊 Result type: {type(result)}")
        print(f"📏 Result length: {len(result) if isinstance(result, str) else 'N/A'}")
        
        # Show first 500 characters of the result
        if isinstance(result, str):
            print(f"\n📄 Result preview (first 500 chars):")
            print("-" * 50)
            print(result[:500])
            if len(result) > 500:
                print("... [truncated]")
            print("-" * 50)
            
            # Check if it looks like a comprehensive report
            if "Executive Summary" in result or "Research Findings" in result or "patent" in result.lower():
                print("✅ Result appears to be a comprehensive report!")
            else:
                print("❌ Result appears to be basic/generic")
        else:
            print(f"❌ Unexpected result type: {type(result)}")
            print(f"Result: {result}")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

async def test_patent_search_service():
    """Test the patent search service directly."""
    print("\n🔍 Testing Patent Search Service Directly...")
    
    try:
        # Create the service instance
        service = PatentSearchService()
        print("✅ Service created")
        
        # Test the search
        search_result, queries = await service.search_patents(
            query="5g ai",
            max_results=5
        )
        
        print(f"✅ Search completed!")
        print(f"📊 Search result type: {type(search_result)}")
        print(f"📊 Queries type: {type(queries)}")
        
        if isinstance(search_result, dict):
            print(f"📊 Results found: {search_result.get('results_found', 'N/A')}")
            print(f"📊 Patents count: {len(search_result.get('patents', []))}")
            
            report = search_result.get('report', '')
            if report:
                print(f"📏 Report length: {len(report)}")
                print(f"\n📄 Report preview (first 300 chars):")
                print("-" * 50)
                print(report[:300])
                if len(report) > 300:
                    print("... [truncated]")
                print("-" * 50)
            else:
                print("❌ No report in search result")
        else:
            print(f"❌ Unexpected search result type: {type(search_result)}")
            
    except Exception as e:
        print(f"❌ Error during service test: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all tests."""
    print("🚀 Starting Prior Art Search Tests...")
    print("=" * 60)
    
    # Test the patent search service first
    await test_patent_search_service()
    
    print("\n" + "=" * 60)
    
    # Test the prior art search tool
    await test_prior_art_search()
    
    print("\n" + "=" * 60)
    print("🏁 Tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
