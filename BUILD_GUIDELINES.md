# 🚀 Build Guidelines for Word Add-in MCP

This document provides comprehensive guidelines for building, deploying, and running the Word Add-in MCP project.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Build Process](#build-process)
- [Development Setup](#development-setup)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)
- [File Structure](#file-structure)

## 🔧 Prerequisites

### Required Software
- **Node.js** (v16+)
- **Docker & Docker Compose**
- **Office Add-in Development Certificates**
- **API Keys** (Azure OpenAI, Google, PatentsView)

### Install Office Add-in Certificates
```bash
# Install Office Add-in development certificates
npx office-addin-dev-certs install

# Or install for all users (requires admin)
npx office-addin-dev-certs install --machine
```

## 🏗️ Build Process

### 1. Frontend Build

#### Standard Build
```bash
cd "Novitai MCP"
npm install
npm run build
```

#### Development Build with Hot Reload
```bash
cd "Novitai MCP"
npm run start:dev
```

### 2. Critical Post-Build Steps

**⚠️ IMPORTANT: These steps are REQUIRED after every build!**

```bash
# Copy authentication files to dist directory
cp public/login-dialog.html dist/
cp public/auth-callback.html dist/

# Copy logo with correct name
cp dist/assets/logo-filled.png dist/assets/novitai-logo.png

# Verify all files are in place
ls -la dist/ | grep -E "(login-dialog|auth-callback|novitai-logo)"
```

### 3. Backend Build

#### Docker Build
```bash
# Build and start all services
docker-compose up -d

# Or build specific service
docker-compose build backend
```

#### Local Development
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 9000
```

## 🚀 Development Setup

### Option 1: HTTPS Server (Recommended for Word Add-in)
```bash
cd "Novitai MCP"
node https_server.js
```
- **URL**: `https://localhost:3000`
- **Features**: Full HTTPS with Office.js certificates
- **Best for**: Word Add-in development and testing

### Option 2: Webpack Dev Server
```bash
cd "Novitai MCP"
npm run start:dev
```
- **URL**: `https://localhost:3000`
- **Features**: Hot reloading, development mode
- **Best for**: Frontend development

### Option 3: Docker Development
```bash
# Start all services
docker-compose up -d

# Start only frontend
docker-compose up frontend-dev
```

## 🏭 Production Deployment

### 1. Build Production Assets
```bash
cd "Novitai MCP"
npm run build

# Copy required files
cp public/login-dialog.html dist/
cp public/auth-callback.html dist/
cp dist/assets/logo-filled.png dist/assets/novitai-logo.png
```

### 2. Deploy with Docker
```bash
# Build production images
docker-compose -f docker-compose.yml build

# Start production services
docker-compose -f docker-compose.yml up -d
```

### 3. Verify Deployment
```bash
# Check frontend
curl -I https://localhost:3000/taskpane.html

# Check backend
curl -s http://localhost:9000/health

# Check auth files
curl -I https://localhost:3000/login-dialog.html
curl -I https://localhost:3000/auth-callback.html
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Missing Authentication Files
**Error**: `File not found: /login-dialog.html`
**Solution**:
```bash
cp public/login-dialog.html dist/
cp public/auth-callback.html dist/
```

#### 2. Missing Logo
**Error**: `File not found: /assets/novitai-logo.png`
**Solution**:
```bash
cp dist/assets/logo-filled.png dist/assets/novitai-logo.png
```

#### 3. CORS Issues
**Error**: `Access to fetch has been blocked by CORS policy`
**Solution**: Check backend CORS configuration in `backend/app/main.py`

#### 4. TypeScript Compilation Errors
**Error**: `Property 'mailbox' does not exist on type 'typeof context'`
**Solution**: Ensure `src/types/office.d.ts` has proper Office.js type definitions

#### 5. Port Conflicts
**Error**: `Port 3000 is already in use`
**Solution**:
```bash
# Kill processes on port 3000
lsof -ti:3000 | xargs kill -9

# Or use different port
npm run start:dev -- --port 3001
```

### Health Checks

#### Frontend Health
```bash
curl -I https://localhost:3000/taskpane.html
# Expected: HTTP/1.1 200 OK
```

#### Backend Health
```bash
curl -s http://localhost:9000/health
# Expected: {"status":"healthy",...}
```

#### Authentication Flow
```bash
curl -I https://localhost:3000/login-dialog.html
curl -I https://localhost:3000/auth-callback.html
# Expected: HTTP/1.1 200 OK for both
```

## 📁 File Structure

### Critical Files That Must Be Copied
```
public/
├── login-dialog.html          → dist/login-dialog.html
├── auth-callback.html         → dist/auth-callback.html
└── assets/
    └── novitai-logo.png       → dist/assets/novitai-logo.png
```

### Build Output Structure
```
dist/
├── taskpane.html              # Main Word Add-in UI
├── commands.html              # Office commands
├── login-dialog.html          # Auth0 login dialog (COPIED)
├── auth-callback.html         # Auth0 callback handler (COPIED)
├── taskpane.js               # Main application bundle
├── polyfill.js               # Browser polyfills
├── react.js                  # React library
├── manifest.xml              # Office Add-in manifest
└── assets/
    ├── novitai-logo.png      # Logo (COPIED/RENAMED)
    ├── icon-*.png            # Office Add-in icons
    └── logo-filled.png       # Original logo
```

## 🔄 Automated Build Script

Create `build.sh` for automated builds:

```bash
#!/bin/bash
set -e

echo "🏗️ Building Word Add-in MCP..."

# Build frontend
echo "📦 Building frontend..."
cd "Novitai MCP"
npm install
npm run build

# Copy required files
echo "📋 Copying authentication files..."
cp public/login-dialog.html dist/
cp public/auth-callback.html dist/
cp dist/assets/logo-filled.png dist/assets/novitai-logo.png

# Verify build
echo "✅ Verifying build..."
ls -la dist/ | grep -E "(login-dialog|auth-callback|novitai-logo)"

echo "🎉 Build complete!"
echo "🌐 Frontend: https://localhost:3000"
echo "🔧 Backend: http://localhost:9000"
```

Make it executable:
```bash
chmod +x build.sh
./build.sh
```

## 📝 Development Workflow

### 1. Daily Development
```bash
# Start backend
docker-compose up -d

# Start frontend
cd "Novitai MCP"
node https_server.js
```

### 2. After Code Changes
```bash
# Rebuild if needed
npm run build

# Copy files
cp public/login-dialog.html dist/
cp public/auth-callback.html dist/
cp dist/assets/logo-filled.png dist/assets/novitai-logo.png
```

### 3. Testing
```bash
# Test frontend
curl -I https://localhost:3000/taskpane.html

# Test backend
curl -s http://localhost:9000/health

# Test auth flow
curl -I https://localhost:3000/login-dialog.html
```

## 🎯 Word Add-in Loading

### 1. Load in Microsoft Word
1. Open **Microsoft Word**
2. Go to **Insert** → **Add-ins** → **My Add-ins**
3. Click **Upload My Add-in**
4. Select `Novitai MCP/manifest.xml`
5. Click **Upload**

### 2. Access the Add-in
- **URL**: `https://localhost:3000/taskpane.html`
- **Manifest**: `Novitai MCP/manifest.xml`

## 🔐 Environment Variables

### Frontend (.env)
```bash
REACT_APP_API_BASE_URL=http://localhost:9000
```

### Backend (.env)
```bash
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=your_endpoint_here
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_here
GOOGLE_API_KEY=your_key_here
GOOGLE_CSE_ID=your_cse_id_here
PATENTSVIEW_API_KEY=your_key_here
```

## 📊 Monitoring

### Logs
```bash
# Frontend logs
tail -f "Novitai MCP/logs/*.log"

# Backend logs
docker-compose logs -f backend

# All services
docker-compose logs -f
```

### Performance
```bash
# Check bundle size
ls -lh dist/taskpane.js

# Check memory usage
docker stats
```

---

## 🚨 Critical Reminders

1. **ALWAYS copy auth files after build**
2. **ALWAYS copy logo with correct name**
3. **ALWAYS test auth flow after deployment**
4. **ALWAYS verify HTTPS certificates**
5. **ALWAYS check CORS configuration**

## 📞 Support

If you encounter issues:
1. Check this guide first
2. Verify all prerequisites are installed
3. Check logs for specific error messages
4. Ensure all required files are copied to `dist/`
5. Test each component individually

---

**Last Updated**: September 2025  
**Version**: 1.0.0
