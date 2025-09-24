#!/usr/bin/env python3
"""
Debug the raw LLM response to see what's actually being returned.
"""

import asyncio
import sys
import os

# Add the backend to the path
sys.path.insert(0, '/Users/Mariam/word-addin-mcp/backend')

from app.services.llm_client import LLMClient
from app.core.config import settings

async def debug_raw_llm():
    """Debug the raw LLM response."""
    print("🔍 Debugging Raw LLM Response...")
    
    try:
        # Create LLM client directly
        llm_client = LLMClient(
            azure_openai_api_key=settings.azure_openai_api_key,
            azure_openai_endpoint=settings.azure_openai_endpoint,
            azure_openai_deployment=settings.azure_openai_deployment
        )
        
        print("✅ LLM client created")
        print(f"📊 Model: {llm_client.azure_openai_deployment}")
        print(f"📊 Endpoint: {llm_client.azure_openai_endpoint}")
        print(f"📊 Available: {llm_client.llm_available}")
        
        if not llm_client.llm_available:
            print("❌ LLM not available")
            return
        
        # Test with a very simple prompt
        print("🔍 Testing simple prompt...")
        simple_prompt = "Hello, how are you?"
        
        # Make the API call directly to see raw response
        messages = [{"role": "user", "content": simple_prompt}]
        
        print("🔍 Making direct API call...")
        response = llm_client.client.chat.completions.create(
            model=llm_client.azure_openai_deployment,
            messages=messages,
            max_completion_tokens=100
        )
        
        print(f"✅ Raw response received")
        print(f"📊 Response type: {type(response)}")
        print(f"📊 Response attributes: {dir(response)}")
        
        if hasattr(response, 'choices'):
            print(f"📊 Choices count: {len(response.choices)}")
            if response.choices:
                choice = response.choices[0]
                print(f"📊 Choice type: {type(choice)}")
                print(f"📊 Choice attributes: {dir(choice)}")
                
                if hasattr(choice, 'message'):
                    message = choice.message
                    print(f"📊 Message type: {type(message)}")
                    print(f"📊 Message attributes: {dir(message)}")
                    print(f"📊 Message content: {repr(message.content)}")
                    print(f"📊 Message content type: {type(message.content)}")
                    print(f"📊 Message role: {message.role}")
                    
                    if hasattr(message, 'finish_reason'):
                        print(f"📊 Finish reason: {message.finish_reason}")
        
        if hasattr(response, 'usage'):
            usage = response.usage
            print(f"📊 Usage: {usage}")
            if usage:
                print(f"📊 Prompt tokens: {usage.prompt_tokens}")
                print(f"📊 Completion tokens: {usage.completion_tokens}")
                print(f"📊 Total tokens: {usage.total_tokens}")
        
        # Test the generate_text method
        print("\n🔍 Testing generate_text method...")
        result = llm_client.generate_text(simple_prompt, max_tokens=100)
        print(f"📊 Result: {result}")
        
    except Exception as e:
        print(f"❌ Error during debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_raw_llm())
