#!/bin/bash

# Azure Container Apps Deployment Script for Word Add-in MCP
# This script deploys the application to Azure Container Apps

set -e

# Configuration
ENVIRONMENT=${1:-dev}
SUBSCRIPTION_ID=${AZURE_SUBSCRIPTION_ID}
RESOURCE_GROUP="rg-wordaddin-mcp-${ENVIRONMENT}"
LOCATION="East US 2"
ACR_NAME="acrwordaddinmcp${ENVIRONMENT}"
KEY_VAULT_NAME="kv-wordaddin-mcp-${ENVIRONMENT}"

echo "🚀 Deploying Word Add-in MCP to Azure Container Apps"
echo "Environment: $ENVIRONMENT"
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"
echo ""

# Check if Azure CLI is installed and logged in
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed. Please install it first."
    exit 1
fi

if ! az account show &> /dev/null; then
    echo "❌ Not logged into Azure. Please run 'az login' first."
    exit 1
fi

# Set subscription if provided
if [ -n "$SUBSCRIPTION_ID" ]; then
    echo "🔧 Setting subscription to $SUBSCRIPTION_ID"
    az account set --subscription "$SUBSCRIPTION_ID"
fi

# Create resource group if it doesn't exist
echo "📦 Ensuring resource group exists..."
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output none

# Create Azure Container Registry if it doesn't exist
echo "🐳 Ensuring Azure Container Registry exists..."
if ! az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    echo "Creating Azure Container Registry..."
    az acr create \
        --name "$ACR_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --sku Basic \
        --admin-enabled true \
        --output none
fi

# Build and push backend image
echo "🏗️  Building and pushing backend image..."
cd ..
az acr build \
    --registry "$ACR_NAME" \
    --image "wordaddin-backend:$ENVIRONMENT" \
    --file "backend/Dockerfile" \
    backend/

# Build and push frontend image
echo "🏗️  Building and pushing frontend image..."
az acr build \
    --registry "$ACR_NAME" \
    --image "wordaddin-frontend:$ENVIRONMENT" \
    --file "Novitai MCP/Dockerfile" \
    "Novitai MCP/" \
    --build-arg BUILDKIT_INLINE_CACHE=1

cd azure-deployment

# Create Key Vault if it doesn't exist
echo "🔐 Ensuring Key Vault exists..."
if ! az keyvault show --name "$KEY_VAULT_NAME" &> /dev/null; then
    echo "Creating Key Vault..."
    az keyvault create \
        --name "$KEY_VAULT_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --output none
fi

# Check if secrets exist in Key Vault
echo "🔍 Checking Key Vault secrets..."
required_secrets=("azure-openai-api-key" "google-api-key" "secret-key")
missing_secrets=()

for secret in "${required_secrets[@]}"; do
    if ! az keyvault secret show --vault-name "$KEY_VAULT_NAME" --name "$secret" &> /dev/null; then
        missing_secrets+=("$secret")
    fi
done

if [ ${#missing_secrets[@]} -ne 0 ]; then
    echo "❌ Missing required secrets in Key Vault:"
    for secret in "${missing_secrets[@]}"; do
        echo "   - $secret"
    done
    echo ""
    echo "Please add these secrets to Key Vault $KEY_VAULT_NAME before continuing:"
    echo "Example: az keyvault secret set --vault-name $KEY_VAULT_NAME --name azure-openai-api-key --value 'your-key'"
    exit 1
fi

# Update parameters file with actual values
echo "⚙️  Updating deployment parameters..."
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
KV_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.KeyVault/vaults/$KEY_VAULT_NAME"

# Create environment-specific parameters file
cat > "parameters.${ENVIRONMENT}.json" << EOF
{
  "\$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "environment": {
      "value": "$ENVIRONMENT"
    },
    "location": {
      "value": "$LOCATION"
    },
    "resourceGroupName": {
      "value": "$RESOURCE_GROUP"
    },
    "containerRegistryName": {
      "value": "$ACR_NAME"
    },
    "azureOpenAIApiKey": {
      "reference": {
        "keyVault": {
          "id": "$KV_ID"
        },
        "secretName": "azure-openai-api-key"
      }
    },
    "azureOpenAIEndpoint": {
      "value": "$(az keyvault secret show --vault-name $KEY_VAULT_NAME --name azure-openai-endpoint --query value -o tsv 2>/dev/null || echo 'https://your-openai-resource.openai.azure.com/')"
    },
    "googleApiKey": {
      "reference": {
        "keyVault": {
          "id": "$KV_ID"
        },
        "secretName": "google-api-key"
      }
    },
    "googleCSEId": {
      "value": "$(az keyvault secret show --vault-name $KEY_VAULT_NAME --name google-cse-id --query value -o tsv 2>/dev/null || echo 'your-google-cse-id')"
    },
    "patentsViewApiKey": {
      "reference": {
        "keyVault": {
          "id": "$KV_ID"
        },
        "secretName": "patentsview-api-key"
      }
    },
    "secretKey": {
      "reference": {
        "keyVault": {
          "id": "$KV_ID"
        },
        "secretName": "secret-key"
      }
    }
  }
}
EOF

# Deploy the infrastructure
echo "🚀 Deploying infrastructure..."
DEPLOYMENT_NAME="wordaddin-mcp-$(date +%Y%m%d-%H%M%S)"

az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --template-file azure-container-apps.yml \
    --parameters "@parameters.${ENVIRONMENT}.json" \
    --name "$DEPLOYMENT_NAME" \
    --output table

# Get deployment outputs
echo ""
echo "📊 Deployment completed! Getting URLs..."
BACKEND_URL=$(az deployment group show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DEPLOYMENT_NAME" \
    --query properties.outputs.backendUrl.value -o tsv)

FRONTEND_URL=$(az deployment group show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DEPLOYMENT_NAME" \
    --query properties.outputs.frontendUrl.value -o tsv)

echo ""
echo "✅ Deployment successful!"
echo ""
echo "🌐 Application URLs:"
echo "   Backend API: $BACKEND_URL"
echo "   Frontend (Word Add-in): $FRONTEND_URL"
echo ""
echo "📖 Next steps:"
echo "   1. Update your Word Add-in manifest.xml with the frontend URL"
echo "   2. Test the application at $FRONTEND_URL"
echo "   3. Monitor logs: az containerapp logs tail --name wordaddin-backend-$ENVIRONMENT --resource-group $RESOURCE_GROUP"
echo ""
