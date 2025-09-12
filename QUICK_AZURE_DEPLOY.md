# 🚀 Quick Azure Deployment - $35/month

## ⚡ **5-Minute Deployment**

### **Step 1: Verify Your .env File**
Make sure your `.env` file contains all required API keys:
```bash
# Check if .env file exists and has the right keys
cat .env | grep -E "(AZURE_OPENAI|GOOGLE|PATENTSVIEW)"
```

### **Step 2: Login to Azure**
```bash
az login
az account set --subscription "Your Subscription Name"
```

### **Step 3: Deploy Everything**
```bash
# The script will automatically load your .env file
./azure-deployment/deploy-budget.sh
```

**That's it!** 🎉

## 🌐 **Your URLs After Deployment**

### **Development Environment (Free)**
- **Frontend**: `https://novitai-word-mcp-frontend-dev.azurewebsites.net`
- **Backend**: `https://novitai-word-mcp-backend-dev.azurewebsites.net`

### **Production Environment**
- **Frontend**: `https://novitai-word-mcp-frontend.azurewebsites.net`
- **Backend**: `https://novitai-word-mcp-backend.azurewebsites.net`

## 🔐 **Auth0 Configuration**

### **Update Auth0 Dashboard:**
1. Go to [Auth0 Dashboard](https://manage.auth0.com/)
2. Navigate to **Applications** → **Your App**
3. Update **Allowed Callback URLs**:
   ```
   https://novitai-word-mcp-frontend.azurewebsites.net/auth-callback.html
   https://novitai-word-mcp-frontend-dev.azurewebsites.net/auth-callback.html
   ```
4. Update **Allowed Web Origins**:
   ```
   https://novitai-word-mcp-frontend.azurewebsites.net
   https://novitai-word-mcp-frontend-dev.azurewebsites.net
   ```
5. Update **Allowed Origins (CORS)**:
   ```
   https://novitai-word-mcp-frontend.azurewebsites.net
   https://novitai-word-mcp-frontend-dev.azurewebsites.net
   ```

## 📱 **Update Word Add-in Manifest**

### **Update `Novitai MCP/manifest.xml`:**
```xml
<!-- Change these URLs to your production URLs -->
<SourceLocation DefaultValue="https://novitai-word-mcp-frontend.azurewebsites.net/taskpane.html"/>
<AppDomain>https://novitai-word-mcp-frontend.azurewebsites.net</AppDomain>
```

## 💰 **Cost Breakdown**

| Service | Tier | Monthly Cost |
|---------|------|--------------|
| App Service Plan (Dev) | F1 (Free) | $0 |
| App Service Plan (Prod) | B1 | $13 |
| PostgreSQL Database | Basic | $25 |
| Redis Cache | C0 | $16 |
| Container Registry | Basic | $5 |
| **Total** | | **$59/month** |

*Note: We can optimize this further to get under $50 if needed*

## 🧪 **Test Your Deployment**

### **Test Backend:**
```bash
curl https://novitai-word-mcp-backend.azurewebsites.net/health
```

### **Test Frontend:**
```bash
curl https://novitai-word-mcp-frontend.azurewebsites.net/taskpane.html
```

### **Test Auth Flow:**
```bash
curl https://novitai-word-mcp-frontend.azurewebsites.net/login-dialog.html
```

## 🔄 **Update Process**

### **To Update Your App:**
1. Make code changes
2. Run: `./build.sh`
3. Push to Azure: `./azure-deployment/deploy-budget.sh`
4. Azure will automatically deploy the new version

## 🚨 **Troubleshooting**

### **Common Issues:**

#### 1. **"Not logged in to Azure"**
```bash
az login
```

#### 2. **"Resource group already exists"**
```bash
# Use different name
./azure-deployment/deploy-budget.sh my-unique-rg-name
```

#### 3. **"Container registry name not available"**
```bash
# Use different name
./azure-deployment/deploy-budget.sh my-rg my-location my-unique-acr
```

#### 4. **Auth0 not working**
- Check Auth0 dashboard URLs
- Verify backend URLs in Auth0 settings
- Check browser console for CORS errors

## 📊 **Monitoring**

### **Check Logs:**
```bash
# Backend logs
az webapp log tail --resource-group novitai-word-mcp-rg --name word-addin-backend

# Frontend logs
az webapp log tail --resource-group novitai-word-mcp-rg --name word-addin-frontend
```

### **Check Status:**
```bash
# All services
az webapp list --resource-group novitai-word-mcp-rg --output table
```

## 🎯 **Next Steps**

1. **Deploy**: Run the deployment script
2. **Test**: Verify all URLs work
3. **Update Auth0**: Configure with new URLs
4. **Update Manifest**: Point to production URL
5. **Load in Word**: Test the complete flow

---

**Need help?** Check the full `AZURE_DEPLOYMENT_GUIDE.md` for detailed instructions.

**Ready to deploy?** Just run the commands above! 🚀
