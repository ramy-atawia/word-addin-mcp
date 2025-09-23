#!/usr/bin/env python3
"""
Debug script to test raw LLM response
"""

import asyncio
import json
import sys
import os

# Add the backend directory to the path
sys.path.append('backend')

from app.services.llm_client import LLMClient
from app.core.config import settings

async def test_raw_response():
    """Test raw LLM response"""
    print("🔍 Testing Raw LLM Response...")
    
    try:
        # Initialize the client
        client = LLMClient(
            azure_openai_api_key=settings.azure_openai_api_key,
            azure_openai_endpoint=settings.azure_openai_endpoint,
            azure_openai_deployment=settings.azure_openai_deployment
        )
        
        # Simple prompt
        prompt = "Say hello world"
        
        print(f"📝 Prompt: {prompt}")
        print()
        
        # Make direct API call to see raw response
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
        
        response = client.client.chat.completions.create(
            model=client.azure_deployment,
            messages=messages,
            max_completion_tokens=100
        )
        
        print(f"📊 Raw Response Type: {type(response)}")
        print(f"📊 Response Choices: {response.choices}")
        print(f"📊 Number of Choices: {len(response.choices)}")
        
        if response.choices:
            choice = response.choices[0]
            print(f"📊 Choice Type: {type(choice)}")
            print(f"📊 Choice Message: {choice.message}")
            print(f"📊 Choice Message Content: {choice.message.content}")
            print(f"📊 Choice Message Content Type: {type(choice.message.content)}")
            print(f"📊 Choice Message Content Length: {len(choice.message.content) if choice.message.content else 0}")
            
            if choice.message.content is None:
                print("❌ Content is None - this indicates content filtering")
            elif choice.message.content == "":
                print("❌ Content is empty string")
            else:
                print("✅ Content is present")
        
        print(f"📊 Usage: {response.usage}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_raw_response())
