#!/bin/bash

# Set environment variables for Azure App Services
# Usage: ./set-env-vars.sh [dev|prod]

ENVIRONMENT=${1:-dev}
RESOURCE_GROUP="novitai-word-mcp-rg"

if [ "$ENVIRONMENT" = "dev" ]; then
    FRONTEND_APP="novitai-word-mcp-frontend-dev"
    BACKEND_APP="novitai-word-mcp-backend-dev"
    echo "Setting environment variables for DEVELOPMENT environment..."
else
    FRONTEND_APP="novitai-word-mcp-frontend"
    BACKEND_APP="novitai-word-mcp-backend"
    echo "Setting environment variables for PRODUCTION environment..."
fi

# Frontend environment variables
echo "Setting frontend environment variables..."
az webapp config appsettings set \
    --name $FRONTEND_APP \
    --resource-group $RESOURCE_GROUP \
    --settings \
        REACT_APP_AUTH0_DOMAIN=dev-bktskx5kbc655wcl.us.auth0.com \
        REACT_APP_AUTH0_CLIENT_ID=INws849yDXaC6MZVXnLhMJi6CZC4nx6U \
        REACT_APP_AUTH0_AUDIENCE=https://$BACKEND_APP.azurewebsites.net \
        REACT_APP_BACKEND_URL=https://$BACKEND_APP.azurewebsites.net \
        REACT_APP_FRONTEND_URL=https://$FRONTEND_APP.azurewebsites.net \
        REACT_APP_API_BASE_URL=https://$BACKEND_APP.azurewebsites.net \
        NODE_ENV=production

# Backend environment variables (if needed)
echo "Setting backend environment variables..."
az webapp config appsettings set \
    --name $BACKEND_APP \
    --resource-group $RESOURCE_GROUP \
    --settings \
        AUTH0_DOMAIN=dev-bktskx5kbc655wcl.us.auth0.com \
        AUTH0_AUDIENCE=https://$BACKEND_APP.azurewebsites.net \
        FRONTEND_URL=https://$FRONTEND_APP.azurewebsites.net

echo "Environment variables set successfully!"
echo "Frontend: https://$FRONTEND_APP.azurewebsites.net"
echo "Backend: https://$BACKEND_APP.azurewebsites.net"
