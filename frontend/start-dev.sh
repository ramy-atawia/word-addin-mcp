#!/bin/bash

echo "🚀 Starting Novitai MCP Word Add-in Development Server..."
echo "🔒 Using Office Add-in SSL certificates"
echo "🌐 Server will be available at: https://localhost:3002"
echo ""

# Check if Office Add-in certificates exist
if [ ! -f ~/.office-addin-dev-certs/localhost.crt ] || [ ! -f ~/.office-addin-dev-certs/localhost.key ]; then
    echo "❌ Office Add-in certificates not found!"
    echo "Please run: office-addin-dev-certs install"
    exit 1
fi

echo "✅ Certificates found, starting development server..."
echo ""

# Start the development server
npm run start:dev
