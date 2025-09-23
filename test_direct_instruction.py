#!/usr/bin/env python3
"""
Debug script to test direct instruction
"""

import asyncio
import json
import sys
import os

# Add the backend directory to the path
sys.path.append('backend')

from app.services.llm_client import LLMClient
from app.core.config import settings

async def test_direct_instruction():
    """Test direct instruction"""
    print("🔍 Testing Direct Instruction...")
    
    try:
        # Initialize the client
        client = LLMClient(
            azure_openai_api_key=settings.azure_openai_api_key,
            azure_openai_endpoint=settings.azure_openai_endpoint,
            azure_openai_deployment=settings.azure_openai_deployment
        )
        
        # Very direct prompt
        prompt = "Generate this exact JSON: {\"queries\": [\"5g ai\", \"5g machine learning\", \"5g artificial intelligence\"]}"
        
        print(f"📝 Prompt: {prompt}")
        print()
        
        # Test with different max_tokens
        for max_tokens in [50, 100, 200, 500]:
            print(f"🔢 Testing with max_tokens={max_tokens}")
            
            response = client.generate_text(
                prompt=prompt,
                system_message="You must respond with valid JSON only. No explanations, no reasoning, just the JSON.",
                max_tokens=max_tokens
            )
            
            print(f"📊 Response: {response}")
            
            if response.get("success"):
                text = response["text"]
                print(f"📄 Text: '{text}'")
                print(f"📏 Length: {len(text)}")
                
                if text.strip():
                    print("✅ Got content!")
                    break
                else:
                    print("❌ Still empty")
            else:
                print(f"❌ Failed: {response.get('error')}")
            
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_instruction())
