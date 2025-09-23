#!/usr/bin/env python3
"""
Debug script to test query generation prompt
"""

import asyncio
import json
import sys
import os

# Add the backend directory to the path
sys.path.append('backend')

from app.services.llm_client import LLMClient
from app.core.config import settings
from app.utils.prompt_loader import load_prompt_template

async def test_query_generation():
    """Test query generation prompt"""
    print("🔍 Testing Query Generation Prompt...")
    
    try:
        # Initialize the client
        client = LLMClient(
            azure_openai_api_key=settings.azure_openai_api_key,
            azure_openai_endpoint=settings.azure_openai_endpoint,
            azure_openai_deployment=settings.azure_openai_deployment
        )
        
        # Load the actual prompt
        prompt = load_prompt_template("patent_search_query_generation",
                                    query="5g ai",
                                    context="",
                                    conversation_history="")
        
        print(f"📝 Prompt loaded, length: {len(prompt)}")
        print(f"📄 Prompt preview: {prompt[:500]}...")
        print()
        
        # Test with the actual prompt
        response = client.generate_text(
            prompt=prompt,
            system_message="You are a patent search expert. Think like a domain expert and analyze query specificity iteratively.",
            max_tokens=2500
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
                    print(f"📊 Parsed data: {json.dumps(data, indent=2)}")
                    
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
    asyncio.run(test_query_generation())
