# Manifest Environment Configuration

This document explains how to use the different manifest files for various deployment environments.

## 📁 **Manifest Files**

### **1. `manifest.xml` (Default - Dev Environment)**
- **Environment:** Development
- **Frontend:** `https://novitai-word-mcp-frontend-dev.azurewebsites.net`
- **Backend:** `https://novitai-word-mcp-backend-dev.azurewebsites.net`
- **Display Name:** "Novitai MCP (Dev)"
- **Use Case:** Default development environment

### **2. `manifest.local.xml` (Local Development)**
- **Environment:** Local Development
- **Frontend:** `https://localhost:3000`
- **Backend:** `https://localhost:9000`
- **Display Name:** "Novitai MCP (Local)"
- **Use Case:** Local development with Docker or npm dev server

### **3. `manifest.dev.xml` (Development Environment)**
- **Environment:** Development
- **Frontend:** `https://novitai-word-mcp-frontend-dev.azurewebsites.net`
- **Backend:** `https://novitai-word-mcp-backend-dev.azurewebsites.net`
- **Display Name:** "Novitai MCP (Dev)"
- **Use Case:** Azure development deployment

### **4. `manifest.prod.xml` (Production Environment)**
- **Environment:** Production
- **Frontend:** `https://novitai-word-mcp-frontend.azurewebsites.net`
- **Backend:** `https://novitai-word-mcp-backend.azurewebsites.net`
- **Display Name:** "Novitai MCP"
- **Use Case:** Production deployment

## 🔄 **How to Switch Environments**

### **For Local Development:**
```bash
# Copy local manifest to main manifest
cp manifest.local.xml manifest.xml
```

### **For Development Environment:**
```bash
# Copy dev manifest to main manifest
cp manifest.dev.xml manifest.xml
```

### **For Production Environment:**
```bash
# Copy production manifest to main manifest
cp manifest.prod.xml manifest.xml
```

## 🚀 **Deployment Workflow**

### **1. Local Development**
1. Use `manifest.local.xml` as `manifest.xml`
2. Start local Docker environment: `./docker-local start`
3. Frontend runs on `https://localhost:3000`
4. Backend runs on `https://localhost:9000`

### **2. Development Deployment**
1. Use `manifest.dev.xml` as `manifest.xml`
2. Push to `dev` branch
3. Azure automatically deploys to dev environment
4. Frontend: `https://novitai-word-mcp-frontend-dev.azurewebsites.net`
5. Backend: `https://novitai-word-mcp-backend-dev.azurewebsites.net`

### **3. Production Deployment**
1. Use `manifest.prod.xml` as `manifest.xml`
2. Push to `main` branch
3. Azure automatically deploys to production
4. Frontend: `https://novitai-word-mcp-frontend.azurewebsites.net`
5. Backend: `https://novitai-word-mcp-backend.azurewebsites.net`

## 🔧 **Environment-Specific Features**

### **Local Environment:**
- Includes both localhost domains for frontend and backend
- Clear "(Local)" indicators in UI text
- Optimized for local development workflow

### **Development Environment:**
- Uses Azure dev URLs
- Clear "(Dev)" indicators in UI text
- Includes development-specific descriptions

### **Production Environment:**
- Uses production Azure URLs
- Clean, professional naming without environment indicators
- Production-optimized descriptions

## 📋 **Best Practices**

1. **Always commit the correct manifest.xml** for the target environment
2. **Test locally first** with `manifest.local.xml`
3. **Use dev environment** for staging and testing
4. **Only use production** for live releases
5. **Keep all manifest files in sync** with any structural changes

## 🐛 **Troubleshooting**

### **Common Issues:**
- **CORS errors:** Check that AppDomains include both frontend and backend URLs
- **Mixed content errors:** Ensure all URLs use HTTPS
- **Add-in not loading:** Verify the SourceLocation URL is accessible
- **Icons not showing:** Check that icon URLs are correct and accessible

### **Debug Steps:**
1. Verify the manifest.xml matches your target environment
2. Check that all URLs are accessible in a browser
3. Validate the manifest using Office Add-in validation tools
4. Check browser console for any loading errors
