# Port Configuration Update Summary

## Overview
Updated the frontend development server from port 3000 to port 3001 to resolve port conflicts and ensure consistent configuration across the project.

## Changes Made

### 1. Frontend Configuration
- **File**: `frontend/package.json`
  - Updated `start` script to use `PORT=3001`
  - Added `homepage` field: `"http://localhost:3001"`
  - Added `start:dev` script for flexible port usage

### 2. Backend Configuration
- **File**: `backend/app/core/config.py`
  - Updated `ALLOWED_ORIGINS`: `["http://localhost:3001", "https://yourdomain.com"]`
  - Updated `FRONTEND_URL`: `"http://localhost:3001"`

### 3. Test Files
- **File**: `backend/tests/test_security_middleware.py`
  - Updated CORS test assertions to use port 3001
  - Fixed 2 occurrences of port 3000 in test headers
- **File**: `tests/backend/test_health.py`
  - Updated health check test to use port 3001

### 4. Docker Configuration
- **File**: `docker-compose.yml`
  - Updated frontend port mapping: `"3001:3000"`
  - Updated Grafana port mapping: `"3002:3000"` (to avoid conflict)

### 5. Documentation
- **File**: `frontend/README.md`
  - Updated development server URL to port 3001

## Port Configuration Summary

| Service | External Port | Internal Port | Purpose |
|---------|---------------|---------------|---------|
| Frontend | 3001 | 3000 | React development server |
| Backend | 9000 | 9000 | FastAPI backend |
| MCP Server | 9001 | 9001 | MCP protocol server |
| Grafana | 3002 | 3000 | Monitoring dashboard |
| Nginx | 80/443 | 80/443 | Reverse proxy |

## Development Commands

### Start Frontend (Port 3001)
```bash
cd frontend
npm start  # Uses port 3001 by default
```

### Start Frontend (Custom Port)
```bash
cd frontend
npm run start:dev  # Uses default port or PORT environment variable
```

### Start Backend
```bash
cd backend
uvicorn app.main:app --reload --port 9000
```

### Start MCP Server
```bash
cd backend
python -m app.mcp.server --port 9001
```

## Environment Variables

### Frontend (.env)
```bash
PORT=3001
REACT_APP_API_URL=http://localhost:9000
REACT_APP_MCP_SERVER_URL=http://localhost:9001
REACT_APP_ENVIRONMENT=development
```

### Backend
```bash
FRONTEND_URL=http://localhost:3001
ALLOWED_ORIGINS=["http://localhost:3001", "https://yourdomain.com"]
```

## Testing

All tests have been updated to use the new port configuration. Run the test suite to verify:

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```

## Notes

- The internal container ports remain unchanged (3000) for Docker compatibility
- External port mappings have been updated to avoid conflicts
- CORS configuration has been updated to allow the new frontend port
- All test assertions have been updated to reflect the new port
- The frontend will now start on port 3001 by default
