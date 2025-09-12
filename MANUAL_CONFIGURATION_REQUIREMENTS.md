# Manual Configuration Requirements

## GitHub Secrets Configuration

The following secrets must be configured in your GitHub repository for the workflow to function properly:

### Required GitHub Secrets

#### Azure Service Principal
```bash
AZURE_CREDENTIALS
```
**Value**: JSON string containing:
```json
{
  "clientId": "your-service-principal-client-id",
  "clientSecret": "your-service-principal-secret",
  "subscriptionId": "your-azure-subscription-id",
  "tenantId": "your-azure-tenant-id"
}
```

#### Container Registry
```bash
ACR_USERNAME=novitaiwordmcp
ACR_PASSWORD=[ACR Admin Password]
```

#### API Keys (for development environment)
```bash
AZURE_OPENAI_API_KEY=[YOUR_AZURE_OPENAI_API_KEY]
AZURE_OPENAI_ENDPOINT=[YOUR_AZURE_OPENAI_ENDPOINT]
GOOGLE_API_KEY=[YOUR_GOOGLE_API_KEY]
GOOGLE_CSE_ID=[YOUR_GOOGLE_CSE_ID]
PATENTSVIEW_API_KEY=[YOUR_PATENTSVIEW_API_KEY]
```

## How to Set GitHub Secrets

1. Go to your GitHub repository
2. Click on **Settings** tab
3. Click on **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add each secret with the exact name and value listed above

## Azure Service Principal Setup

If you don't have a service principal, create one:

```bash
# Login to Azure
az login

# Create service principal
az ad sp create-for-rbac --name "github-actions-word-mcp" --role contributor --scopes /subscriptions/{subscription-id}/resourceGroups/novitai-word-mcp-rg --sdk-auth
```

Copy the JSON output and use it as the `AZURE_CREDENTIALS` secret.

## ACR Admin Password

Get the ACR admin password:

```bash
az acr credential show --name novitaiwordmcp --query "passwords[0].value" --output tsv
```

Use this value for the `ACR_PASSWORD` secret.

## Verification Steps

After setting up the secrets:

1. **Test the workflow**: Push to the `dev` branch to trigger deployment
2. **Check deployment logs**: Monitor the GitHub Actions workflow
3. **Verify endpoints**: 
   - Backend: `https://novitai-word-mcp-backend-dev.azurewebsites.net/health`
   - Frontend: `https://novitai-word-mcp-frontend-dev.azurewebsites.net`

## Troubleshooting

### Common Issues

1. **"Azure login failed"**: Check `AZURE_CREDENTIALS` secret format
2. **"ACR authentication failed"**: Verify `ACR_USERNAME` and `ACR_PASSWORD`
3. **"Environment variables not set"**: Check if all API key secrets are configured
4. **"Build failed"**: Ensure all build arguments are properly set

### Debug Commands

```bash
# Check Azure login
az account show

# Check ACR access
az acr login --name novitaiwordmcp

# Check App Service status
az webapp show --name novitai-word-mcp-backend-dev --resource-group novitai-word-mcp-rg --query "{State:state, AvailabilityState:availabilityState}"
```

## Security Notes

- **Never commit secrets to the repository**
- **Use different API keys for dev and prod if possible**
- **Regularly rotate service principal credentials**
- **Monitor secret usage in GitHub Actions logs**
