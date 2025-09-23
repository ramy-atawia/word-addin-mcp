#!/usr/bin/env python3
"""
Debug script to test report generation
"""

import asyncio
import json
import sys
import os

# Add the backend directory to the path
sys.path.append('backend')

from app.services.patent_search_service import PatentSearchService

async def test_report_generation():
    """Test report generation specifically"""
    print("🔍 Testing Report Generation...")
    
    try:
        # Initialize the service
        service = PatentSearchService()
        
        # Create mock patent data
        mock_patents = [
            {
                "patent_id": "12345678",
                "patent_title": "Test Patent 1",
                "patent_date": "2023-01-01",
                "patent_abstract": "Test abstract 1",
                "claims": [{"number": "1", "text": "Test claim 1"}],
                "inventors": [{"inventor_name_first": "John", "inventor_name_last": "Doe"}],
                "assignees": [{"assignee_organization": "Test Corp"}],
                "cpc_current": ["H04W1/00"]
            },
            {
                "patent_id": "87654321",
                "patent_title": "Test Patent 2",
                "patent_date": "2023-02-01",
                "patent_abstract": "Test abstract 2",
                "claims": [{"number": "1", "text": "Test claim 2"}],
                "inventors": [{"inventor_name_first": "Jane", "inventor_name_last": "Smith"}],
                "assignees": [{"assignee_organization": "Test Inc"}],
                "cpc_current": ["H04W2/00"]
            }
        ]
        
        mock_query_results = [
            {"query_text": "test query 1", "result_count": 1},
            {"query_text": "test query 2", "result_count": 1}
        ]
        
        print(f"📝 Testing with {len(mock_patents)} patents")
        print()
        
        # Test report generation directly
        try:
            report = await service._generate_report(
                query="5g ai",
                query_results=mock_query_results,
                patents=mock_patents,
                found_claims_summary="Test claims summary"
            )
            
            print(f"✅ Report generation successful")
            print(f"📏 Report length: {len(report)} characters")
            print(f"📄 Report preview: {report[:500]}...")
            
            if len(report) > 0:
                print("✅ Report contains content")
            else:
                print("❌ Report is empty")
                
        except Exception as e:
            print(f"❌ Report generation failed: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_report_generation())
