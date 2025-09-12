# Word Add-in MCP - Docker Deployment Guide

This guide covers containerization and deployment of the Word Add-in MCP application for both local development and Azure production environments.

## 🏗️ Architecture Overview

The application consists of:
- **Backend**: FastAPI Python application with integrated MCP functionality
- **Frontend**: React Word Add-in with HTTPS support
- **Database**: PostgreSQL for data persistence
- **Cache**: Redis for session and cache management
- **SSL**: Automated certificate generation for HTTPS compliance

## 🚀 Quick Start (Local Development)

### Prerequisites
1. Docker and Docker Compose installed
2. `.env` file configured with API keys
3. Ports 3000, 9000, 5432, 6379 available

### Start Development Environment
```bash
# Start development environment with hot reloading
./docker-scripts/dev-start.sh

# Access points:
# - Word Add-in: https://localhost:3000
# - Backend API: http://localhost:9000
# - API Docs: http://localhost:9000/docs
```

### Stop Development Environment
```bash
./docker-scripts/stop.sh
```

## 🔧 Docker Configuration

### Development vs Production

#### Development Mode
- Hot reloading enabled for both backend and frontend
- Volume mounts for live code changes
- Debug logging enabled
- Self-signed SSL certificates
- Exposed database and Redis ports

#### Production Mode
- Optimized multi-stage builds
- No volume mounts (immutable containers)
- Production-grade nginx configuration
- Health checks and auto-restart
- Proper SSL termination

### Container Services

#### Backend (`wordaddin-backend`)
- **Base**: Python 3.12 slim
- **Port**: 9000
- **Features**: FastAPI + MCP orchestrator, health checks
- **Volumes**: logs, uploads
- **Dependencies**: PostgreSQL, Redis

#### Frontend (`wordaddin-frontend-dev/prod`)
- **Development**: Node.js with webpack-dev-server
- **Production**: nginx with optimized static assets
- **Port**: 3000 (HTTPS)
- **Features**: React SPA, Office.js integration

#### Database (`postgres`)
- **Image**: PostgreSQL 15 Alpine
- **Port**: 5432
- **Volume**: Persistent data storage
- **Security**: Authentication required

#### Cache (`redis`)
- **Image**: Redis 7 Alpine
- **Port**: 6379
- **Volume**: Persistent cache storage

#### SSL Generator (`ssl-generator`)
- **Purpose**: Generate self-signed certificates for local development
- **Runs**: Once on startup
- **Volume**: Shared certificate storage

## 🌐 Local Development

### Environment Setup

1. **Copy environment template**:
   ```bash
   cp env.example .env
   ```

2. **Configure required API keys** in `.env`:
   ```env
   AZURE_OPENAI_API_KEY=your_azure_openai_api_key
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   GOOGLE_API_KEY=your_google_api_key
   GOOGLE_CSE_ID=your_google_cse_id
   SECRET_KEY=your_32_character_secret_key
   ```

3. **Start development environment**:
   ```bash
   ./docker-scripts/dev-start.sh
   ```

### Development Workflow

1. **Code Changes**: Edit files in `backend/` or `Novitai MCP/`
2. **Auto-reload**: Changes automatically reflected in containers
3. **Logs**: View with `docker-compose logs -f [service-name]`
4. **Health Check**: `./docker-scripts/health-check.sh`

### Troubleshooting Development

```bash
# View all container status
docker-compose ps

# Check specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend-dev

# Restart specific service
docker-compose restart backend

# Access container shell
docker-compose exec backend bash
docker-compose exec frontend-dev sh

# Clean environment (removes all data)
./docker-scripts/clean.sh
```

## ☁️ Azure Deployment

### Prerequisites
1. Azure CLI installed and configured
2. Azure subscription with Container Apps enabled
3. API keys stored in Azure Key Vault

### Deploy to Azure

1. **Login to Azure**:
   ```bash
   az login
   az account set --subscription "your-subscription-id"
   ```

2. **Set up Key Vault secrets**:
   ```bash
   # Create or use existing Key Vault
   az keyvault create --name kv-wordaddin-mcp-dev --resource-group rg-wordaddin-mcp-dev

   # Add required secrets
   az keyvault secret set --vault-name kv-wordaddin-mcp-dev --name azure-openai-api-key --value "your-key"
   az keyvault secret set --vault-name kv-wordaddin-mcp-dev --name google-api-key --value "your-key"
   az keyvault secret set --vault-name kv-wordaddin-mcp-dev --name secret-key --value "your-32-char-secret"
   ```

3. **Deploy application**:
   ```bash
   cd azure-deployment
   ./deploy.sh dev  # or 'staging', 'prod'
   ```

### Azure Architecture

The Azure deployment creates:
- **Container Apps Environment**: Managed Kubernetes environment
- **Container Apps**: Backend and frontend applications
- **PostgreSQL Flexible Server**: Managed database
- **Redis Cache**: Managed cache service
- **Log Analytics**: Centralized logging
- **Key Vault**: Secret management
- **Container Registry**: Private Docker registry

### Azure Configuration

#### Environment Variables
- Secrets stored in Azure Key Vault
- Configuration via Container Apps environment variables
- Automatic secret injection into containers

#### Networking
- Private virtual network for database/cache
- Public ingress for frontend and backend
- HTTPS termination at Container Apps level

#### Scaling
- Auto-scaling based on HTTP requests
- Min/max replica configuration
- Resource limits per container

## 🔐 SSL/HTTPS Configuration

### Local Development
- Self-signed certificates generated automatically
- Office.js compatible certificate structure
- Certificates stored in Docker volume for reuse

### Azure Production
- Azure manages SSL termination
- Custom domain support available
- Automatic certificate renewal

## 📊 Monitoring & Health Checks

### Health Endpoints
- Backend: `http://localhost:9000/health`
- Frontend: `https://localhost:3000/health` (production)

### Monitoring Tools
```bash
# Check all service health
./docker-scripts/health-check.sh

# View logs
docker-compose logs -f

# Monitor resource usage
docker stats
```

### Azure Monitoring
- Application Insights integration
- Log Analytics workspace
- Container Apps metrics
- Custom dashboards available

## 🔧 Customization

### Development Environment

1. **Modify `docker-compose.dev.yml`** for development overrides
2. **Update environment variables** in `.env`
3. **Adjust port mappings** in `docker-compose.yml`

### Production Environment

1. **Modify `Dockerfile`** for build optimizations
2. **Update Azure templates** in `azure-deployment/`
3. **Adjust scaling parameters** in Container Apps configuration

## 📝 Important Notes

### MCP Functionality
- MCP orchestrator runs within the backend container
- No separate MCP server needed (integrated architecture)
- All MCP tools and external server connections preserved

### Word Add-in Compatibility
- HTTPS required for Office.js loading
- Manifest.xml must point to correct URLs
- CORS configured for Office applications

### Data Persistence
- Database and cache data persisted in Docker volumes
- Logs accessible via mounted volumes
- Upload directory preserved

### Security
- API keys never stored in images
- Secrets managed via environment variables
- Non-root users in containers
- Security headers configured

## 🆘 Support & Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 3000, 9000, 5432, 6379 are available
2. **SSL certificate errors**: Try `./docker-scripts/clean.sh` and restart
3. **API key errors**: Verify `.env` file configuration
4. **Memory issues**: Increase Docker memory allocation

### Logs & Debugging
```bash
# View all logs
docker-compose logs

# Debug specific service
docker-compose exec backend python -c "from app.main import app; print('Backend OK')"

# Check environment variables
docker-compose exec backend env | grep AZURE
```

### Performance Optimization
- Use production mode for better performance
- Monitor resource usage with `docker stats`
- Adjust container resource limits as needed

For additional support, check the application logs and health endpoints first.
