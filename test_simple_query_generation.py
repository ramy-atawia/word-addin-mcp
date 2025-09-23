#!/usr/bin/env python3
"""
Debug script to test simplified query generation
"""

import asyncio
import json
import sys
import os

# Add the backend directory to the path
sys.path.append('backend')

from app.services.llm_client import LLMClient
from app.core.config import settings

async def test_simple_query_generation():
    """Test simplified query generation"""
    print("🔍 Testing Simplified Query Generation...")
    
    try:
        # Initialize the client
        client = LLMClient(
            azure_openai_api_key=settings.azure_openai_api_key,
            azure_openai_endpoint=settings.azure_openai_endpoint,
            azure_openai_deployment=settings.azure_openai_deployment
        )
        
        # Simple prompt
        simple_prompt = """Generate 3-5 PatentsView API queries for "5g ai" in this exact JSON format:

{
  "search_queries": [
    {
      "search_query": {"_text_all": {"patent_abstract": "5g ai"}},
      "reasoning": "Direct search for 5G AI patents",
      "expected_results": "100-200 patents"
    },
    {
      "search_query": {"_or": [{"_text_all": {"patent_abstract": "5g"}}, {"_text_all": {"patent_abstract": "artificial intelligence"}}]},
      "reasoning": "Search for 5G OR AI patents",
      "expected_results": "200-500 patents"
    },
    {
      "search_query": {"_and": [{"_text_all": {"patent_abstract": "5g"}}, {"_text_all": {"patent_abstract": "machine learning"}}]},
      "reasoning": "Search for 5G AND machine learning",
      "expected_results": "50-150 patents"
    }
  ]
}"""
        
        print(f"📝 Simple prompt length: {len(simple_prompt)}")
        print()
        
        # Test with simple prompt
        response = client.generate_text(
            prompt=simple_prompt,
            system_message="You are a patent search expert. Always respond with valid JSON in the exact format requested.",
            max_tokens=1000
        )
        
        print(f"📊 Response: {response}")
        print()
        
        if response.get("success"):
            text = response["text"]
            print(f"📄 Response Text: {text}")
            print(f"📏 Response Length: {len(text)}")
            
            if text.strip():
                print("✅ LLM returned non-empty response")
                
                # Try to parse as JSON
                try:
                    # Clean the text
                    if text.startswith("```json"):
                        text = text[7:-3]
                    elif text.startswith("```"):
                        text = text[3:-3]
                    
                    data = json.loads(text)
                    print("✅ JSON parsing successful")
                    print(f"📊 Number of queries: {len(data.get('search_queries', []))}")
                    
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing failed: {e}")
                    print(f"📄 Raw text: {text}")
            else:
                print("❌ LLM returned empty response")
        else:
            print(f"❌ LLM failed: {response.get('error')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_query_generation())
