# MCP Server Configuration Management

This directory contains tools and configuration files for managing MCP (Model Context Protocol) servers in the Word Add-in MCP application.

## 📁 Files Overview

### Configuration Files
- **`configured_mcp_servers.json`** - Static snapshot of currently configured MCP servers
- **`exported_mcp_servers.json`** - Dynamic export from the running application API

### Management Scripts
- **`export_mcp_servers.py`** - Export current server configuration from running app
- **`restore_mcp_servers.py`** - Restore servers from configuration file

## 🚀 Quick Start

### Export Current Configuration
```bash
# Export from running application
python export_mcp_servers.py export

# Export from custom API URL
python export_mcp_servers.py export https://your-api-url:9000 custom_export.json
```

### Restore Configuration
```bash
# Restore from default configuration file
python restore_mcp_servers.py restore

# Restore from custom configuration file
python restore_mcp_servers.py restore my_servers.json

# List currently configured servers
python restore_mcp_servers.py list
```

## 📊 Currently Configured Servers

### Internal Server
- **Name**: Internal MCP Server
- **Type**: Internal
- **Tools**: 4 tools (web_search_tool, text_analysis_tool, document_analysis_tool, file_reader_tool)

### External Servers

#### 1. Sequential Thinking Server
- **URL**: `https://remote.mcpservers.org/sequentialthinking/mcp`
- **Tools**: 1 tool (sequentialthinking)
- **Description**: Dynamic problem-solving through structured thinking

#### 2. McPoogle Search Server
- **URL**: `https://mcp.mcpoogle.com/sse`
- **Tools**: 1 tool (searchMcpServers)
- **Description**: Search engine for MCP servers and tools

#### 3. Cloudflare MCP Demo Server
- **URL**: `https://demo-day.mcp.cloudflare.com/sse`
- **Tools**: 1 tool (mcp_demo_day_info)
- **Description**: Information about Cloudflare's MCP Demo Day

#### 4. Microsoft Learn Documentation Server
- **URL**: `https://learn.microsoft.com/api/mcp`
- **Tools**: 2 tools (microsoft_docs_search, microsoft_docs_fetch)
- **Description**: Search and fetch Microsoft/Azure documentation

## 🔧 Configuration File Format

### Server Configuration Structure
```json
{
  "metadata": {
    "generated_at": "2025-09-01T21:40:00Z",
    "source": "Running Word Add-in MCP Application",
    "version": "1.0.0"
  },
  "servers": {
    "server_name": {
      "name": "Display Name",
      "server_id": "unique-id",
      "type": "internal|external",
      "url": "server-url",
      "status": "healthy|unhealthy",
      "connected": true|false,
      "authentication": {
        "type": "none|api_key|oauth|basic",
        "required": true|false
      },
      "tools": [
        {
          "name": "tool_name",
          "description": "tool description",
          "category": "general",
          "requires_auth": false,
          "usage_count": 0
        }
      ]
    }
  },
  "summary": {
    "total_servers": 5,
    "internal_servers": 1,
    "external_servers": 4,
    "total_tools": 9,
    "healthy_servers": 5,
    "connected_servers": 5
  }
}
```

### Cursor MCP Config Format
```json
{
  "cursor_mcp_config": {
    "mcpServers": {
      "sequentialthinking": {
        "transport": "http",
        "url": "https://remote.mcpservers.org/sequentialthinking/mcp",
        "headers": {
          "Content-Type": "application/json"
        }
      }
    }
  }
}
```

## 🛠️ Script Usage

### Export Script (`export_mcp_servers.py`)

**Purpose**: Export current server configuration from running application

**Commands**:
- `python export_mcp_servers.py export` - Export from localhost:9000
- `python export_mcp_servers.py export <api_url> <output_file>` - Custom export
- `python export_mcp_servers.py help` - Show help

**Features**:
- Fetches live data from API
- Includes server health status
- Includes tool usage statistics
- Generates Cursor MCP config format

### Restore Script (`restore_mcp_servers.py`)

**Purpose**: Restore servers from configuration file

**Commands**:
- `python restore_mcp_servers.py restore` - Restore from default config
- `python restore_mcp_servers.py restore <config_file>` - Restore from custom config
- `python restore_mcp_servers.py list` - List current servers
- `python restore_mcp_servers.py help` - Show help

**Features**:
- Adds external servers to registry
- Tests server connections
- Provides health check summary
- Error handling and reporting

## 🔐 Authentication Support

The configuration supports various authentication types:

### No Authentication
```json
"authentication": {
  "type": "none",
  "required": false
}
```

### API Key Authentication
```json
"authentication": {
  "type": "api_key",
  "required": true,
  "api_key": "your-api-key"
}
```

### OAuth Bearer Token
```json
"authentication": {
  "type": "oauth",
  "required": true,
  "api_key": "your-bearer-token"
}
```

### Basic Authentication
```json
"authentication": {
  "type": "basic",
  "required": true,
  "username": "your-username",
  "password": "your-password"
}
```

## 📈 Monitoring and Health Checks

### Health Status
- **healthy**: Server is responding and tools are accessible
- **unhealthy**: Server is not responding or has errors
- **unknown**: Health status could not be determined

### Connection Status
- **connected**: Server is currently connected
- **disconnected**: Server is not connected

### Usage Statistics
- **usage_count**: Number of times each tool has been used
- **last_health_check**: Timestamp of last health check

## 🚨 Troubleshooting

### Common Issues

1. **SSL Certificate Errors**
   - The scripts disable SSL verification for localhost
   - For production, ensure proper SSL certificates

2. **Server Connection Failures**
   - Check server URLs are accessible
   - Verify authentication credentials
   - Check network connectivity

3. **Tool Discovery Failures**
   - Ensure servers are running
   - Check server logs for errors
   - Verify MCP protocol compatibility

### Debug Commands
```bash
# Test server connectivity
curl -k https://localhost:9000/api/v1/mcp/external/servers

# Check tool availability
curl -k https://localhost:9000/api/v1/mcp/tools

# List current servers
python restore_mcp_servers.py list
```

## 🔄 Backup and Restore Workflow

### 1. Export Current Configuration
```bash
python export_mcp_servers.py export
```

### 2. Backup Configuration File
```bash
cp exported_mcp_servers.json backup_$(date +%Y%m%d_%H%M%S).json
```

### 3. Restore Configuration
```bash
python restore_mcp_servers.py restore exported_mcp_servers.json
```

### 4. Verify Restoration
```bash
python restore_mcp_servers.py list
```

## 📝 Notes

- Configuration files are in JSON format for easy editing
- Server IDs are UUIDs and should not be modified
- Tool schemas are automatically discovered from servers
- Health checks run automatically in the background
- Authentication credentials are not stored in plain text in the configuration files

## 🔗 Related Files

- `/Users/Mariam/.cursor/mcp.json` - Cursor MCP configuration
- `app/services/mcp/server_registry.py` - Server registry implementation
- `app/api/v1/external_mcp.py` - External MCP API endpoints
- `app/core/fastmcp_client.py` - FastMCP client implementation
