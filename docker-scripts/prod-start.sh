#!/bin/bash

# Word Add-in MCP - Production Docker Setup
# This script starts the application in production mode

set -e

echo "🚀 Starting Word Add-in MCP in Production Mode..."
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ No .env file found. Please create one with production values."
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Validate required environment variables
required_vars=("AZURE_OPENAI_API_KEY" "AZURE_OPENAI_ENDPOINT" "SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable $var is not set"
        exit 1
    fi
done

# Create necessary directories
mkdir -p logs uploads

# Generate SSL certificates if needed
echo "🔐 Ensuring SSL certificates are ready..."
docker-compose run --rm ssl-generator

# Start production services
echo "🐳 Starting Docker containers in production mode..."
docker-compose --profile prod up --build -d

echo ""
echo "✅ Production environment is running!"
echo ""
echo "🌐 Access points:"
echo "  - Frontend (Word Add-in): https://localhost:3002"
echo "  - Backend API: http://localhost:9000"
echo "  - Database: localhost:5432"
echo "  - Redis: localhost:6379"
echo ""
echo "📖 To stop: './docker-scripts/stop.sh'"
echo "🔧 To view logs: 'docker-compose logs -f [service-name]'"
echo "📊 To check health: './docker-scripts/health-check.sh'"
