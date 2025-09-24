#!/usr/bin/env python3
"""
Debug the LLM response in report generation.
"""

import asyncio
import sys
import os
import json

# Add the backend to the path
sys.path.insert(0, '/Users/Mariam/word-addin-mcp/backend')

from app.services.patent_search_service import PatentSearchService
from app.utils.prompt_loader import load_prompt_template

async def debug_llm_response():
    """Debug the LLM response step by step."""
    print("🔍 Debugging LLM Response...")
    
    try:
        # Create the service instance
        service = PatentSearchService()
        print("✅ Service created")
        
        # Test loading prompts
        print("🔍 Testing prompt loading...")
        try:
            system_prompt = load_prompt_template("prior_art_search_system")
            print(f"✅ System prompt loaded: {len(system_prompt)} chars")
            print(f"📄 System prompt preview: {system_prompt[:200]}...")
        except Exception as e:
            print(f"❌ System prompt loading failed: {e}")
            return
        
        try:
            user_prompt = load_prompt_template("prior_art_search_simple",
                                              user_query="5g ai",
                                              conversation_context="Test context",
                                              document_reference="Test patents")
            print(f"✅ User prompt loaded: {len(user_prompt)} chars")
            print(f"📄 User prompt preview: {user_prompt[:300]}...")
        except Exception as e:
            print(f"❌ User prompt loading failed: {e}")
            return
        
        # Test LLM call directly
        print("🔍 Testing LLM call...")
        try:
            response = service.llm_client.generate_text(
                prompt=user_prompt,
                system_message=system_prompt,
                max_tokens=6000
            )
            
            print(f"✅ LLM response received")
            print(f"📊 Response type: {type(response)}")
            print(f"📊 Response keys: {response.keys() if isinstance(response, dict) else 'N/A'}")
            
            if isinstance(response, dict):
                success = response.get("success", False)
                print(f"📊 Success: {success}")
                
                if success:
                    text = response.get("text", "")
                    print(f"📏 Text length: {len(text)}")
                    if text:
                        print(f"📄 Text preview: {text[:300]}...")
                    else:
                        print("❌ Empty text in response")
                else:
                    error = response.get("error", "Unknown error")
                    print(f"❌ LLM error: {error}")
            else:
                print(f"❌ Unexpected response type: {type(response)}")
                print(f"Response: {response}")
                
        except Exception as e:
            print(f"❌ LLM call failed: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Error during debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_llm_response())
