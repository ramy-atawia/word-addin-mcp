# Azure Deployment Guide for Word Add-in MCP Project

## Overview

This guide provides comprehensive deployment options for the Word Add-in MCP Project on Microsoft Azure. The application consists of:

- **Frontend**: React TypeScript Word Add-in (Office.js)
- **Backend**: FastAPI Python backend with LangChain agent
- **MCP Server**: Python MCP server for tool integration
- **Database**: PostgreSQL
- **Cache**: Redis
- **AI Integration**: Azure OpenAI
- **Storage**: Azure Blob Storage

## Deployment Options

### 1. Azure Container Apps (Recommended)

**Best for**: Microservices architecture with auto-scaling needs

#### Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   MCP Server    │
│   Container     │    │   Container     │    │   Container     │
│   App           │    │   App           │    │   App           │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   Redis Cache   │    │   Blob Storage  │
│   Flexible      │    │   Standard      │    │   Standard LRS  │
│   Server        │    │   Tier          │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### Pros
- ✅ Serverless container hosting
- ✅ Auto-scaling based on HTTP requests
- ✅ Built-in load balancing
- ✅ Easy CI/CD integration
- ✅ Cost-effective for variable workloads
- ✅ Integrated monitoring with Application Insights
- ✅ No infrastructure management

#### Cons
- ❌ Cold start latency (1-2 seconds)
- ❌ Limited control over underlying infrastructure
- ❌ Maximum 4 CPU cores per container
- ❌ 8GB memory limit per container

#### Cost Estimate (Monthly)
- **Container Apps**: ~$50-150 (depending on usage)
- **PostgreSQL Flexible Server**: ~$30-80
- **Redis Cache**: ~$20-50
- **Blob Storage**: ~$5-20
- **Total**: ~$105-300/month

#### Deployment Steps
1. Deploy infrastructure using Bicep template
2. Build and push container images to Azure Container Registry
3. Deploy Container Apps with the images
4. Configure environment variables and secrets
5. Set up monitoring and logging

### 2. Azure App Service (Multi-container)

**Best for**: Traditional web applications with predictable traffic

#### Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    App Service Plan                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │  Frontend   │ │  Backend    │ │    MCP Server       │   │
│  │  App        │ │  App        │ │    App              │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   Redis Cache   │    │   Blob Storage  │
│   Flexible      │    │   Standard      │    │   Standard LRS  │
│   Server        │    │   Tier          │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### Pros
- ✅ Easy deployment and management
- ✅ Built-in CI/CD with GitHub Actions
- ✅ Auto-scaling capabilities
- ✅ Integrated monitoring
- ✅ SSL certificates management
- ✅ Custom domains support

#### Cons
- ❌ Shared resources in Basic/Standard tiers
- ❌ Less flexible than Container Apps
- ❌ Platform-specific limitations
- ❌ Higher cost for dedicated resources

#### Cost Estimate (Monthly)
- **App Service Plan (B1)**: ~$55
- **PostgreSQL Flexible Server**: ~$30-80
- **Redis Cache**: ~$20-50
- **Blob Storage**: ~$5-20
- **Total**: ~$110-205/month

### 3. Azure Kubernetes Service (AKS)

**Best for**: Enterprise-grade, highly scalable deployments

#### Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                        AKS Cluster                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │  Frontend   │ │  Backend    │ │    MCP Server       │   │
│  │  Pods       │ │  Pods       │ │    Pods             │   │
│  │  (3 replicas)│ │  (3 replicas)│ │    (2 replicas)     │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              NGINX Ingress Controller                   │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   Redis Cache   │    │   Blob Storage  │
│   Flexible      │    │   Standard      │    │   Standard LRS  │
│   Server        │    │   Tier          │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### Pros
- ✅ Full control over infrastructure
- ✅ Advanced orchestration and scaling
- ✅ High availability and fault tolerance
- ✅ Enterprise security features
- ✅ Support for complex networking
- ✅ Advanced monitoring with Prometheus/Grafana

#### Cons
- ❌ Complex setup and management
- ❌ Higher operational overhead
- ❌ Requires Kubernetes expertise
- ❌ More expensive
- ❌ Longer deployment times

#### Cost Estimate (Monthly)
- **AKS Cluster (3 nodes)**: ~$150-300
- **PostgreSQL Flexible Server**: ~$30-80
- **Redis Cache**: ~$20-50
- **Blob Storage**: ~$5-20
- **Container Registry**: ~$5-10
- **Total**: ~$210-460/month

### 4. Hybrid Approach (Recommended for Production)

**Best for**: Optimized cost and performance

#### Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   MCP Server    │
│   Static Web    │    │   Container     │    │   Container     │
│   Apps + CDN    │    │   Apps          │    │   Apps          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   Redis Cache   │    │   Blob Storage  │
│   Flexible      │    │   Standard      │    │   Standard LRS  │
│   Server        │    │   Tier          │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### Pros
- ✅ Optimized for each component
- ✅ Cost-effective
- ✅ High performance
- ✅ Global CDN for frontend
- ✅ Serverless backend scaling

#### Cons
- ❌ More complex architecture
- ❌ Multiple deployment pipelines
- ❌ More monitoring points

## Prerequisites

### 1. Azure CLI
```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login to Azure
az login

# Set subscription
az account set --subscription "Your Subscription ID"
```

### 2. Docker
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
```

### 3. Required Azure Resources
- Azure subscription
- Resource group
- Azure Container Registry (for container deployments)
- Azure OpenAI service (for AI functionality)

## Quick Start Deployment

### Option 1: Container Apps (Recommended)

1. **Clone and setup**:
```bash
git clone <repository-url>
cd word-addin-mcp
```

2. **Deploy infrastructure**:
```bash
cd azure-deployment/container-apps
az deployment group create \
  --resource-group your-rg \
  --template-file bicep/main.bicep \
  --parameters environment=prod
```

3. **Build and deploy containers**:
```bash
# Build images
docker build -t wordaddin-mcp-backend:latest ./backend
docker build -t wordaddin-mcp-frontend:latest "./Novitai MCP"
docker build -t wordaddin-mcp-mcp-server:latest ./middleware

# Push to Azure Container Registry
az acr login --name your-registry
docker tag wordaddin-mcp-backend:latest your-registry.azurecr.io/wordaddin-mcp-backend:latest
docker push your-registry.azurecr.io/wordaddin-mcp-backend:latest
```

### Option 2: App Service

1. **Deploy infrastructure**:
```bash
cd azure-deployment/app-service
az deployment group create \
  --resource-group your-rg \
  --template-file arm-template.json \
  --parameters appServiceName=wordaddin-mcp-app
```

2. **Deploy applications**:
```bash
# Deploy backend
az webapp deployment source config-zip \
  --resource-group your-rg \
  --name wordaddin-mcp-app-backend \
  --src backend.zip

# Deploy frontend
az webapp deployment source config-zip \
  --resource-group your-rg \
  --name wordaddin-mcp-app-frontend \
  --src frontend.zip
```

## Environment Variables

### Backend Configuration
```bash
DATABASE_URL=postgresql://user:password@host:5432/database
REDIS_URL=redis://host:6379
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_STORAGE_CONNECTION_STRING=your_storage_connection
ENVIRONMENT=production
```

### Frontend Configuration
```bash
REACT_APP_API_URL=https://your-backend-url
REACT_APP_MCP_SERVER_URL=https://your-mcp-server-url
REACT_APP_ENVIRONMENT=production
```

### MCP Server Configuration
```bash
MCP_SERVER_PORT=9001
MCP_SERVER_HOST=0.0.0.0
ENVIRONMENT=production
```

## Monitoring and Logging

### Application Insights
- Automatic request tracking
- Performance monitoring
- Error tracking and alerting
- Custom metrics and events

### Log Analytics
- Centralized logging
- Query and analyze logs
- Create custom dashboards
- Set up alerts

### Health Checks
- `/health` endpoint for backend
- `/health` endpoint for MCP server
- Frontend health check via load balancer

## Security Considerations

### 1. Network Security
- VNet integration for private networking
- NSG rules for traffic filtering
- Private endpoints for databases

### 2. Authentication & Authorization
- Azure AD integration
- API key management
- Role-based access control

### 3. Data Protection
- Encryption at rest and in transit
- Key management with Azure Key Vault
- Regular security updates

### 4. Compliance
- GDPR compliance
- SOC 2 Type II
- ISO 27001

## Cost Optimization

### 1. Right-sizing Resources
- Monitor actual usage
- Adjust resource sizes accordingly
- Use auto-scaling policies

### 2. Reserved Instances
- 1-year or 3-year commitments
- Up to 72% cost savings
- For predictable workloads

### 3. Spot Instances
- Up to 90% cost savings
- For non-critical workloads
- With proper fault tolerance

### 4. Storage Optimization
- Use appropriate storage tiers
- Implement lifecycle policies
- Regular cleanup of old data

## Troubleshooting

### Common Issues

1. **Container startup failures**
   - Check environment variables
   - Verify image availability
   - Review container logs

2. **Database connection issues**
   - Verify connection strings
   - Check firewall rules
   - Ensure SSL configuration

3. **Performance issues**
   - Monitor resource usage
   - Check scaling policies
   - Review application code

### Debugging Commands

```bash
# Check container logs
az containerapp logs show --name your-app --resource-group your-rg

# Check app service logs
az webapp log tail --name your-app --resource-group your-rg

# Check AKS pods
kubectl get pods -n wordaddin-mcp
kubectl logs -f deployment/backend -n wordaddin-mcp
```

## Support and Resources

- [Azure Container Apps Documentation](https://docs.microsoft.com/en-us/azure/container-apps/)
- [Azure App Service Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [Azure Kubernetes Service Documentation](https://docs.microsoft.com/en-us/azure/aks/)
- [Azure DevOps Documentation](https://docs.microsoft.com/en-us/azure/devops/)

## Conclusion

Choose the deployment option that best fits your requirements:

- **Container Apps**: Best for most use cases with auto-scaling needs
- **App Service**: Best for traditional web applications
- **AKS**: Best for enterprise-grade, highly scalable deployments
- **Hybrid**: Best for optimized cost and performance

Each option provides different trade-offs between complexity, cost, and control. Start with Container Apps for most scenarios and migrate to AKS as your requirements grow.