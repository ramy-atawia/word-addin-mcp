# Docker Local Development

This project now supports one-command local development using Docker Compose.

## Quick Start

```bash
# Start everything
./docker-local start

# Stop everything  
./docker-local stop

# Restart everything
./docker-local restart
```

## Available Commands

| Command | Description |
|---------|-------------|
| `./docker-local start` | Start all services (default) |
| `./docker-local stop` | Stop all services |
| `./docker-local restart` | Restart all services |
| `./docker-local status` | Show service status |
| `./docker-local logs` | Show logs for all services |
| `./docker-local logs [service]` | Show logs for specific service |
| `./docker-local build` | Build all services |
| `./docker-local cleanup` | Stop services and clean up Docker resources |
| `./docker-local help` | Show help message |

## Services

When running, the following services are available:

- **Backend API**: http://localhost:9000
- **Frontend**: https://localhost:3000
- **Database**: localhost:5432
- **Redis**: localhost:6379

## Environment Variables

All environment variables are automatically configured for local development:

- Auth0 domain and credentials
- Database connections
- API endpoints
- CORS settings

## Development Features

- **Hot Reload**: Frontend automatically reloads on code changes
- **HTTPS**: Automatic SSL certificates for Office Add-in compatibility
- **Health Checks**: All services include health monitoring
- **Volume Mounting**: Source code is mounted for live development
- **Network Isolation**: Services communicate through Docker network

## Troubleshooting

### Services won't start
```bash
# Check Docker is running
docker info

# Check service status
./docker-local status

# View logs
./docker-local logs
```

### Port conflicts
```bash
# Stop all services
./docker-local stop

# Clean up Docker resources
./docker-local cleanup

# Start fresh
./docker-local start
```

### SSL certificate issues
```bash
# The SSL generator service automatically creates certificates
# If you have issues, check the ssl-generator logs:
./docker-local logs ssl-generator
```

## Production vs Local

- **Local**: Uses `docker-compose.override.yml` for development settings
- **Production**: Uses standard `docker-compose.yml` with production settings
- **Dev/Staging**: Deployed via GitHub Actions to Azure

## File Structure

```
word-addin-mcp/
├── docker-local              # Main convenience script
├── docker-compose.yml        # Base configuration
├── docker-compose.override.yml # Local development overrides
└── DOCKER_LOCAL_README.md    # This file
```
