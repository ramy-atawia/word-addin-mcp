#!/bin/bash

echo "🔐 Installing SSL Certificate to macOS System Trust Store..."

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is for macOS only"
    exit 1
fi

# Check if certificate files exist
if [ ! -f "localhost.crt" ] || [ ! -f "localhost.key" ]; then
    echo "❌ Certificate files not found. Please run the certificate generation first."
    exit 1
fi

# Install certificate to system keychain
echo "📋 Adding certificate to system keychain..."
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain localhost.crt

if [ $? -eq 0 ]; then
    echo "✅ Certificate installed successfully!"
    echo "🔒 The certificate is now trusted by the system"
    echo "🌐 You should no longer see SSL warnings in browsers"
    echo ""
    echo "Note: You may need to restart your browser for changes to take effect"
else
    echo "❌ Failed to install certificate"
    exit 1
fi

echo ""
echo "🎯 Next steps:"
echo "1. Restart your browser"
echo "2. Start the backend: cd backend && uvicorn app.main:app --host 0.0.0.0 --port 9000 --ssl-keyfile ../localhost.key --ssl-certfile ../localhost.crt --reload"
echo "3. Start the frontend: cd 'Novitai MCP' && node https_server.js"
echo "4. Open: https://localhost:3002/taskpane.html"
