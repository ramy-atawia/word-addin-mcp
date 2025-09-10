#!/bin/bash

# Start Complete E2E Word Add-in MCP System

echo "🚀 Starting Complete E2E Word Add-in MCP System..."

# Start backend with Docker
echo "📦 Starting backend container..."
docker run -d \
    --name word-addin-backend \
    -p 9000:9000 \
    --env-file .env \
    word-addin-mcp-backend || echo "Backend already running"

# Start frontend with HTTPS using office-addin-dev-certs
echo "🌐 Starting frontend with HTTPS..."
cd "Novitai MCP"

# Generate Office certificates if needed
if [ ! -d ~/.office-addin-dev-certs ]; then
    echo "🔐 Generating Office Add-in certificates..."
    npx office-addin-dev-certs install --machine
fi

# Serve the dist folder with HTTPS
echo "🚀 Starting HTTPS server on port 3002..."
npx office-addin-https-reverse-proxy \
    --url http://localhost:3001 \
    --port 3002 &

# Start simple HTTP server for the dist folder
cd dist
python3 -m http.server 3001 &

cd ..

echo ""
echo "✅ E2E System Started!"
echo ""
echo "🌐 Frontend (Word Add-in): https://localhost:3002"
echo "🔧 Backend API: http://localhost:9000"
echo "📖 API Docs: http://localhost:9000/docs"
echo ""
echo "📱 Office Add-in Manifest: /Users/Mariam/word-addin-mcp/Novitai MCP/manifest.xml"
echo ""
echo "To sideload in Word:"
echo "1. Open Word"
echo "2. Go to Insert > My Add-ins > Upload My Add-in"
echo "3. Select the manifest.xml file"
echo "4. The add-in will appear in the ribbon"
echo ""
echo "🛑 To stop: ./stop-e2e.sh"
