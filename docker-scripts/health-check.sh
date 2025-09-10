#!/bin/bash

# Word Add-in MCP - Health Check Script
# This script checks the health of all services

set -e

echo "🏥 Checking Word Add-in MCP service health..."
echo ""

# Function to check service health
check_service() {
    local service=$1
    local url=$2
    local expected_code=${3:-200}
    
    echo -n "📋 $service: "
    
    if curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" | grep -q "$expected_code"; then
        echo "✅ Healthy"
    else
        echo "❌ Unhealthy"
    fi
}

# Check backend
check_service "Backend API" "http://localhost:9000/health"

# Check frontend (dev)
if docker-compose ps | grep -q "wordaddin-frontend-dev"; then
    check_service "Frontend (Dev)" "https://localhost:3002" "200\|404"
fi

# Check frontend (prod)
if docker-compose ps | grep -q "wordaddin-frontend-prod"; then
    check_service "Frontend (Prod)" "https://localhost:3002" "200\|404"
fi

# Check database
echo -n "📋 PostgreSQL: "
if docker-compose exec -T postgres pg_isready -U wordaddin_user -d wordaddin >/dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
fi

# Check Redis
echo -n "📋 Redis: "
if docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; then
    echo "✅ Healthy"
else
    echo "❌ Unhealthy"
fi

echo ""
echo "📊 Container Status:"
docker-compose ps
