#!/usr/bin/env python3
"""
Simple test script for prior art search with "prior art search 5G ai"
"""

import asyncio
import sys
import os
import json

# Add the backend to the path
sys.path.insert(0, '/Users/Mariam/word-addin-mcp/backend')

from app.services.agent import AgentService

async def test_prior_art_search():
    """Test prior art search with a simple request."""
    print("🔍 Testing Prior Art Search: 'prior art search 5G ai'")
    print("=" * 60)
    
    try:
        # Create agent service
        agent_service = AgentService()
        print("✅ Agent service created")
        
        # Test the unified LangGraph agent
        print("🔍 Testing unified LangGraph agent...")
        
        result = await agent_service.process_user_message_unified_langgraph(
            user_message="prior art search 5G ai"
        )
        
        print("✅ Request completed!")
        print(f"📊 Result type: {type(result)}")
        
        if isinstance(result, dict):
            print(f"📊 Result keys: {list(result.keys())}")
            
            if 'response' in result:
                response = result['response']
                print(f"📏 Response length: {len(response) if isinstance(response, str) else 'N/A'}")
                
                if isinstance(response, str) and response:
                    print(f"\n📄 Response preview (first 500 chars):")
                    print("-" * 50)
                    print(response[:500])
                    if len(response) > 500:
                        print("... [truncated]")
                    print("-" * 50)
                    
                    # Check if it looks like a comprehensive report
                    if any(keyword in response.lower() for keyword in 
                           ['executive summary', 'patent', 'analysis', 'findings', 'recommendations']):
                        print("✅ Response appears to be a comprehensive report!")
                    else:
                        print("❌ Response appears to be basic/generic")
                else:
                    print("❌ Empty or invalid response")
            else:
                print(f"❌ No 'response' key in result")
                print(f"📄 Full result: {result}")
        else:
            print(f"❌ Unexpected result type: {type(result)}")
            print(f"📄 Result: {result}")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_prior_art_search())
