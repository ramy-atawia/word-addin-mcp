#!/usr/bin/env python3
"""
Capture All Google Search Results

This script captures and displays ALL results returned by Google API
for the "Ramy Atawia" query to see what the other 4 results were.
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.services.web_search_service import WebSearchService

async def capture_all_results():
    """Capture all Google search results for detailed analysis."""
    print("🔍 Capturing ALL Google Search Results for 'Ramy Atawia'")
    print("=" * 60)
    
    try:
        # Initialize the service as async context manager
        async with WebSearchService() as web_search_service:
            # Get all results
            print("📡 Fetching results from Google API...")
            results = await web_search_service.search_google("Ramy Atawia", max_results=10, include_abstracts=True)
            
            print(f"✅ Total results returned: {len(results)}")
            print()
            
            # Display each result in detail
            for i, result in enumerate(results, 1):
                print(f"📋 RESULT #{i}")
                print(f"{'='*40}")
                
                # Display all available fields
                for key, value in result.items():
                    if key == 'snippet' and len(str(value)) > 150:
                        print(f"   {key}: {str(value)[:150]}...")
                    elif key == 'description' and len(str(value)) > 150:
                        print(f"   {key}: {str(value)[:150]}...")
                    elif key == 'abstract' and len(str(value)) > 150:
                        print(f"   {key}: {str(value)[:150]}...")
                    else:
                        print(f"   {key}: {value}")
                
                print()
            
            # Save detailed results to file
            output_file = "all_google_results_detailed.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Detailed results saved to: {output_file}")
            
            # Summary analysis
            print(f"\n📊 SUMMARY ANALYSIS:")
            print(f"   Total Results: {len(results)}")
            
            # Count result types
            result_types = {}
            sources = {}
            for result in results:
                result_type = result.get('type', 'unknown')
                source = result.get('source', 'unknown')
                
                result_types[result_type] = result_types.get(result_type, 0) + 1
                sources[source] = sources.get(source, 0) + 1
            
            print(f"   Result Types: {result_types}")
            print(f"   Sources: {sources}")
            
            # Show URLs
            print(f"\n🔗 All URLs:")
            for i, result in enumerate(results, 1):
                print(f"   {i}. {result.get('link', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(capture_all_results())
