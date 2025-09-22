#!/usr/bin/env python3
"""
Test script to analyze prompting for invention disclosure drafting.
"""

import requests
import json
import time

def test_invention_disclosure_prompting():
    """Test how the system handles invention disclosure drafting requests."""
    
    base_url = "http://localhost:9000"
    
    print("🔍 Testing Invention Disclosure Prompting...")
    print("=" * 60)
    
    # Test data
    test_cases = [
        {
            "name": "Simple invention disclosure request",
            "message": "draft an invention disclosure",
            "context": {
                "document_content": "",
                "chat_history": "",
                "available_tools": "web_search_tool,prior_art_search_tool,claim_drafting_tool,claim_analysis_tool"
            }
        },
        {
            "name": "Detailed invention disclosure request",
            "message": "draft an invention disclosure for a new AI-powered patent search system",
            "context": {
                "document_content": "We have developed a novel AI system that uses machine learning to improve patent search accuracy by 40%.",
                "chat_history": "",
                "available_tools": "web_search_tool,prior_art_search_tool,claim_drafting_tool,claim_analysis_tool"
            }
        },
        {
            "name": "Invention disclosure with context",
            "message": "I need to draft an invention disclosure for my blockchain-based voting system",
            "context": {
                "document_content": "The system uses blockchain technology to ensure secure, transparent, and tamper-proof voting in elections.",
                "chat_history": "User: What are the key components of a patent application?\nAI: A patent application typically includes...",
                "available_tools": "web_search_tool,prior_art_search_tool,claim_drafting_tool,claim_analysis_tool"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 40)
        print(f"Input: {test_case['message']}")
        print(f"Context: {test_case['context']['document_content'][:100]}...")
        
        try:
            # Test the agent chat endpoint
            response = requests.post(
                f"{base_url}/api/v1/mcp/agent/chat",
                json={
                    "message": test_case['message'],
                    "context": test_case['context'],
                    "session_id": f"test_session_{i}"
                },
                headers={
                    "Authorization": "Bearer test_token",  # This will fail auth, but we can see the response
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 401:
                print("✅ Endpoint properly protected (requires authentication)")
            elif response.status_code == 200:
                result = response.json()
                print("Response received:")
                print(f"  Success: {result.get('success', 'N/A')}")
                print(f"  Intent: {result.get('intent_type', 'N/A')}")
                print(f"  Tool: {result.get('tool_name', 'N/A')}")
                print(f"  Response: {result.get('response', 'N/A')[:200]}...")
            else:
                print(f"Unexpected status: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Prompting Analysis:")
    print("   - Test how the system interprets invention disclosure requests")
    print("   - Check if it routes to appropriate tools")
    print("   - Analyze the quality of responses")

if __name__ == "__main__":
    test_invention_disclosure_prompting()
