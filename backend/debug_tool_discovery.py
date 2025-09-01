#!/usr/bin/env python3
"""
Debug script to trace the tool discovery chain.
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

async def debug_tool_discovery():
    """Debug the tool discovery chain."""
    print("🔍 Debugging Tool Discovery Chain...")
    
    try:
        # 1. Check internal tool registry directly
        print("\n1️⃣ Checking Internal Tool Registry...")
        from app.mcp_servers.tool_registry import InternalToolRegistry
        tr = InternalToolRegistry()
        print(f"   Tools in registry: {[t.name for t in tr.tools.values()]}")
        
        # 2. Check internal MCP server
        print("\n2️⃣ Checking Internal MCP Server...")
        from app.mcp_servers.internal_server import internal_mcp_server
        tools_data = await internal_mcp_server.tool_registry.list_all_tools()
        print(f"   Tools from internal server: {[t.get('name') for t in tools_data]}")
        
        # 3. Check server registry
        print("\n3️⃣ Checking Server Registry...")
        from app.services.mcp.server_registry import MCPServerRegistry
        server_registry = MCPServerRegistry()
        await server_registry.initialize()
        
        # Check what servers are registered
        print(f"   Registered servers: {list(server_registry.servers.keys())}")
        
        # Check tools from server registry
        all_tools = await server_registry.list_all_tools()
        print(f"   Tools from server registry: {[t.name for t in all_tools]}")
        print(f"   Tool sources: {[t.source for t in all_tools]}")
        
        # 4. Check orchestrator
        print("\n4️⃣ Checking MCP Orchestrator...")
        from app.services.mcp.orchestrator import get_initialized_mcp_orchestrator
        try:
            mcp_orchestrator = get_initialized_mcp_orchestrator()
            tools_data = await mcp_orchestrator.list_all_tools()
            print(f"   Tools from orchestrator: {[t.get('name') for t in tools_data.get('tools', [])]}")
            print(f"   Tool sources: {[t.get('source') for t in tools_data.get('tools', [])]}")
        except Exception as e:
            print(f"   Orchestrator error: {str(e)}")
        
        # 5. Check if there's an old MCP hub
        print("\n5️⃣ Checking for Old MCP Hub...")
        try:
            from app.core.mcp_hub import mcp_hub
            print(f"   Old MCP hub exists: {mcp_hub is not None}")
            if mcp_hub:
                tools_data = await mcp_hub.list_all_tools()
                print(f"   Tools from old hub: {[t.get('name') for t in tools_data.get('tools', [])]}")
        except ImportError:
            print("   Old MCP hub not found")
        except Exception as e:
            print(f"   Old MCP hub error: {str(e)}")
            
    except Exception as e:
        print(f"❌ Debug failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Tool Discovery Debug...")
    asyncio.run(debug_tool_discovery())
