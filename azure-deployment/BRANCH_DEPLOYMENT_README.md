# 🚀 Branch-Based Deployment Strategy

## Overview
This project now uses a **branch-based deployment strategy** where different branches deploy to different environments:

- **`dev` branch** → **Development Environment**
- **`main` branch** → **Production Environment**

## 🌍 Environments

### Development Environment
- **Resource Group**: `novitai-word-mcp-dev-rg`
- **ACR**: `novitaiwordmcpdev.azurecr.io`
- **Backend**: `https://novitai-word-mcp-backend-dev.azurewebsites.net`
- **Frontend**: `https://novitai-word-mcp-frontend-dev.azurewebsites.net`
- **Log Level**: DEBUG
- **Environment**: development

### Production Environment
- **Resource Group**: `novitai-word-mcp-rg`
- **ACR**: `novitaiwordmcp.azurecr.io`
- **Backend**: `https://novitai-word-mcp-backend.azurewebsites.net`
- **Frontend**: `https://novitai-word-mcp-frontend.azurewebsites.net`
- **Log Level**: INFO
- **Environment**: production

## 🔄 Deployment Flow

### Development Deployment
```bash
# Work on development branch
git checkout dev
git add .
git commit -m "Feature: Add new functionality"
git push origin dev
# → Automatically deploys to Development Environment
```

### Production Deployment
```bash
# Merge dev to main for production
git checkout main
git merge dev
git push origin main
# → Automatically deploys to Production Environment
```

## 🛠️ Setup Instructions

### 1. Create Development Environment
```bash
# Run the setup script
chmod +x azure-deployment/setup-dev-environment.sh
./azure-deployment/setup-dev-environment.sh
```

### 2. Update Auth0 Settings
Update your Auth0 application settings to include development URLs:
- **Allowed Callback URLs**: Add `https://novitai-word-mcp-frontend-dev.azurewebsites.net`
- **Allowed Logout URLs**: Add `https://novitai-word-mcp-frontend-dev.azurewebsites.net`
- **Allowed Web Origins**: Add `https://novitai-word-mcp-frontend-dev.azurewebsites.net`

### 3. Update Pipeline Variables
Ensure your Azure DevOps pipeline has the correct service connection:
- `azureServiceConnection`: `novitai-word-mcp-connection`

## 📋 Pipeline Configuration

The pipeline automatically:
1. **Detects the branch** being pushed
2. **Sets environment variables** based on the branch
3. **Builds and pushes** Docker images to the appropriate ACR
4. **Deploys** to the correct App Service
5. **Configures** environment-specific settings

## 🔧 Environment-Specific Settings

### Development
- `ENVIRONMENT=development`
- `LOG_LEVEL=DEBUG`
- Debug logging enabled
- Development Auth0 settings

### Production
- `ENVIRONMENT=production`
- `LOG_LEVEL=INFO`
- Production logging
- Production Auth0 settings

## 🚨 Important Notes

1. **Always test in development first** before merging to main
2. **Development environment** is for testing and development
3. **Production environment** is for live users
4. **Branch protection** can be enabled to require pull requests for main branch
5. **Environment variables** are automatically configured by the pipeline

## 🔍 Monitoring

### Development Environment
- Monitor logs: `az webapp log tail --name novitai-word-mcp-backend-dev --resource-group novitai-word-mcp-dev-rg`
- Health check: `https://novitai-word-mcp-backend-dev.azurewebsites.net/health`

### Production Environment
- Monitor logs: `az webapp log tail --name novitai-word-mcp-backend --resource-group novitai-word-mcp-rg`
- Health check: `https://novitai-word-mcp-backend.azurewebsites.net/health`

## 🎯 Benefits

1. **Safe Development**: Test changes in development before production
2. **Automated Deployment**: No manual deployment steps
3. **Environment Isolation**: Development and production are completely separate
4. **Easy Rollback**: Can easily switch between environments
5. **Branch Protection**: Can require code review before production deployment

## 🚀 Quick Start

1. **Create development environment**: Run `setup-dev-environment.sh`
2. **Start developing**: Work on `dev` branch
3. **Test changes**: Push to `dev` branch (auto-deploys to development)
4. **Deploy to production**: Merge `dev` to `main` (auto-deploys to production)

Ready to go! 🎉
