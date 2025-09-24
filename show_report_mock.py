#!/usr/bin/env python3
"""
Show a sample report using mock data to bypass query generation issues
"""

import sys
import os
import json
import asyncio

# Add the backend to the path to get credentials
sys.path.insert(0, '/Users/Mariam/word-addin-mcp/backend')

from app.services.patent_search_service import PatentSearchService
from app.utils.prompt_loader import load_prompt_template

async def show_report_mock():
    """Show a sample report using mock data."""
    print("🔍 Generating patent search report sample with mock data")
    print("=" * 60)
    
    try:
        # Create service
        service = PatentSearchService()
        print("✅ PatentSearchService created")
        
        # Mock patent data (realistic but smaller)
        mock_patent_summaries = [
            {
                "id": "12345678",
                "title": "Method and apparatus for 5G network optimization using artificial intelligence",
                "date": "2023-01-15",
                "abstract": "A system and method for optimizing 5G network performance using machine learning algorithms to predict and adjust network parameters in real-time, including transmission power, beamforming angles, and resource allocation.",
                "claims_count": 15,
                "claims_info": ["Claim 1 (independent)", "Claim 2 (dependent)", "Claim 3 (dependent)"],
                "inventor": "John Smith",
                "assignee": "Tech Corp",
                "cpc_codes": ["H04W24/02", "G06N3/08"],
                "is_top_patent": True,
                "rank": 1
            },
            {
                "id": "87654321",
                "title": "AI-driven handover management in 5G networks",
                "date": "2023-03-20",
                "abstract": "An intelligent handover management system for 5G networks that uses artificial intelligence to predict optimal handover timing and target cells based on historical data and real-time network conditions.",
                "claims_count": 12,
                "claims_info": ["Claim 1 (independent)", "Claim 2 (dependent)"],
                "inventor": "Jane Doe",
                "assignee": "Wireless Inc",
                "cpc_codes": ["H04W36/00", "G06N20/00"],
                "is_top_patent": True,
                "rank": 2
            },
            {
                "id": "11223344",
                "title": "Machine learning-based spectrum allocation in 5G networks",
                "date": "2023-05-10",
                "abstract": "A dynamic spectrum allocation system that uses machine learning to optimize frequency band assignment in 5G networks, improving spectral efficiency and reducing interference.",
                "claims_count": 8,
                "claims_info": ["Claim 1 (independent)", "Claim 2 (dependent)", "Claim 3 (dependent)"],
                "inventor": "Bob Johnson",
                "assignee": "Spectrum Corp",
                "cpc_codes": ["H04W72/04", "G06N20/00"],
                "is_top_patent": True,
                "rank": 3
            }
        ]
        
        mock_claims_summary = """
**Patent 12345678: Method and apparatus for 5G network optimization using artificial intelligence**
- Technical Summary: This patent describes a comprehensive system for optimizing 5G network performance using machine learning algorithms to predict and adjust network parameters in real-time.
- Key Technical Features: Neural network-based analysis, real-time parameter adjustment, network performance prediction, adaptive algorithms
- Claim Structure: Independent claim 1 covers the core optimization method, with dependent claims covering specific implementations and edge cases
- Technical Scope: Broad coverage of AI-based 5G optimization with specific focus on machine learning algorithms and real-time adaptation

**Patent 87654321: AI-driven handover management in 5G networks**
- Technical Summary: An intelligent handover management system that uses AI to predict optimal handover timing and target cells in 5G networks based on historical patterns and current conditions.
- Key Technical Features: AI prediction module, decision engine, handover execution unit, historical data analysis, real-time decision making
- Claim Structure: Independent claim 1 covers the system architecture, with dependent claims covering specific AI implementations and handover scenarios
- Technical Scope: Focused on handover management with AI integration for improved network performance and reduced handover failures

**Patent 11223344: Machine learning-based spectrum allocation in 5G networks**
- Technical Summary: A dynamic spectrum allocation system that uses machine learning to optimize frequency band assignment in 5G networks, improving spectral efficiency and reducing interference.
- Key Technical Features: ML-based spectrum prediction, dynamic allocation algorithms, interference mitigation, efficiency optimization
- Claim Structure: Independent claim 1 covers the spectrum allocation method, with dependent claims covering specific ML techniques and optimization criteria
- Technical Scope: Focused on spectrum management with machine learning for improved network efficiency and reduced interference
"""
        
        mock_query_summary = """
  - Query 1: 5G network AI → 15 patents
  - Query 2: AI in 5G networks → 12 patents
  - Query 3: 5G optimization machine learning → 8 patents
  - Query 4: 5G handover AI → 5 patents
"""
        
        print("✅ Mock data created")
        
        # Prepare the report generation
        patent_json = json.dumps(mock_patent_summaries, indent=2)
        document_reference = f"Patents Found:\n{patent_json}\n\n**Detailed Claims Analysis:**\n{mock_claims_summary}"
        
        user_prompt = load_prompt_template("prior_art_search_simple",
                                          user_query="5G AI",
                                          conversation_context=f"Search Queries Used (with result counts):\n{mock_query_summary}",
                                          document_reference=document_reference)
        
        system_prompt = load_prompt_template("prior_art_search_system")
        
        print(f"📊 Prompt size: {len(user_prompt) + len(system_prompt)} characters")
        
        # Generate the report
        print("🔍 Generating report...")
        response = service.report_llm_client.generate_text(
            prompt=user_prompt,
            system_message=system_prompt,
            max_tokens=6000
        )
        
        if response.get('success') and response.get('text'):
            report = response['text']
            print(f"\n📏 Report length: {len(report)} characters")
            print("\n" + "="*80)
            print("📄 GENERATED REPORT:")
            print("="*80)
            print(report)
            print("="*80)
        else:
            print("❌ Report generation failed")
            print(f"📊 Response: {response}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(show_report_mock())
