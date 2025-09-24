#!/usr/bin/env python3
"""
Show a sample of the generated patent search report
"""

import sys
import os
import json
import asyncio

# Add the backend to the path to get credentials
sys.path.insert(0, '/Users/Mariam/word-addin-mcp/backend')

from app.services.patent_search_service import PatentSearchService

async def show_report_sample():
    """Show a sample of the generated patent search report."""
    print("🔍 Generating patent search report sample")
    print("=" * 60)
    
    try:
        # Create service
        service = PatentSearchService()
        print("✅ PatentSearchService created")
        
        # Generate a report
        print("🔍 Generating report for '5G AI'...")
        search_result, generated_queries = await service.search_patents(
            query="5G AI",
            max_results=10
        )
        
        print(f"📊 Results found: {search_result.get('results_found')}")
        print(f"📊 Patents count: {len(search_result.get('patents', []))}")
        
        report = search_result.get("report")
        if report:
            print(f"\n📏 Report length: {len(report)} characters")
            print("\n" + "="*80)
            print("📄 GENERATED REPORT:")
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
    asyncio.run(show_report_sample())
