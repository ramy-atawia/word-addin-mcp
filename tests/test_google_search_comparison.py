#!/usr/bin/env python3
"""
Test Script: Google Search Raw Results Analysis

This script tests the web_search_service with three queries and records:
1. Raw Google API response
2. Analysis of result types and sources

Queries to test:
1. Ramy Atawia
2. Open RAN
3. AI and 5G
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.services.web_search_service import WebSearchService

class GoogleSearchAnalysisTest:
    def __init__(self):
        self.web_search_service = WebSearchService()
        self.output_dir = Path("test_outputs_google_comparison")
        self.output_dir.mkdir(exist_ok=True)
        
    async def test_query(self, query: str, query_id: str):
        """Test a single query and record raw Google results."""
        print(f"\n{'='*60}")
        print(f"Testing Query: {query}")
        print(f"{'='*60}")
        
        try:
            # 1. Get raw Google search results
            print("1. Fetching raw Google search results...")
            raw_results = await self.web_search_service.search_google(query, max_results=5, include_abstracts=True)
            
            # 2. Analyze the results
            print("2. Analyzing raw results...")
            
            # 3. Record outputs
            test_result = {
                "query": query,
                "query_id": query_id,
                "timestamp": datetime.utcnow().isoformat(),
                "raw_google_results": raw_results,
                "analysis": {
                    "raw_result_count": len(raw_results),
                    "raw_result_types": [result.get("type", "unknown") for result in raw_results],
                    "raw_result_sources": [result.get("source", "unknown") for result in raw_results],
                    "urls": [result.get("link", "N/A") for result in raw_results],
                    "titles": [result.get("title", "N/A") for result in raw_results]
                }
            }
            
            # Save to file
            output_file = self.output_dir / f"{query_id}_results.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(test_result, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Results saved to: {output_file}")
            
            # 4. Display summary
            print(f"\n📊 Raw Google Results Count: {len(raw_results)}")
            
            if raw_results:
                print(f"\n🔍 Raw Result Types: {[r.get('type', 'unknown') for r in raw_results]}")
                print(f"🌐 Raw Result Sources: {[r.get('source', 'unknown') for r in raw_results]}")
                
                # Show first result details
                first_result = raw_results[0]
                print(f"\n📋 First Result Details:")
                print(f"   Title: {first_result.get('title', 'N/A')}")
                print(f"   Source: {first_result.get('source', 'N/A')}")
                print(f"   Type: {first_result.get('type', 'N/A')}")
                print(f"   URL: {first_result.get('link', 'N/A')}")
                print(f"   Snippet: {first_result.get('snippet', 'N/A')[:100]}...")
                
                # Show all results summary
                print(f"\n📋 All Results Summary:")
                for i, result in enumerate(raw_results, 1):
                    print(f"   {i}. {result.get('title', 'N/A')}")
                    print(f"      Source: {result.get('source', 'N/A')}")
                    print(f"      Type: {result.get('type', 'N/A')}")
                    print(f"      URL: {result.get('link', 'N/A')}")
                    print()
            else:
                print("❌ No results returned from Google API")
            
            return test_result
            
        except Exception as e:
            print(f"❌ Error testing query '{query}': {str(e)}")
            return None
    
    async def run_all_tests(self):
        """Run tests for all three queries."""
        print("🚀 Starting Google Search Analysis Tests")
        print(f"📁 Output directory: {self.output_dir.absolute()}")
        
        test_queries = [
            ("Ramy Atawia", "ramy_atawia"),
            ("Open RAN", "open_ran"),
            ("AI and 5G", "ai_5g")
        ]
        
        all_results = []
        
        for query, query_id in test_queries:
            result = await self.test_query(query, query_id)
            if result:
                all_results.append(result)
        
        # Generate summary report
        await self.generate_summary_report(all_results)
        
        print(f"\n🎉 All tests completed! Check {self.output_dir} for detailed results.")
    
    async def generate_summary_report(self, results):
        """Generate a summary report of all test results."""
        summary = {
            "test_summary": {
                "total_queries_tested": len(results),
                "successful_tests": len([r for r in results if r is not None]),
                "timestamp": datetime.utcnow().isoformat()
            },
            "query_results": []
        }
        
        for result in results:
            if result:
                summary["query_results"].append({
                    "query": result["query"],
                    "raw_results_count": result["analysis"]["raw_result_count"],
                    "result_types": result["analysis"]["raw_result_types"],
                    "sources": result["analysis"]["raw_result_sources"],
                    "urls": result["analysis"]["urls"]
                })
        
        # Save summary
        summary_file = self.output_dir / "test_summary_report.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"📋 Summary report saved to: {summary_file}")
        
        # Display summary
        print(f"\n📊 TEST SUMMARY:")
        print(f"   Total Queries: {summary['test_summary']['total_queries_tested']}")
        print(f"   Successful: {summary['test_summary']['successful_tests']}")
        
        for qr in summary["query_results"]:
            print(f"\n   Query: {qr['query']}")
            print(f"     Raw Results: {qr['raw_results_count']}")
            print(f"     Result Types: {', '.join(qr['result_types'])}")
            print(f"     Sources: {', '.join(qr['sources'])}")
            print(f"     URLs: {', '.join(qr['urls'][:2])}...")

async def main():
    """Main test runner."""
    # Check if environment is configured
    if not os.getenv('GOOGLE_API_KEY') or not os.getenv('GOOGLE_CSE_ID'):
        print("❌ Error: GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables must be set")
        print("Please set these in your .env file or environment")
        return
    
    print("🔧 Environment check passed!")
    print(f"🔑 Google API Key: {'*' * (len(os.getenv('GOOGLE_API_KEY', '')) - 4) + os.getenv('GOOGLE_API_KEY', '')[-4:]}")
    
    # Run tests
    tester = GoogleSearchAnalysisTest()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
