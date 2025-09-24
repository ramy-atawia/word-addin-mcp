#!/usr/bin/env python3
"""
Debug the actual model configuration being used
"""

import sys
import os

# Add the backend to the path
sys.path.insert(0, '/Users/Mariam/word-addin-mcp/backend')

from app.core.config import settings
from app.services.llm_client import LLMClient

def debug_model_config():
    """Debug the model configuration."""
    print("🔍 Debugging Model Configuration")
    print("=" * 50)
    
    print(f"📊 Azure OpenAI API Key: {'✅ Set' if settings.azure_openai_api_key else '❌ Not set'}")
    print(f"📊 Azure OpenAI Endpoint: {settings.azure_openai_endpoint}")
    print(f"📊 Azure OpenAI Deployment: {settings.azure_openai_deployment}")
    print(f"📊 Azure OpenAI API Version: {settings.azure_openai_api_version}")
    
    # Create LLM client
    try:
        llm_client = LLMClient(
            azure_openai_api_key=settings.azure_openai_api_key,
            azure_openai_endpoint=settings.azure_openai_endpoint,
            azure_openai_deployment=settings.azure_openai_deployment
        )
        
        print(f"\n📊 LLM Client Model: {llm_client.azure_openai_deployment}")
        print(f"📊 LLM Client Available: {llm_client.llm_available}")
        print(f"📊 LLM Client Endpoint: {llm_client.azure_openai_endpoint}")
        
        # Test a simple LLM call
        print(f"\n🔍 Testing simple LLM call...")
        response = llm_client.generate_text("Hello, how are you?", max_tokens=50)
        
        print(f"📊 LLM Response Success: {response.get('success', False)}")
        print(f"📊 LLM Response Text Length: {len(response.get('text', ''))}")
        print(f"📊 LLM Response Model: {response.get('model', 'N/A')}")
        
        if response.get('text'):
            print(f"📄 LLM Response: {response['text']}")
            print("✅ LLM is generating text!")
        else:
            print("❌ LLM is not generating text")
            print(f"📄 Full Response: {response}")
            
    except Exception as e:
        print(f"❌ Error creating LLM client: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_model_config()
