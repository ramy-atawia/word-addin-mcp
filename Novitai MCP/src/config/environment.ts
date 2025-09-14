// Environment configuration
export interface EnvironmentConfig {
  auth0: {
    domain: string;
    clientId: string;
    audience: string;
  };
  backend: {
    baseUrl: string;
  };
  frontend: {
    baseUrl: string;
  };
}

// Get environment-specific configuration
export function getEnvironmentConfig(): EnvironmentConfig {
  const hostname = typeof window !== 'undefined' ? window.location.hostname : '';
  
  // Determine environment based on hostname
  const isLocal = hostname === 'localhost' || hostname === '127.0.0.1' || hostname.includes('localhost');
  const isDev = hostname.includes('dev') && !isLocal;
  const isProd = !isLocal && !isDev;
  
  // Use window globals that are injected by webpack plugin, fallback to defaults
  const getEnvVar = (key: string, localDefault: string, devDefault: string, prodDefault: string) => {
    if (typeof window !== 'undefined' && (window as any)[key]) {
      return (window as any)[key];
    }
    if (isLocal) return localDefault;
    if (isDev) return devDefault;
    return prodDefault;
  };
  
  // Environment-specific configurations
  if (isLocal) {
    return {
      auth0: {
        domain: getEnvVar('AUTH0_DOMAIN', 'dev-bktskx5kbc655wcl.us.auth0.com', '', ''),
        clientId: getEnvVar('AUTH0_CLIENT_ID', 'INws849yDXaC6MZVXnLhMJi6CZC4nx6U', '', ''),
        audience: getEnvVar('AUTH0_AUDIENCE', 'INws849yDXaC6MZVXnLhMJi6CZC4nx6U', '', '')
      },
      backend: {
        baseUrl: getEnvVar('BACKEND_URL', 'http://localhost:9000', '', '')
      },
      frontend: {
        baseUrl: getEnvVar('FRONTEND_URL', 'https://localhost:3000', '', '')
      }
    };
  } else if (isDev) {
    return {
      auth0: {
        domain: getEnvVar('AUTH0_DOMAIN', '', 'dev-bktskx5kbc655wcl.us.auth0.com', ''),
        clientId: getEnvVar('AUTH0_CLIENT_ID', '', 'INws849yDXaC6MZVXnLhMJi6CZC4nx6U', ''),
        audience: getEnvVar('AUTH0_AUDIENCE', '', 'INws849yDXaC6MZVXnLhMJi6CZC4nx6U', '')
      },
      backend: {
        baseUrl: getEnvVar('BACKEND_URL', '', 'https://novitai-word-mcp-apim-dev.azure-api.net/api', '')
      },
      frontend: {
        baseUrl: getEnvVar('FRONTEND_URL', '', 'https://novitai-word-mcp-frontend-dev.azurewebsites.net', '')
      }
    };
  } else {
    // Production - uses APIM for authentication
    return {
      auth0: {
        domain: getEnvVar('AUTH0_DOMAIN', '', '', 'dev-bktskx5kbc655wcl.us.auth0.com'),
        clientId: getEnvVar('AUTH0_CLIENT_ID', '', '', 'INws849yDXaC6MZVXnLhMJi6CZC4nx6U'),
        audience: getEnvVar('AUTH0_AUDIENCE', '', '', 'INws849yDXaC6MZVXnLhMJi6CZC4nx6U')
      },
      backend: {
        baseUrl: getEnvVar('BACKEND_URL', '', '', 'https://novitai-word-mcp-apim.azure-api.net/api')
      },
      frontend: {
        baseUrl: getEnvVar('FRONTEND_URL', '', '', 'https://novitai-word-mcp-frontend.azurewebsites.net')
      }
    };
  }
}
