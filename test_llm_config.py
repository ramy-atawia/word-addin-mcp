#!/usr/bin/env python3
"""
Quick LLM Configuration Test
Tests if Azure OpenAI is properly configured
"""

import os
import sys
sys.path.append('/Users/Mariam/word-addin-mcp/backend')

from app.services.llm_client import LLMClient
from app.core.config import settings

def test_llm_config():
    print("🔍 Testing LLM Configuration")
    print("=" * 40)
    
    # Check environment variables
    print(f"AZURE_OPENAI_API_KEY: {'✅ Set' if os.getenv('AZURE_OPENAI_API_KEY') else '❌ Missing'}")
    print(f"AZURE_OPENAI_ENDPOINT: {'✅ Set' if os.getenv('AZURE_OPENAI_ENDPOINT') else '❌ Missing'}")
    print(f"AZURE_OPENAI_DEPLOYMENT: {'✅ Set' if os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME') else '❌ Missing'}")
    
    # Check settings
    print(f"\nSettings:")
    print(f"API Key: {'✅ Set' if settings.azure_openai_api_key else '❌ Missing'}")
    print(f"Endpoint: {'✅ Set' if settings.azure_openai_endpoint else '❌ Missing'}")
    print(f"Deployment: {settings.azure_openai_deployment}")
    print(f"API Version: {settings.azure_openai_api_version}")
    
    # Test LLM client
    print(f"\nTesting LLM Client:")
    try:
        llm_client = LLMClient(
            azure_openai_api_key=settings.azure_openai_api_key,
            azure_openai_endpoint=settings.azure_openai_endpoint,
            azure_openai_deployment=settings.azure_openai_deployment,
            azure_openai_api_version=settings.azure_openai_api_version
        )
        
        print(f"LLM Available: {'✅ Yes' if llm_client.llm_available else '❌ No'}")
        
        if llm_client.llm_available:
            print("Testing simple generation...")
            result = llm_client.generate_text(
                prompt="Hello, this is a test. Please respond with 'Test successful'.",
                max_tokens=50
            )
            
            if result.get("success"):
                print(f"✅ LLM Test Successful: {result.get('text', 'No text')}")
            else:
                print(f"❌ LLM Test Failed: {result.get('error', 'Unknown error')}")
        else:
            print("❌ LLM Client not available - check configuration")
            
    except Exception as e:
        print(f"❌ Error creating LLM client: {e}")

if __name__ == "__main__":
    test_llm_config()
