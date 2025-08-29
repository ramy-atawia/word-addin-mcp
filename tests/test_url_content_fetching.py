#!/usr/bin/env python3
"""
Test URL Content Fetching

This script tests whether the web_content_fetcher tool actually fetches
content from the URLs returned by Google search, or just shows snippets.
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.tools.web_content_fetcher import WebContentFetcherTool
from backend.app.core.mcp_tool_interface import ToolExecutionContext

async def test_url_content_fetching():
    """Test if the tool actually fetches content from URLs."""
    print("🔍 Testing URL Content Fetching")
    print("=" * 50)
    
    try:
        # Initialize the tool
        tool = WebContentFetcherTool()
        
        # Test 1: Direct URL fetching (LinkedIn profile)
        print("\n🧪 Test 1: Fetching LinkedIn Profile Content")
        print("-" * 40)
        
        linkedin_url = "https://ca.linkedin.com/in/ramyatawia"
        
        context = ToolExecutionContext(
            session_id="test_session",
            user_id="test_user",
            parameters={
                "url": linkedin_url,
                "extract_type": "text",
                "max_length": 2000
            }
        )
        
        result = await tool.execute(context)
        
        if result.status.value == "SUCCESS":
            print(f"✅ Success! Content fetched from LinkedIn")
            print(f"📊 Content Length: {len(result.data.get('content', ''))}")
            print(f"📝 Content Preview: {result.data.get('content', '')[:300]}...")
            print(f"🔗 URL: {result.data.get('url')}")
            print(f"⏱️  Extraction Time: {result.data.get('extraction_time')}s")
        else:
            print(f"❌ Failed: {result.error_message}")
        
        # Test 2: Search query with content extraction
        print("\n🧪 Test 2: Search Query with Content Extraction")
        print("-" * 40)
        
        context = ToolExecutionContext(
            session_id="test_session",
            user_id="test_user",
            parameters={
                "query": "Ramy Atawia LinkedIn profile",
                "extract_type": "summary",
                "max_length": 1500
            }
        )
        
        result = await tool.execute(context)
        
        if result.status.value == "SUCCESS":
            print(f"✅ Success! Search completed with content extraction")
            print(f"📊 Content Length: {len(result.data.get('content', ''))}")
            print(f"📝 Content Preview: {result.data.get('content', '')[:300]}...")
            print(f"🔗 Source Type: {result.data.get('source_type')}")
            print(f"🤖 AI Enhanced: {result.data.get('ai_enhanced')}")
            print(f"⏱️  Extraction Time: {result.data.get('extraction_time')}s")
        else:
            print(f"❌ Failed: {result.error_message}")
        
        # Test 3: Academic paper content
        print("\n🧪 Test 3: Fetching Academic Paper Content")
        print("-" * 40)
        
        arxiv_url = "https://arxiv.org/abs/2208.01793"
        
        context = ToolExecutionContext(
            session_id="test_session",
            user_id="test_user",
            parameters={
                "url": arxiv_url,
                "extract_type": "key_points",
                "max_length": 2000
            }
        )
        
        result = await tool.execute(context)
        
        if result.status.value == "SUCCESS":
            print(f"✅ Success! Academic paper content fetched")
            print(f"📊 Content Length: {len(result.data.get('content', ''))}")
            print(f"📝 Content Preview: {result.data.get('content', '')[:300]}...")
            print(f"🔗 URL: {result.data.get('url')}")
            print(f"🤖 AI Enhanced: {result.data.get('ai_enhanced')}")
            print(f"⏱️  Extraction Time: {result.data.get('extraction_time')}s")
        else:
            print(f"❌ Failed: {result.error_message}")
        
        print(f"\n🎉 Testing completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_url_content_fetching())
