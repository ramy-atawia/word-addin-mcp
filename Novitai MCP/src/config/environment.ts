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
  const isDev = hostname.includes('dev');
  
  // Use window globals that are injected by webpack plugin, fallback to defaults
  const getEnvVar = (key: string, devDefault: string, prodDefault: string) => {
    if (typeof window !== 'undefined' && (window as any)[key]) {
      return (window as any)[key];
    }
    return isDev ? devDefault : prodDefault;
  };
  
  // Override with environment-specific URLs if we're in dev
  const getDevUrl = (baseUrl: string) => {
    // Only transform if the URL doesn't already contain '-dev'
    if (baseUrl.includes('-dev.azurewebsites.net')) {
      return baseUrl; // Already a dev URL, return as-is
    }
    return baseUrl.replace('.azurewebsites.net', '-dev.azurewebsites.net');
  };
  
  // Get base URLs from environment variables or defaults
  const baseBackendUrl = process.env.REACT_APP_API_BASE_URL || getEnvVar('BACKEND_URL', 'http://localhost:9000', 'https://novitai-word-mcp-backend.azurewebsites.net');
  const baseFrontendUrl = process.env.REACT_APP_FRONTEND_URL || getEnvVar('FRONTEND_URL', 'https://localhost:3000', 'https://novitai-word-mcp-frontend.azurewebsites.net');
  
  if (isDev) {
    return {
      auth0: {
        domain: getEnvVar('AUTH0_DOMAIN', 'dev-bktskx5kbc655wcl.us.auth0.com', 'dev-bktskx5kbc655wcl.us.auth0.com'),
        clientId: getEnvVar('AUTH0_CLIENT_ID', 'INws849yDXaC6MZVXnLhMJi6CZC4nx6U', 'INws849yDXaC6MZVXnLhMJi6CZC4nx6U'),
        audience: getEnvVar('AUTH0_AUDIENCE', 'INws849yDXaC6MZVXnLhMJi6CZC4nx6U', 'INws849yDXaC6MZVXnLhMJi6CZC4nx6U')
      },
      backend: {
        baseUrl: getDevUrl(baseBackendUrl)
      },
      frontend: {
        baseUrl: getDevUrl(baseFrontendUrl)
      }
    };
  } else {
    return {
      auth0: {
        domain: getEnvVar('AUTH0_DOMAIN', 'dev-bktskx5kbc655wcl.us.auth0.com', 'dev-bktskx5kbc655wcl.us.auth0.com'),
        clientId: getEnvVar('AUTH0_CLIENT_ID', 'INws849yDXaC6MZVXnLhMJi6CZC4nx6U', 'INws849yDXaC6MZVXnLhMJi6CZC4nx6U'),
        audience: getEnvVar('AUTH0_AUDIENCE', 'INws849yDXaC6MZVXnLhMJi6CZC4nx6U', 'INws849yDXaC6MZVXnLhMJi6CZC4nx6U')
      },
      backend: {
        baseUrl: baseBackendUrl
      },
      frontend: {
        baseUrl: baseFrontendUrl
      }
    };
  }
}
