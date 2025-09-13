#!/bin/bash
set -e

# Azure Deployment Script for Word Add-in MCP
# Usage: ./deploy.sh <resource-group> <location>

RESOURCE_GROUP=${1:-novitai-word-mcp-rg}
LOCATION=${2:-eastus}
ACR_NAME=${3:-novitaiwordmcp}
BACKEND_APP_NAME=${4:-novitai-word-mcp-backend}
FRONTEND_APP_NAME=${5:-novitai-word-mcp-frontend}

echo "🚀 Deploying Word Add-in MCP to Azure..."
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "ACR: $ACR_NAME"

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

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it first."
    exit 1
fi

# Check if logged in
if ! az account show &> /dev/null; then
    print_error "Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

# Create resource group
print_status "Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Container Registry
print_status "Creating Azure Container Registry..."
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query loginServer --output tsv)

# Create App Service Plan
print_status "Creating App Service Plan..."
az appservice plan create --resource-group $RESOURCE_GROUP --name word-addin-plan --sku B1 --is-linux

# Database removed - using stateless architecture

# Create Redis Cache
print_status "Creating Redis Cache..."
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

# Create backend web app
print_status "Creating backend web app..."
az webapp create \
    --resource-group $RESOURCE_GROUP \
    --plan word-addin-plan \
    --name $BACKEND_APP_NAME \
    --deployment-container-image-name $ACR_LOGIN_SERVER/backend:latest

# Configure backend environment variables
print_status "Configuring backend environment variables..."
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
        ALLOWED_HOSTS="*"

# Create frontend web app
print_status "Creating frontend web app..."
az webapp create \
    --resource-group $RESOURCE_GROUP \
    --plan word-addin-plan \
    --name $FRONTEND_APP_NAME \
    --deployment-container-image-name $ACR_LOGIN_SERVER/frontend:latest

# Configure frontend environment variables
print_status "Configuring frontend environment variables..."
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
    --name $BACKEND_APP_NAME \
    --enable-cd true

az webapp deployment container config \
    --resource-group $RESOURCE_GROUP \
    --name $FRONTEND_APP_NAME \
    --enable-cd true

print_success "Deployment completed!"
echo ""
echo "🌐 URLs:"
echo "   Frontend: https://$FRONTEND_APP_NAME.azurewebsites.net"
echo "   Backend:  https://$BACKEND_APP_NAME.azurewebsites.net"
echo "   API Docs: https://$BACKEND_APP_NAME.azurewebsites.net/docs"
echo ""
echo "🔑 Redis Key: $REDIS_CONNECTION_STRING"
echo ""
echo "📝 Next steps:"
echo "1. Update your manifest.xml with the new frontend URL"
echo "2. Test the deployment"
echo "3. Configure custom domain (optional)"
echo "4. Set up monitoring and alerts"