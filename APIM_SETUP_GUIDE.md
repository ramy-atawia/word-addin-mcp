# Azure API Management Setup Guide

## ✅ What We've Completed

1. **APIM Instance Created**: `novitai-word-mcp-apim`
2. **API Imported**: `word-addin-mcp-api` 
3. **JWT Policy Created**: `apim-jwt-policy.xml`

## 🔧 Manual Configuration Steps

### Step 1: Access APIM Portal
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **API Management** → **novitai-word-mcp-apim**
3. Click **APIs** → **Word Add-in MCP API**

### Step 2: Configure JWT Validation Policy
1. Click **Design** tab
2. Click **</>** (Code view) under **Inbound processing**
3. Replace the content with:

```xml
<policies>
    <inbound>
        <!-- JWT Validation Policy for Auth0 -->
        <validate-jwt 
            header-name="Authorization" 
            require-scheme="Bearer"
            failed-validation-httpcode="401" 
            failed-validation-error-message="Unauthorized. Access token is missing or invalid.">
            
            <!-- Auth0 OpenID Configuration -->
            <openid-config url="https://dev-bktskx5kbc655wcl.us.auth0.com/.well-known/openid_configuration" />
            
            <!-- Your Auth0 Audience -->
            <audiences>
                <audience>INws849yDXaC6MZVXNlMJi6CZC4nx6U</audience>
            </audiences>
            
            <!-- Auth0 Issuer -->
            <issuers>
                <issuer>https://dev-bktskx5kbc655wcl.us.auth0.com/</issuer>
            </issuers>
            
            <!-- Additional Security Settings -->
            <required-claims>
                <claim name="aud" match="all">
                    <value>INws849yDXaC6MZVXNlMJi6CZC4nx6U</value>
                </claim>
            </required-claims>
        </validate-jwt>
    </inbound>
    <backend>
        <forward-request />
    </backend>
    <outbound />
    <on-error />
</policies>
```

4. Click **Save**

### Step 3: Configure Backend
1. Click **Settings** tab
2. Set **Web service URL** to: `http://localhost:9000`
3. Set **API URL suffix** to: `api`
4. Click **Save**

## 🧪 Testing the Setup

### Test 1: Without Token (Should Fail)
```bash
curl https://novitai-word-mcp-apim.azure-api.net/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "context": {}}'
```
**Expected**: `401 Unauthorized`

### Test 2: With Valid Auth0 Token (Should Work)
```bash
curl https://novitai-word-mcp-apim.azure-api.net/api/agent/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_AUTH0_TOKEN" \
  -d '{"message": "test", "context": {}}'
```
**Expected**: `200 OK` with response

## 🔄 Next Steps

1. **Remove JWT validation from your FastAPI backend** (APIM handles it now)
2. **Update your frontend** to use APIM URL instead of direct backend
3. **Test with real Auth0 tokens**
4. **Monitor usage and costs** in Azure Portal

## 📊 APIM Gateway URL
**Your API is now available at:**
`https://novitai-word-mcp-apim.azure-api.net/api`

## 💰 Cost Monitoring
- Check costs in **Azure Portal** → **Cost Management**
- Monitor API calls in **APIM** → **Analytics**
- Set up billing alerts if needed
