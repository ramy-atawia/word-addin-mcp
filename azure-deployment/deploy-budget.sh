#!/bin/bash
set -e

# Budget Azure Deployment Script for Word Add-in MCP
# Optimized for 10 concurrent users, $30-50/month budget

RESOURCE_GROUP=${1:-novitai-word-mcp-rg}
LOCATION=${2:-eastus}
ACR_NAME=${3:-novitaiwordmcp}
BACKEND_APP_NAME=${4:-novitai-word-mcp-backend}
FRONTEND_APP_NAME=${5:-novitai-word-mcp-frontend}

echo "🚀 Deploying Word Add-in MCP to Azure (Budget Optimized)..."
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "Target Budget: $30-50/month"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it first."
    exit 1
fi

if ! az account show &> /dev/null; then
    print_error "Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

# Load environment variables from .env file
if [ -f ".env" ]; then
    print_status "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
    print_success "Environment variables loaded"
else
    print_warning ".env file not found. Make sure your API keys are set as environment variables."
fi

# Create resource group
print_status "Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Container Registry (Basic tier for cost optimization)
print_status "Creating Azure Container Registry (Basic tier)..."
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query loginServer --output tsv)

# Create App Service Plans (Free for dev, B1 for prod)
print_status "Creating App Service Plans..."
az appservice plan create --resource-group $RESOURCE_GROUP --name novitai-word-mcp-dev-plan --sku F1 --is-linux
az appservice plan create --resource-group $RESOURCE_GROUP --name novitai-word-mcp-prod-plan --sku B1 --is-linux

# Database removed - using stateless architecture

# Create Redis Cache (C0 tier)
print_status "Creating Redis Cache (C0 tier)..."
az redis create \
    --resource-group $RESOURCE_GROUP \
    --name word-addin-redis \
    --location $LOCATION \
    --sku Basic \
    --vm-size c0

# Get Redis connection string
REDIS_CONNECTION_STRING=$(az redis list-keys --resource-group $RESOURCE_GROUP --name word-addin-redis --query primaryKey --output tsv)

# Build and push images
print_status "Building and pushing Docker images..."

# Login to ACR
az acr login --name $ACR_NAME

# Build backend
print_status "Building backend image..."
docker build -t $ACR_LOGIN_SERVER/backend:latest ./backend
docker push $ACR_LOGIN_SERVER/backend:latest

# Build frontend
print_status "Building frontend image..."
docker build -t $ACR_LOGIN_SERVER/frontend:latest ./Novitai\ MCP
docker push $ACR_LOGIN_SERVER/frontend:latest

# Create Development Environment
print_status "Creating development environment..."
az webapp create \
    --resource-group $RESOURCE_GROUP \
    --plan novitai-word-mcp-dev-plan \
    --name $BACKEND_APP_NAME-dev \
    --deployment-container-image-name $ACR_LOGIN_SERVER/backend:latest

az webapp create \
    --resource-group $RESOURCE_GROUP \
    --plan novitai-word-mcp-dev-plan \
    --name $FRONTEND_APP_NAME-dev \
    --deployment-container-image-name $ACR_LOGIN_SERVER/frontend:latest

# Create Production Environment
print_status "Creating production environment..."
az webapp create \
    --resource-group $RESOURCE_GROUP \
    --plan novitai-word-mcp-prod-plan \
    --name $BACKEND_APP_NAME \
    --deployment-container-image-name $ACR_LOGIN_SERVER/backend:latest

az webapp create \
    --resource-group $RESOURCE_GROUP \
    --plan novitai-word-mcp-prod-plan \
    --name $FRONTEND_APP_NAME \
    --deployment-container-image-name $ACR_LOGIN_SERVER/frontend:latest

# Configure Development Environment
print_status "Configuring development environment..."
az webapp config appsettings set \
    --resource-group $RESOURCE_GROUP \
    --name $BACKEND_APP_NAME-dev \
    --settings \
        REDIS_URL="redis://word-addin-redis.redis.cache.windows.net:6380" \
        AZURE_OPENAI_API_KEY="${AZURE_OPENAI_API_KEY}" \
        AZURE_OPENAI_ENDPOINT="${AZURE_OPENAI_ENDPOINT}" \
        AZURE_OPENAI_DEPLOYMENT_NAME="${AZURE_OPENAI_DEPLOYMENT_NAME}" \
        GOOGLE_API_KEY="${GOOGLE_API_KEY}" \
        GOOGLE_CSE_ID="${GOOGLE_CSE_ID}" \
        PATENTSVIEW_API_KEY="${PATENTSVIEW_API_KEY}" \
        SECRET_KEY="$(openssl rand -base64 32)" \
        ENVIRONMENT="development" \
        DEBUG="true" \
        ALLOWED_ORIGINS="https://$FRONTEND_APP_NAME-dev.azurewebsites.net" \
        ALLOWED_HOSTS="*" \
        AUTH0_DOMAIN="dev-bktskx5kbc655wcl.us.auth0.com" \
        AUTH0_AUDIENCE="https://$BACKEND_APP_NAME-dev.azurewebsites.net"

az webapp config appsettings set \
    --resource-group $RESOURCE_GROUP \
    --name $FRONTEND_APP_NAME-dev \
    --settings \
        NODE_ENV="development" \
        REACT_APP_API_BASE_URL="https://$BACKEND_APP_NAME-dev.azurewebsites.net"

# Configure Production Environment
print_status "Configuring production environment..."
az webapp config appsettings set \
    --resource-group $RESOURCE_GROUP \
    --name $BACKEND_APP_NAME \
    --settings \
        REDIS_URL="redis://word-addin-redis.redis.cache.windows.net:6380" \
        AZURE_OPENAI_API_KEY="${AZURE_OPENAI_API_KEY}" \
        AZURE_OPENAI_ENDPOINT="${AZURE_OPENAI_ENDPOINT}" \
        AZURE_OPENAI_DEPLOYMENT_NAME="${AZURE_OPENAI_DEPLOYMENT_NAME}" \
        GOOGLE_API_KEY="${GOOGLE_API_KEY}" \
        GOOGLE_CSE_ID="${GOOGLE_CSE_ID}" \
        PATENTSVIEW_API_KEY="${PATENTSVIEW_API_KEY}" \
        SECRET_KEY="$(openssl rand -base64 32)" \
        ENVIRONMENT="production" \
        DEBUG="false" \
        ALLOWED_ORIGINS="https://$FRONTEND_APP_NAME.azurewebsites.net" \
        ALLOWED_HOSTS="*" \
        AUTH0_DOMAIN="dev-bktskx5kbc655wcl.us.auth0.com" \
        AUTH0_AUDIENCE="https://$BACKEND_APP_NAME.azurewebsites.net"

az webapp config appsettings set \
    --resource-group $RESOURCE_GROUP \
    --name $FRONTEND_APP_NAME \
    --settings \
        NODE_ENV="production" \
        REACT_APP_API_BASE_URL="https://$BACKEND_APP_NAME.azurewebsites.net"

# Enable continuous deployment
print_status "Enabling continuous deployment..."
az webapp deployment container config \
    --resource-group $RESOURCE_GROUP \
    --name $BACKEND_APP_NAME-dev \
    --enable-cd true

az webapp deployment container config \
    --resource-group $RESOURCE_GROUP \
    --name $FRONTEND_APP_NAME-dev \
    --enable-cd true

az webapp deployment container config \
    --resource-group $RESOURCE_GROUP \
    --name $BACKEND_APP_NAME \
    --enable-cd true

az webapp deployment container config \
    --resource-group $RESOURCE_GROUP \
    --name $FRONTEND_APP_NAME \
    --enable-cd true

print_success "Deployment completed!"
echo ""
echo "🌐 URLs:"
echo "   Development Frontend: https://$FRONTEND_APP_NAME-dev.azurewebsites.net"
echo "   Development Backend:  https://$BACKEND_APP_NAME-dev.azurewebsites.net"
echo "   Production Frontend:  https://$FRONTEND_APP_NAME.azurewebsites.net"
echo "   Production Backend:   https://$BACKEND_APP_NAME.azurewebsites.net"
echo ""
echo "🔑 Redis Key: $REDIS_CONNECTION_STRING"
echo ""
echo "💰 Estimated Monthly Cost: ~$10"
echo "   - App Service Plan (Dev): $0 (Free tier)"
echo "   - App Service Plan (Prod): $13 (B1)"
echo "   - Redis Cache: $0 (C0 tier)"
echo "   - Container Registry: $5 (Basic)"
echo ""
echo "📝 Next steps:"
echo "1. Update your manifest.xml with the production frontend URL"
echo "2. Test both environments"
echo "3. Configure Auth0 with the new backend URLs"
echo "4. Set up monitoring (optional)"
