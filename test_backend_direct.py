#!/usr/bin/env python3
"""
Test backend directly without authentication
"""

import sys
import os
import json
import asyncio

# Add the backend to the path to get credentials
sys.path.insert(0, '/Users/Mariam/word-addin-mcp/backend')

from app.services.agent import AgentService

async def test_backend_direct():
    """Test backend directly without authentication."""
    print("🔍 Testing backend directly for patent search")
    print("=" * 60)
    
    try:
        # Create agent service
        agent_service = AgentService()
        print("✅ Agent service created")
        
        # Test the unified LangGraph agent
        print("🔍 Testing with 'prior art search 5G AI'...")
        
        result = await agent_service.process_user_message_unified_langgraph(
            user_message="prior art search 5G AI"
        )
        
        print("✅ Request completed!")
        print(f"📊 Result type: {type(result)}")
        
        if isinstance(result, dict):
            response_text = result.get("response", "")
            print(f"📏 Response length: {len(response_text)} characters")
            print(f"\n📄 REAL BACKEND RESPONSE:")
            print("="*80)
            print(response_text)
            print("="*80)
            
            # Check if it's a comprehensive report
            if "Comprehensive Prior Art Search Report" in response_text:
                print("\n✅ Generated comprehensive patent search report!")
            elif "patent" in response_text.lower():
                print("\n✅ Generated patent-related response!")
            else:
                print("\n❌ Response doesn't appear to be patent search related")
        else:
            print(f"❌ Result is not a dictionary: {result}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_backend_direct())
