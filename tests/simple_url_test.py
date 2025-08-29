#!/usr/bin/env python3
"""
Simple URL Test

Basic test to see what's happening with URL fetching.
"""

import asyncio
import os
import sys

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.tools.web_content_fetcher import WebContentFetcherTool
from backend.app.core.mcp_tool_interface import ToolExecutionContext

async def simple_test():
    """Simple test of URL fetching."""
    print("🧪 Simple URL Test")
    print("=" * 30)
    
    try:
        # Initialize the tool
        tool = WebContentFetcherTool()
        print("✅ Tool initialized")
        
        # Test with a simple URL
        context = ToolExecutionContext(
            session_id="test_session",
            user_id="test_user",
            parameters={
                "url": "https://httpbin.org/get",
                "extract_type": "text",
                "max_length": 1000
            }
        )
        
        print("🔍 Executing tool...")
        result = await tool.execute(context)
        
        print(f"📊 Result status: {result.status}")
        print(f"📊 Result data: {result.data}")
        
        if hasattr(result, 'error_message'):
            print(f"❌ Error message: {result.error_message}")
        
        if hasattr(result, 'error_code'):
            print(f"❌ Error code: {result.error_code}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_test())
