#!/bin/bash

# Word Add-in MCP - Stop Docker Services
# This script stops all running containers

set -e

echo "🛑 Stopping Word Add-in MCP Docker services..."

# Stop all profiles
docker-compose --profile dev --profile prod down

echo "✅ All services stopped."
echo ""
echo "💡 To clean up completely (remove volumes): './docker-scripts/clean.sh'"
