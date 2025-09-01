# Word Add-in MCP Certificate Setup & Troubleshooting Guide

## Overview
This document contains the exact steps used to resolve HTTPS certificate trust issues between the Word Add-in frontend and the FastAPI backend. The solution involves installing Office Add-in development certificates to the macOS System keychain.

## Prerequisites
- macOS system with admin privileges
- Office Add-in development certificates installed via `office-addin-dev-certs install`
- Backend running on `https://localhost:9000`
- Frontend running on `https://localhost:3002`

## Problem Description
The Word Add-in was experiencing `ERR_CERT_AUTHORITY_INVALID` errors when trying to connect to the backend, even though both servers were running with HTTPS. This was caused by the certificates not being trusted by the macOS system.

## Solution: Install Certificates to System Keychain

### Step 1: Verify Backend is Running
```bash
# Check if backend is responding
curl -k https://localhost:9000/
# Expected: {"message":"Word Add-in MCP Backend","version":"1.0.0","status":"running"...}

# Check MCP tools endpoint
curl -k https://localhost:9000/api/v1/mcp/tools
# Expected: JSON response with 4 MCP tools
```

### Step 2: Install Localhost Certificate to System Keychain
```bash
# Navigate to project root
cd /Users/Mariam/word-addin-mcp

# Install localhost certificate to system keychain (requires admin password)
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ~/.office-addin-dev-certs/localhost.crt
```

### Step 3: Install CA Certificate to System Keychain
```bash
# Install CA certificate to system keychain (requires admin password)
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ~/.office-addin-dev-certs/ca.crt
```

### Step 4: Verify Certificate Installation
```bash
# Check that certificates are in system keychain
security find-certificate -c "localhost" -a | grep "keychain:"
# Expected: Multiple entries showing "/Library/Keychains/System.keychain"
```

### Step 5: Test Backend Certificate Trust
```bash
# Test without -k flag (should work if certificate is trusted)
curl https://localhost:9000/api/v1/mcp/tools
# Expected: JSON response with MCP tools (no certificate errors)
```

### Step 6: Clear Office Add-in Cache
```bash
# Disable Office Add-in debugging
defaults write com.microsoft.Word OfficeWebAddinDeveloperDebug -bool NO

# Remove Office Add-in cache
rm -rf ~/Library/Containers/com.microsoft.Word/Data/Library/Application\ Support/Microsoft/Office/16.0/Wef/

# Re-enable Office Add-in debugging
defaults write com.microsoft.Word OfficeWebAddinDeveloperDebug -bool YES
```

### Step 7: Start Frontend Server
```bash
# Navigate to frontend directory
cd /Users/Mariam/word-addin-mcp/Novitai\ MCP

# Start HTTPS server
node https_server.js
# Expected: "🚀 HTTPS server running on https://localhost:3002"
```

### Step 8: Test Frontend Certificate Trust
```bash
# Test frontend without -k flag
curl -I https://localhost:3002/taskpane.html
# Expected: HTTP/1.1 200 OK (no certificate errors)
```

## Verification Commands

### Check Running Processes
```bash
# Check if port 3002 is in use
lsof -ti:3002

# Kill process if needed
lsof -ti:3002 | xargs kill -9
```

### Test Certificate Trust
```bash
# Backend test
curl https://localhost:9000/api/v1/mcp/tools

# Frontend test  
curl https://localhost:3002/taskpane.html
```

### Check Certificate Files
```bash
# List available certificates
ls -la ~/.office-addin-dev-certs/
# Expected: ca.crt, localhost.crt, localhost.key
```

## Expected Results

### After Successful Setup:
1. **Backend**: `curl https://localhost:9000/api/v1/mcp/tools` works without `-k` flag
2. **Frontend**: `curl https://localhost:3002/taskpane.html` works without `-k` flag
3. **Browser**: No certificate warnings when accessing https://localhost:3002/taskpane.html
4. **Word Add-in**: Loads without certificate errors and connects to backend successfully

### Backend Response Example:
```json
{
  "tools": [
    {
      "name": "web_search_tool",
      "description": "Search the web for information",
      "server_id": "30f09764-88dd-43b5-ac06-8320f16ba11a",
      "server_name": "Internal MCP Server",
      "source": "internal",
      "version": "1.0.0"
    }
    // ... more tools
  ],
  "total_count": 4,
  "built_in_count": 4,
  "external_count": 0
}
```

## Troubleshooting

### Common Issues:

1. **Port Already in Use**:
   ```bash
   lsof -ti:3002 | xargs kill -9
   ```

2. **Certificate Still Not Trusted**:
   - Ensure both `localhost.crt` and `ca.crt` are installed
   - Check that certificates are in System keychain, not just user keychain
   - Restart browser after certificate installation

3. **Backend Connection Failed**:
   - Verify backend is running with correct host (`localhost`, not `0.0.0.0`)
   - Check SSL certificate paths in uvicorn command

### Backend Startup Command:
```bash
cd backend && source ../venv/bin/activate && python -m uvicorn app.main:app --host localhost --port 9000 --ssl-keyfile /Users/Mariam/.office-addin-dev-certs/localhost.key --ssl-certfile /Users/Mariam/.office-addin-dev-certs/localhost.crt --reload
```

### Frontend Startup Command:
```bash
cd "Novitai MCP" && node https_server.js
```

## Security Notes

- **System Keychain**: Installing to System keychain makes certificates trusted system-wide
- **Admin Privileges**: Required for system keychain installation
- **Development Only**: These certificates are for development purposes only
- **Production**: Use proper CA-signed certificates in production environments

## File Locations

- **Certificates**: `~/.office-addin-dev-certs/`
  - `ca.crt` - Certificate Authority certificate
  - `localhost.crt` - Localhost server certificate  
  - `localhost.key` - Private key (keep secure)

- **Backend**: `/Users/Mariam/word-addin-mcp/backend/`
- **Frontend**: `/Users/Mariam/word-addin-mcp/Novitai MCP/`

## Success Indicators

✅ **Backend responds without certificate errors**  
✅ **Frontend serves files without certificate warnings**  
✅ **Word Add-in loads and connects to backend**  
✅ **MCP tools are discovered and functional**  
✅ **Agent can process requests and execute tools**  

## Last Updated
August 31, 2025 - Certificate trust issues successfully resolved
