#!/usr/bin/env python3
"""
Direct test of Azure OpenAI with gpt-5-nano using backend credentials
"""

import sys
import os
from openai import AzureOpenAI

# Add the backend to the path to get credentials
sys.path.insert(0, '/Users/Mariam/word-addin-mcp/backend')

from app.core.config import settings

def test_gpt5_nano_direct():
    """Test gpt-5-nano directly with Azure OpenAI using backend credentials."""
    print("🔍 Testing Azure OpenAI gpt-5-nano directly with backend credentials")
    print("=" * 70)
    
    # Get credentials from backend config
    api_key = settings.azure_openai_api_key
    endpoint = settings.azure_openai_endpoint
    deployment = "gpt-5-nano"
    
    print(f"📊 API Key: {'✅ Set' if api_key else '❌ Not set'}")
    print(f"📊 Endpoint: {endpoint}")
    print(f"📊 Deployment: {deployment}")
    
    if not api_key or not endpoint:
        print("❌ Missing credentials")
        return
    
    try:
        # Create client
        client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version="2024-12-01-preview"
        )
        
        print("✅ Azure OpenAI client created")
        
        # Test simple prompt
        print("\n🔍 Testing simple prompt...")
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "user", "content": "Hello, how are you?"}
            ],
            max_completion_tokens=100
        )
        
        print("✅ Response received!")
        print(f"📊 Response type: {type(response)}")
        print(f"📊 Choices count: {len(response.choices)}")
        
        if response.choices:
            choice = response.choices[0]
            message = choice.message
            content = message.content
            
            print(f"📊 Message content: {repr(content)}")
            print(f"📊 Content length: {len(content) if content else 0}")
            print(f"📊 Finish reason: {choice.finish_reason}")
            
            if content:
                print(f"📄 Content: {content}")
                print("✅ gpt-5-nano is generating text!")
            else:
                print("❌ gpt-5-nano is not generating text")
        
        # Test usage
        if hasattr(response, 'usage') and response.usage:
            usage = response.usage
            print(f"\n📊 Usage:")
            print(f"  - Prompt tokens: {usage.prompt_tokens}")
            print(f"  - Completion tokens: {usage.completion_tokens}")
            print(f"  - Total tokens: {usage.total_tokens}")
            
            # Check for reasoning tokens
            if hasattr(usage, 'completion_tokens_details'):
                details = usage.completion_tokens_details
                if hasattr(details, 'reasoning_tokens'):
                    print(f"  - Reasoning tokens: {details.reasoning_tokens}")
        
        # Test with a more complex prompt
        print("\n🔍 Testing complex prompt...")
        response2 = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "user", "content": "Write a short paragraph about 5G technology and AI integration."}
            ],
            max_completion_tokens=200
        )
        
        if response2.choices:
            choice2 = response2.choices[0]
            content2 = choice2.message.content
            print(f"📊 Complex prompt content: {repr(content2)}")
            print(f"📊 Complex prompt length: {len(content2) if content2 else 0}")
            
            if content2:
                print(f"📄 Complex content: {content2}")
                print("✅ gpt-5-nano can handle complex prompts!")
            else:
                print("❌ gpt-5-nano cannot handle complex prompts")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gpt5_nano_direct()
