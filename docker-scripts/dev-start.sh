#!/bin/bash

# Word Add-in MCP - Development Docker Setup
# This script starts the application in development mode with hot reloading

set -e

echo "🚀 Starting Word Add-in MCP in Development Mode..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ No .env file found. Please create one with required values."
    echo "   Required: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, GOOGLE_API_KEY, GOOGLE_CSE_ID"
    exit 1
fi

# Load environment variables properly (source the file instead of export)
set -a
source .env
set +a

echo "✅ Environment variables loaded from .env"

# Create necessary directories
mkdir -p logs uploads ssl

# Generate SSL certificates if needed
echo "🔐 Ensuring SSL certificates are ready..."
docker-compose run --rm ssl-generator

# Start development services
echo "🐳 Starting Docker containers..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

echo ""
echo "✅ Development environment is running!"
echo ""
echo "🌐 Access points:"
echo "  - Frontend (Word Add-in): https://localhost:3002"
echo "  - Backend API: http://localhost:9000"
echo "  - API Documentation: http://localhost:9000/docs"
echo "  - Database: localhost:5432"
echo "  - Redis: localhost:6379"
echo ""
echo "📖 To stop: Ctrl+C or 'docker-compose down'"
echo "🔧 To view logs: 'docker-compose logs -f [service-name]'"
