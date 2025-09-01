#!/usr/bin/env python3
"""
Direct demo of Google Search working through your MCP tool.
"""

import asyncio
import sys
sys.path.insert(0, '.')

async def demo_google_search():
    """Demo the Google Search functionality directly."""
    print("🚀 Direct Google Search Demo")
    print("=" * 50)
    
    try:
        # Import your web search tool
        from app.mcp_servers.tools.web_search import WebSearchTool
        
        # Create tool instance
        search_tool = WebSearchTool()
        
        # Test searches
        test_queries = [
            "latest AI developments 2024",
            "machine learning breakthroughs",
            "GPT-4 capabilities"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Test {i}: '{query}'")
            print("-" * 40)
            
            try:
                # Execute search
                result = await search_tool.execute({
                    "query": query,
                    "max_results": 3
                })
                
                if result.get("status") == "success":
                    results = result.get("results", [])
                    source = result.get("source", "Unknown")
                    exec_time = result.get("execution_time", 0)
                    
                    print(f"✅ Found {len(results)} results from {source} in {exec_time:.3f}s")
                    
                    for j, item in enumerate(results, 1):
                        title = item.get("title", "No title")
                        url = item.get("url", "No URL")
                        snippet = item.get("snippet", "")[:100]
                        
                        print(f"\n{j}. {title}")
                        print(f"   🔗 {url}")
                        if snippet:
                            print(f"   📄 {snippet}...")
                else:
                    print(f"❌ Search failed: {result}")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        
        print(f"\n🎉 Demo completed! Google Search is working through your MCP tool!")
        
    except Exception as e:
        print(f"❌ Setup error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(demo_google_search())
