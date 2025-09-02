#!/usr/bin/env python3
"""
Script to restore MCP servers from the configured_mcp_servers.json file.
This script can be used to restore all the currently configured MCP servers
to a fresh instance of the application.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.services.mcp.server_registry import get_global_registry
from app.core.fastmcp_client import MCPConnectionError, MCPToolError

async def restore_mcp_servers(config_file: str = "configured_mcp_servers.json"):
    """Restore MCP servers from the configuration file."""
    
    print("🔄 Restoring MCP Servers from Configuration")
    print("=" * 50)
    
    # Load configuration
    config_path = Path(config_file)
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_file}")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False
    
    print(f"📁 Loaded configuration from: {config_file}")
    print(f"📊 Found {config['summary']['total_servers']} servers to restore")
    
    # Get the global registry
    registry = await get_global_registry()
    
    # Restore external servers only (internal server is always present)
    external_servers = {k: v for k, v in config['servers'].items() if v['type'] == 'external'}
    
    success_count = 0
    error_count = 0
    
    for server_name, server_config in external_servers.items():
        print(f"\n🔧 Restoring server: {server_config['name']}")
        print(f"   URL: {server_config['url']}")
        
        try:
            # Add server to registry
            await registry.add_server(
                name=server_config['name'],
                url=server_config['url'],
                server_type=server_config['type'].upper(),
                auth_type=server_config.get('authentication', {}).get('type', 'none').upper(),
                timeout=30.0
            )
            
            print(f"   ✅ Successfully restored: {server_config['name']}")
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ Failed to restore {server_config['name']}: {e}")
            error_count += 1
    
    # Summary
    print(f"\n📊 Restoration Summary:")
    print(f"   ✅ Successfully restored: {success_count} servers")
    print(f"   ❌ Failed to restore: {error_count} servers")
    print(f"   📈 Total external servers: {len(external_servers)}")
    
    if success_count > 0:
        print(f"\n🎯 Testing restored servers...")
        
        # Test all servers
        servers = registry.list_servers()
        healthy_count = 0
        
        for server in servers:
            if server.server_type == "EXTERNAL":
                try:
                    health = registry.get_health(server.name)
                    if health.get('status') == 'healthy':
                        print(f"   ✅ {server.name}: Healthy")
                        healthy_count += 1
                    else:
                        print(f"   ⚠️  {server.name}: {health.get('status', 'Unknown')}")
                except Exception as e:
                    print(f"   ❌ {server.name}: Error checking health - {e}")
        
        print(f"\n🏥 Health Check Summary:")
        print(f"   ✅ Healthy servers: {healthy_count}")
        print(f"   📊 Total external servers: {len([s for s in servers if s.server_type == 'EXTERNAL'])}")
    
    return success_count > 0

async def list_current_servers():
    """List currently configured servers."""
    
    print("📋 Currently Configured MCP Servers")
    print("=" * 40)
    
    registry = await get_global_registry()
    servers = registry.list_servers()
    
    if not servers:
        print("   No servers configured")
        return
    
    for server in servers:
        print(f"\n🔧 {server.name}")
        print(f"   Type: {server.server_type}")
        print(f"   URL: {server.url}")
        print(f"   Status: {server.status}")
        print(f"   Connected: {server.connected}")
        
        # Get health status
        try:
            health = registry.get_health(server.name)
            print(f"   Health: {health.get('status', 'Unknown')}")
        except Exception as e:
            print(f"   Health: Error - {e}")

async def main():
    """Main function."""
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "restore":
            config_file = sys.argv[2] if len(sys.argv) > 2 else "configured_mcp_servers.json"
            success = await restore_mcp_servers(config_file)
            sys.exit(0 if success else 1)
            
        elif command == "list":
            await list_current_servers()
            sys.exit(0)
            
        elif command == "help":
            print("Usage:")
            print("  python restore_mcp_servers.py restore [config_file]  - Restore servers from config")
            print("  python restore_mcp_servers.py list                   - List current servers")
            print("  python restore_mcp_servers.py help                   - Show this help")
            sys.exit(0)
            
        else:
            print(f"Unknown command: {command}")
            print("Use 'help' for usage information")
            sys.exit(1)
    else:
        # Default: restore from configured_mcp_servers.json
        success = await restore_mcp_servers()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
