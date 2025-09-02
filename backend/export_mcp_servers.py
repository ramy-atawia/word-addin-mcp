#!/usr/bin/env python3
"""
Script to export currently configured MCP servers from the running application.
This script fetches the current server configuration via the API and exports it to a JSON file.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
import httpx

async def export_mcp_servers(api_base_url: str = "https://localhost:9000", output_file: str = "exported_mcp_servers.json"):
    """Export MCP servers from the running application."""
    
    print("📤 Exporting MCP Servers from Running Application")
    print("=" * 55)
    
    try:
        # Create HTTP client with SSL verification disabled for localhost
        async with httpx.AsyncClient(verify=False) as client:
            
            # Fetch servers
            print("🔍 Fetching server list...")
            servers_response = await client.get(f"{api_base_url}/api/v1/mcp/external/servers")
            servers_response.raise_for_status()
            servers_data = servers_response.json()
            
            # Fetch tools
            print("🔍 Fetching tool list...")
            tools_response = await client.get(f"{api_base_url}/api/v1/mcp/tools")
            tools_response.raise_for_status()
            tools_data = tools_response.json()
            
    except Exception as e:
        print(f"❌ Error fetching data from API: {e}")
        return False
    
    # Process the data
    print("📊 Processing server and tool data...")
    
    # Create the export structure
    export_data = {
        "metadata": {
            "exported_at": datetime.now().isoformat(),
            "source": "Running Word Add-in MCP Application API",
            "api_base_url": api_base_url,
            "version": "1.0.0",
            "description": "Exported MCP servers and tools from running application"
        },
        "servers": {},
        "summary": {
            "total_servers": 0,
            "internal_servers": 0,
            "external_servers": 0,
            "total_tools": 0,
            "internal_tools": 0,
            "external_tools": 0,
            "healthy_servers": 0,
            "connected_servers": 0
        }
    }
    
    # Process servers
    if servers_data.get("status") == "success" and servers_data.get("servers"):
        for server_info in servers_data["servers"]:
            server_id = server_info["server_id"]
            server_name = server_info["name"]
            
            # Find tools for this server
            server_tools = []
            for tool in tools_data.get("tools", []):
                if tool.get("server_id") == server_id:
                    server_tools.append({
                        "name": tool["name"],
                        "description": tool["description"],
                        "category": tool.get("category", "general"),
                        "requires_auth": tool.get("requires_auth", False),
                        "usage_count": tool.get("usage_count", 0)
                    })
            
            # Add server to export
            export_data["servers"][server_name.lower().replace(" ", "_")] = {
                "name": server_name,
                "server_id": server_id,
                "type": "external",
                "url": server_info["url"],
                "status": server_info["status"],
                "connected": server_info["connected"],
                "last_health_check": server_info.get("last_health_check"),
                "authentication": {
                    "type": "none",
                    "required": False
                },
                "tools": server_tools
            }
            
            export_data["summary"]["external_servers"] += 1
            export_data["summary"]["external_tools"] += len(server_tools)
            
            if server_info["status"] == "healthy":
                export_data["summary"]["healthy_servers"] += 1
            if server_info["connected"]:
                export_data["summary"]["connected_servers"] += 1
    
    # Process internal tools
    internal_tools = []
    for tool in tools_data.get("tools", []):
        if tool.get("source") == "internal":
            internal_tools.append({
                "name": tool["name"],
                "description": tool["description"],
                "category": tool.get("category", "general"),
                "requires_auth": tool.get("requires_auth", False),
                "usage_count": tool.get("usage_count", 0)
            })
    
    if internal_tools:
        export_data["servers"]["internal"] = {
            "name": "Internal MCP Server",
            "server_id": "internal",
            "type": "internal",
            "url": "localhost:9000",
            "status": "healthy",
            "connected": True,
            "tools": internal_tools
        }
        export_data["summary"]["internal_servers"] = 1
        export_data["summary"]["internal_tools"] = len(internal_tools)
        export_data["summary"]["healthy_servers"] += 1
        export_data["summary"]["connected_servers"] += 1
    
    # Update summary
    export_data["summary"]["total_servers"] = export_data["summary"]["internal_servers"] + export_data["summary"]["external_servers"]
    export_data["summary"]["total_tools"] = export_data["summary"]["internal_tools"] + export_data["summary"]["external_tools"]
    
    # Add Cursor MCP config format
    export_data["cursor_mcp_config"] = {
        "mcpServers": {}
    }
    
    for server_name, server_config in export_data["servers"].items():
        if server_config["type"] == "external":
            export_data["cursor_mcp_config"]["mcpServers"][server_name] = {
                "transport": "http",
                "url": server_config["url"],
                "headers": {
                    "Content-Type": "application/json"
                }
            }
    
    # Write to file
    output_path = Path(output_file)
    try:
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✅ Successfully exported to: {output_file}")
        print(f"📊 Exported {export_data['summary']['total_servers']} servers with {export_data['summary']['total_tools']} tools")
        
        return True
        
    except Exception as e:
        print(f"❌ Error writing export file: {e}")
        return False

async def main():
    """Main function."""
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "export":
            api_url = sys.argv[2] if len(sys.argv) > 2 else "https://localhost:9000"
            output_file = sys.argv[3] if len(sys.argv) > 3 else "exported_mcp_servers.json"
            success = await export_mcp_servers(api_url, output_file)
            sys.exit(0 if success else 1)
            
        elif command == "help":
            print("Usage:")
            print("  python export_mcp_servers.py export [api_url] [output_file]  - Export servers from API")
            print("  python export_mcp_servers.py help                           - Show this help")
            print()
            print("Examples:")
            print("  python export_mcp_servers.py export")
            print("  python export_mcp_servers.py export https://localhost:9000 my_servers.json")
            sys.exit(0)
            
        else:
            print(f"Unknown command: {command}")
            print("Use 'help' for usage information")
            sys.exit(1)
    else:
        # Default: export from localhost:9000
        success = await export_mcp_servers()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
