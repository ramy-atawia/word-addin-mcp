#!/usr/bin/env python3
"""
Debug Script: Google API Diagnostics

This script helps debug Google Custom Search API issues by:
1. Testing direct API calls
2. Checking response status and content
3. Verifying configuration
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.services.web_search_service import WebSearchService

async def debug_google_api():
    """Debug Google API configuration and responses."""
    print("🔍 Google API Debug Session")
    print("=" * 50)
    
    # Check environment variables
    google_api_key = os.getenv('GOOGLE_API_KEY')
    google_cse_id = os.getenv('GOOGLE_CSE_ID')
    
    print(f"🔑 Google API Key: {'*' * (len(google_api_key) - 4) + google_api_key[-4:] if google_api_key else 'NOT SET'}")
    print(f"🔑 Google CSE ID: {'*' * (len(google_cse_id) - 4) + google_cse_id[-4:] if google_cse_id else 'NOT SET'}")
    
    if not google_api_key or not google_cse_id:
        print("❌ Missing required environment variables")
        return
    
    # Test direct API call
    print(f"\n🧪 Testing direct Google API call...")
    
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        # Test query
        test_query = "Ramy Atawia"
        api_url = "https://www.googleapis.com/customsearch/v1"
        
        params = {
            "key": google_api_key,
            "cx": google_cse_id,
            "q": test_query,
            "num": 5
        }
        
        print(f"🔗 API URL: {api_url}")
        print(f"📝 Query: {test_query}")
        print(f"⚙️  Parameters: {json.dumps(params, indent=2)}")
        
        try:
            async with session.get(api_url, params=params) as response:
                print(f"\n📡 Response Status: {response.status}")
                print(f"📡 Response Headers: {dict(response.headers)}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"\n✅ API Response:")
                    print(f"   Response Keys: {list(data.keys())}")
                    
                    if 'items' in data:
                        items = data['items']
                        print(f"   Items Count: {len(items)}")
                        
                        if items:
                            print(f"\n📋 First Result:")
                            first_item = items[0]
                            for key, value in first_item.items():
                                if key == 'snippet' and len(str(value)) > 100:
                                    print(f"   {key}: {str(value)[:100]}...")
                                else:
                                    print(f"   {key}: {value}")
                        else:
                            print("   ❌ No items in response")
                    else:
                        print(f"   ❌ No 'items' key in response")
                        print(f"   📄 Full Response: {json.dumps(data, indent=2)}")
                        
                else:
                    error_text = await response.text()
                    print(f"❌ API Error Response:")
                    print(f"   Status: {response.status}")
                    print(f"   Error: {error_text}")
                    
        except Exception as e:
            print(f"❌ Exception during API call: {str(e)}")
    
    # Test the web search service
    print(f"\n🧪 Testing WebSearchService...")
    try:
        web_search_service = WebSearchService()
        
        # Test with async context manager
        async with web_search_service as service:
            print("✅ WebSearchService initialized successfully")
            
            # Test search
            results = await service.search_google("Ramy Atawia", max_results=5, include_abstracts=True)
            print(f"📊 Search Results Count: {len(results)}")
            
            if results:
                print(f"📋 First Result:")
                first_result = results[0]
                for key, value in first_result.items():
                    if key == 'snippet' and len(str(value)) > 100:
                        print(f"   {key}: {str(value)[:100]}...")
                    else:
                        print(f"   {key}: {value}")
            else:
                print("❌ No results from WebSearchService")
                
    except Exception as e:
        print(f"❌ WebSearchService error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_google_api())
