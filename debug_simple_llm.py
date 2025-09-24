#!/usr/bin/env python3
"""
Debug with a simple LLM call to see if the issue is with the prompt or the LLM.
"""

import asyncio
import sys
import os

# Add the backend to the path
sys.path.insert(0, '/Users/Mariam/word-addin-mcp/backend')

from app.services.patent_search_service import PatentSearchService

async def debug_simple_llm():
    """Debug with a simple LLM call."""
    print("🔍 Debugging Simple LLM Call...")
    
    try:
        # Create the service instance
        service = PatentSearchService()
        print("✅ Service created")
        
        # Test with a very simple prompt
        print("🔍 Testing simple prompt...")
        simple_prompt = "Write a short paragraph about 5G technology."
        
        response = service.llm_client.generate_text(
            prompt=simple_prompt,
            max_tokens=100
        )
        
        print(f"✅ Simple LLM response received")
        print(f"📊 Response type: {type(response)}")
        print(f"📊 Success: {response.get('success', False)}")
        print(f"📏 Text length: {len(response.get('text', ''))}")
        
        if response.get('text'):
            print(f"📄 Text: {response['text']}")
        else:
            print("❌ No text in simple response")
            print(f"📊 Full response: {response}")
        
        # Test with a slightly more complex prompt
        print("\n🔍 Testing medium prompt...")
        medium_prompt = """Generate a brief prior art search report for 5G AI technology.

Include:
1. Executive Summary
2. Key findings
3. Recommendations

Keep it concise but informative."""

        response2 = service.llm_client.generate_text(
            prompt=medium_prompt,
            max_tokens=500
        )
        
        print(f"✅ Medium LLM response received")
        print(f"📊 Response type: {type(response2)}")
        print(f"📊 Success: {response2.get('success', False)}")
        print(f"📏 Text length: {len(response2.get('text', ''))}")
        
        if response2.get('text'):
            print(f"📄 Text preview: {response2['text'][:300]}...")
        else:
            print("❌ No text in medium response")
            print(f"📊 Full response: {response2}")
            
    except Exception as e:
        print(f"❌ Error during debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_simple_llm())
