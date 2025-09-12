#!/bin/bash
set -e

# Simple Azure Deployment Script for Word Add-in MCP
# No database needed - just containers!

RESOURCE_GROUP=${1:-novitai-word-mcp-rg}
LOCATION=${2:-eastus}
ACR_NAME=${3:-novitaiwordmcp}
BACKEND_APP_NAME=${4:-novitai-word-mcp-backend}
FRONTEND_APP_NAME=${5:-novitai-word-mcp-frontend}

echo "🚀 Deploying Word Add-in MCP to Azure (Simple - No Database)..."
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo "Target Budget: ~$20/month"

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

# Create Azure Container Registry (Basic tier)
print_status "Creating Azure Container Registry (Basic tier)..."
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query loginServer --output tsv)

# Create App Service Plans (Free for dev, B1 for prod)
print_status "Creating App Service Plans..."
az appservice plan create --resource-group $RESOURCE_GROUP --name novitai-word-mcp-dev-plan --sku F1 --is-linux
az appservice plan create --resource-group $RESOURCE_GROUP --name novitai-word-mcp-prod-plan --sku B1 --is-linux

# Build and push backend image
print_status "Building and pushing backend Docker image..."
az acr build --registry $ACR_NAME --image $BACKEND_APP_NAME:latest --file backend/Dockerfile backend/

# Build and push frontend image
print_status "Building and pushing frontend Docker image..."
az acr build --registry $ACR_NAME --image $FRONTEND_APP_NAME:latest --file "Novitai MCP/Dockerfile" "Novitai MCP/"

# Create backend web app (dev)
print_status "Creating backend web app (development)..."
az webapp create \
    --resource-group $RESOURCE_GROUP \
    --plan novitai-word-mcp-dev-plan \
    --name $BACKEND_APP_NAME-dev \
    --deployment-container-image-name $ACR_LOGIN_SERVER/$BACKEND_APP_NAME:latest

# Configure backend environment variables (dev)
print_status "Configuring backend environment variables (development)..."
az webapp config appsettings set \
    --resource-group $RESOURCE_GROUP \
    --name $BACKEND_APP_NAME-dev \
    --settings \
        AZURE_OPENAI_API_KEY="$AZURE_OPENAI_API_KEY" \
        AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
        AZURE_OPENAI_DEPLOYMENT_NAME="$AZURE_OPENAI_DEPLOYMENT_NAME" \
        GOOGLE_API_KEY="$GOOGLE_API_KEY" \
        GOOGLE_CSE_ID="$GOOGLE_CSE_ID" \
        PATENTSVIEW_API_KEY="$PATENTSVIEW_API_KEY" \
        SECRET_KEY="$(openssl rand -base64 32)" \
        ENVIRONMENT="development" \
        DEBUG="true" \
        ALLOWED_ORIGINS="https://$FRONTEND_APP_NAME-dev.azurewebsites.net" \
        ALLOWED_HOSTS="*" \
        AUTH0_DOMAIN="dev-bktskx5kbc655wcl.us.auth0.com" \
        AUTH0_AUDIENCE="https://$BACKEND_APP_NAME-dev.azurewebsites.net"

# Create frontend web app (dev)
print_status "Creating frontend web app (development)..."
az webapp create \
    --resource-group $RESOURCE_GROUP \
    --plan novitai-word-mcp-dev-plan \
    --name $FRONTEND_APP_NAME-dev \
    --deployment-container-image-name $ACR_LOGIN_SERVER/$FRONTEND_APP_NAME:latest

# Configure frontend environment variables (dev)
print_status "Configuring frontend environment variables (development)..."
az webapp config appsettings set \
    --resource-group $RESOURCE_GROUP \
    --name $FRONTEND_APP_NAME-dev \
    --settings \
        REACT_APP_API_BASE_URL="https://$BACKEND_APP_NAME-dev.azurewebsites.net"

# Create backend web app (prod)
print_status "Creating backend web app (production)..."
az webapp create \
    --resource-group $RESOURCE_GROUP \
    --plan novitai-word-mcp-prod-plan \
    --name $BACKEND_APP_NAME \
    --deployment-container-image-name $ACR_LOGIN_SERVER/$BACKEND_APP_NAME:latest

# Configure backend environment variables (prod)
print_status "Configuring backend environment variables (production)..."
az webapp config appsettings set \
    --resource-group $RESOURCE_GROUP \
    --name $BACKEND_APP_NAME \
    --settings \
        AZURE_OPENAI_API_KEY="$AZURE_OPENAI_API_KEY" \
        AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
        AZURE_OPENAI_DEPLOYMENT_NAME="$AZURE_OPENAI_DEPLOYMENT_NAME" \
        GOOGLE_API_KEY="$GOOGLE_API_KEY" \
        GOOGLE_CSE_ID="$GOOGLE_CSE_ID" \
        PATENTSVIEW_API_KEY="$PATENTSVIEW_API_KEY" \
        SECRET_KEY="$(openssl rand -base64 32)" \
        ENVIRONMENT="production" \
        DEBUG="false" \
        ALLOWED_ORIGINS="https://$FRONTEND_APP_NAME.azurewebsites.net" \
        ALLOWED_HOSTS="*" \
        AUTH0_DOMAIN="dev-bktskx5kbc655wcl.us.auth0.com" \
        AUTH0_AUDIENCE="https://$BACKEND_APP_NAME.azurewebsites.net"

# Create frontend web app (prod)
print_status "Creating frontend web app (production)..."
az webapp create \
    --resource-group $RESOURCE_GROUP \
    --plan novitai-word-mcp-prod-plan \
    --name $FRONTEND_APP_NAME \
    --deployment-container-image-name $ACR_LOGIN_SERVER/$FRONTEND_APP_NAME:latest

# Configure frontend environment variables (prod)
print_status "Configuring frontend environment variables (production)..."
az webapp config appsettings set \
    --resource-group $RESOURCE_GROUP \
    --name $FRONTEND_APP_NAME \
    --settings \
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

print_success "Deployment completed successfully!"
echo ""
echo "🌐 Your URLs:"
echo "   Development Frontend: https://$FRONTEND_APP_NAME-dev.azurewebsites.net"
echo "   Development Backend:  https://$BACKEND_APP_NAME-dev.azurewebsites.net"
echo "   Production Frontend:  https://$FRONTEND_APP_NAME.azurewebsites.net"
echo "   Production Backend:   https://$BACKEND_APP_NAME.azurewebsites.net"
echo ""
echo "💰 Estimated Monthly Cost: ~$20"
echo "   - Development: Free (F1 tier)"
echo "   - Production: $13 (B1 tier)"
echo "   - Container Registry: $5 (Basic)"
echo "   - No database costs!"
echo ""
echo "🔧 Next Steps:"
echo "   1. Update Auth0 dashboard with your new URLs"
echo "   2. Update manifest.xml with production URL"
echo "   3. Test your deployment!"
