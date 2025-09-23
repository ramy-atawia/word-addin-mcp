#!/usr/bin/env python3
"""
Debug script to test LLM client
"""

import asyncio
import json
import sys
import os

# Add the backend directory to the path
sys.path.append('backend')

from app.services.llm_client import LLMClient
from app.core.config import settings

async def test_llm_client():
    """Test LLM client directly"""
    print("🔍 Testing LLM Client...")
    
    try:
        # Initialize the client
        client = LLMClient(
            azure_openai_api_key=settings.azure_openai_api_key,
            azure_openai_endpoint=settings.azure_openai_endpoint,
            azure_openai_deployment=settings.azure_openai_deployment
        )
        
        print(f"✅ LLM Client initialized")
        print(f"📡 Endpoint: {settings.azure_openai_endpoint}")
        print(f"🤖 Deployment: {settings.azure_openai_deployment}")
        print()
        
        # Test simple prompt
        test_prompt = "Generate 3 search queries for '5g ai' in JSON format: {\"queries\": [\"query1\", \"query2\", \"query3\"]}"
        
        print(f"📝 Test Prompt: {test_prompt}")
        print()
        
        response = client.generate_text(
            prompt=test_prompt,
            system_message="You are a helpful assistant. Always respond with valid JSON.",
            max_tokens=500
        )
        
        print(f"📊 Response: {response}")
        print()
        
        if response.get("success"):
            text = response["text"]
            print(f"📄 Response Text: {text}")
            print(f"📏 Response Length: {len(text)}")
            
            if text.strip():
                print("✅ LLM returned non-empty response")
            else:
                print("❌ LLM returned empty response")
        else:
            print(f"❌ LLM failed: {response.get('error')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm_client())
