#!/bin/bash

# Setup Development Environment for Word Add-in MCP
# This script creates the development Azure resources

set -e

# Configuration
DEV_RESOURCE_GROUP="novitai-word-mcp-dev-rg"
DEV_ACR_NAME="novitaiwordmcpdev"
DEV_BACKEND_APP_NAME="novitai-word-mcp-backend-dev"
DEV_FRONTEND_APP_NAME="novitai-word-mcp-frontend-dev"
LOCATION="East US 2"
SERVICE_PLAN_NAME="novitai-word-mcp-dev-plan"

echo "🚀 Setting up Development Environment..."

# Create resource group
echo "📦 Creating resource group: $DEV_RESOURCE_GROUP"
az group create \
  --name $DEV_RESOURCE_GROUP \
  --location "$LOCATION" \
  --output table

# Create App Service Plan
echo "📋 Creating App Service Plan: $SERVICE_PLAN_NAME"
az appservice plan create \
  --name $SERVICE_PLAN_NAME \
  --resource-group $DEV_RESOURCE_GROUP \
  --location "$LOCATION" \
  --is-linux \
  --sku B1 \
  --output table

# Create Azure Container Registry
echo "🐳 Creating Azure Container Registry: $DEV_ACR_NAME"
az acr create \
  --name $DEV_ACR_NAME \
  --resource-group $DEV_RESOURCE_GROUP \
  --location "$LOCATION" \
  --sku Basic \
  --admin-enabled true \
  --output table

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $DEV_ACR_NAME --resource-group $DEV_RESOURCE_GROUP --query loginServer --output tsv)
echo "🔑 ACR Login Server: $ACR_LOGIN_SERVER"

# Create Backend App Service
echo "🔧 Creating Backend App Service: $DEV_BACKEND_APP_NAME"
az webapp create \
  --name $DEV_BACKEND_APP_NAME \
  --resource-group $DEV_RESOURCE_GROUP \
  --plan $SERVICE_PLAN_NAME \
  --deployment-container-image-name $ACR_LOGIN_SERVER/backend:latest \
  --output table

# Create Frontend App Service
echo "🎨 Creating Frontend App Service: $DEV_FRONTEND_APP_NAME"
az webapp create \
  --name $DEV_FRONTEND_APP_NAME \
  --resource-group $DEV_RESOURCE_GROUP \
  --plan $SERVICE_PLAN_NAME \
  --deployment-container-image-name $ACR_LOGIN_SERVER/frontend:latest \
  --output table

# Configure Backend App Settings
echo "⚙️ Configuring Backend App Settings..."
az webapp config appsettings set \
  --resource-group $DEV_RESOURCE_GROUP \
  --name $DEV_BACKEND_APP_NAME \
  --settings \
    ENVIRONMENT="development" \
    LOG_LEVEL="DEBUG" \
    ALLOWED_ORIGINS="https://$DEV_FRONTEND_APP_NAME.azurewebsites.net" \
    AZURE_OPENAI_API_KEY="YOUR_AZURE_OPENAI_API_KEY" \
    AZURE_OPENAI_ENDPOINT="https://your-azure-openai-endpoint.cognitiveservices.azure.com" \
    AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini" \
    AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o-mini" \
    AZURE_OPENAI_API_VERSION="2024-02-15-preview" \
    AUTH0_DOMAIN="your-dev-auth0-domain.us.auth0.com" \
    AUTH0_CLIENT_ID="your-dev-client-id" \
    AUTH0_CLIENT_SECRET="your-dev-client-secret" \
    AUTH0_AUDIENCE="your-dev-api-identifier" \
  --output table

# Configure Frontend App Settings
echo "⚙️ Configuring Frontend App Settings..."
az webapp config appsettings set \
  --resource-group $DEV_RESOURCE_GROUP \
  --name $DEV_FRONTEND_APP_NAME \
  --settings \
    REACT_APP_API_BASE_URL="https://$DEV_BACKEND_APP_NAME.azurewebsites.net" \
    REACT_APP_AUTH0_DOMAIN="your-dev-auth0-domain.us.auth0.com" \
    REACT_APP_AUTH0_CLIENT_ID="your-dev-client-id" \
    REACT_APP_AUTH0_AUDIENCE="your-dev-api-identifier" \
  --output table

# Enable continuous deployment for backend
echo "🔄 Enabling continuous deployment for backend..."
az webapp deployment container config \
  --enable-cd true \
  --name $DEV_BACKEND_APP_NAME \
  --resource-group $DEV_RESOURCE_GROUP \
  --query CI_CD_URL \
  --output tsv

# Enable continuous deployment for frontend
echo "🔄 Enabling continuous deployment for frontend..."
az webapp deployment container config \
  --enable-cd true \
  --name $DEV_FRONTEND_APP_NAME \
  --resource-group $DEV_RESOURCE_GROUP \
  --query CI_CD_URL \
  --output tsv

# Create webhook for ACR to trigger deployment
echo "🔗 Creating ACR webhook for backend..."
az acr webhook create \
  --name appserviceCD-backend \
  --registry $DEV_ACR_NAME \
  --uri "https://$DEV_BACKEND_APP_NAME:$(az webapp deployment list-publishing-credentials --name $DEV_BACKEND_APP_NAME --resource-group $DEV_RESOURCE_GROUP --query publishingPassword --output tsv)@$DEV_BACKEND_APP_NAME.scm.azurewebsites.net/docker/hook" \
  --actions push \
  --scope backend:latest \
  --output table

echo "🔗 Creating ACR webhook for frontend..."
az acr webhook create \
  --name appserviceCD-frontend \
  --registry $DEV_ACR_NAME \
  --uri "https://$DEV_FRONTEND_APP_NAME:$(az webapp deployment list-publishing-credentials --name $DEV_FRONTEND_APP_NAME --resource-group $DEV_RESOURCE_GROUP --query publishingPassword --output tsv)@$DEV_FRONTEND_APP_NAME.scm.azurewebsites.net/docker/hook" \
  --actions push \
  --scope frontend:latest \
  --output table

echo "✅ Development environment setup complete!"
echo ""
echo "📋 Development Environment URLs:"
echo "  Backend:  https://$DEV_BACKEND_APP_NAME.azurewebsites.net"
echo "  Frontend: https://$DEV_FRONTEND_APP_NAME.azurewebsites.net"
echo ""
echo "🔧 Next Steps:"
echo "  1. Update Auth0 settings with development URLs"
echo "  2. Push to 'dev' branch to trigger development deployment"
echo "  3. Push to 'main' branch to trigger production deployment"
echo ""
echo "🚀 Ready for branch-based deployment!"
