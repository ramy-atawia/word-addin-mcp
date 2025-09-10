#!/bin/bash

echo "🛑 Stopping E2E Word Add-in MCP System..."

# Stop backend container
docker stop word-addin-backend 2>/dev/null || echo "Backend not running"
docker rm word-addin-backend 2>/dev/null || echo "Backend container not found"

# Stop Python HTTP server
pkill -f "python3 -m http.server 3001" 2>/dev/null || echo "Python server not running"

# Stop office-addin-https-reverse-proxy
pkill -f "office-addin-https-reverse-proxy" 2>/dev/null || echo "HTTPS proxy not running"

echo "✅ All services stopped"
