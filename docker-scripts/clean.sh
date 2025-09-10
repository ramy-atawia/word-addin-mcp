#!/bin/bash

# Word Add-in MCP - Clean Docker Environment
# This script removes all containers, volumes, and networks

set -e

echo "🧹 Cleaning Word Add-in MCP Docker environment..."
echo ""

read -p "⚠️  This will remove all data including database. Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Aborted."
    exit 1
fi

# Stop and remove everything
echo "🛑 Stopping services..."
docker-compose --profile dev --profile prod down

echo "🗑️  Removing containers, volumes, and networks..."
docker-compose --profile dev --profile prod down --volumes --remove-orphans

# Remove dangling images
echo "🖼️  Removing unused images..."
docker image prune -f

echo ""
echo "✅ Environment cleaned!"
echo "💡 To start fresh: './docker-scripts/dev-start.sh' or './docker-scripts/prod-start.sh'"
