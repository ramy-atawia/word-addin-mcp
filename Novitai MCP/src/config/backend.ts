// Backend configuration and utilities
export interface BackendConfig {
  baseUrl: string;
  apiVersion: string;
  timeout: number;
  retryAttempts: number;
}

// Default backend configuration
export const defaultBackendConfig: BackendConfig = {
  baseUrl: 'https://localhost:9000',
  apiVersion: 'v1',
  timeout: 30000, // 30 seconds
  retryAttempts: 3,
};

// Environment-based configuration
const getBackendConfig = (): BackendConfig => {
  // Use default configuration for now - environment variables will be handled by webpack
  return {
    ...defaultBackendConfig,
    baseUrl: defaultBackendConfig.baseUrl,
    timeout: defaultBackendConfig.timeout,
    retryAttempts: defaultBackendConfig.retryAttempts,
  };
};

// Get the current backend configuration
export const backendConfig = getBackendConfig();

// Get the API base URL
export const getApiBaseUrl = (): string => {
  return `${backendConfig.baseUrl}/api/${backendConfig.apiVersion}`;
};

// Get the full URL for a specific endpoint
export const getEndpointUrl = (endpoint: string): string => {
  const baseUrl = getApiBaseUrl();
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  return `${baseUrl}/${cleanEndpoint}`;
};

// Health check endpoint
export const getHealthCheckUrl = (): string => {
  return `${backendConfig.baseUrl}/health`;
};

// Unified endpoint support - consolidates all endpoint functions
export const getApiUrl = (endpoint: string): string => {
  const endpoints: { [key: string]: string } = {
    // MCP endpoints
    'MCP_TOOLS': getEndpointUrl('mcp/tools'),
    'MCP_EXECUTE': getEndpointUrl('mcp/execute'),
    'MCP_SERVERS': getEndpointUrl('mcp/servers'),
    
    // External server endpoints
    'EXTERNAL_SERVERS': getEndpointUrl('external/servers'),
    'TEST_CONNECTION': getEndpointUrl('external/servers/test-connection'),
    'ADD_SERVER': getEndpointUrl('external/servers'),
    'UPDATE_SERVER': getEndpointUrl('external/servers/{id}'),
    'REMOVE_SERVER': getEndpointUrl('external/servers/{id}'),
  };
  
  return endpoints[endpoint] || getEndpointUrl(endpoint);
};

// Helper functions for dynamic endpoints
export const getMCPSchemaUrl = (toolName: string): string => {
  return getEndpointUrl(`mcp/schema/${toolName}`);
};

export const getMCPServerToolsUrl = (serverName: string): string => {
  return getEndpointUrl(`mcp/servers/${serverName}/tools`);
};

// Utility function to check if backend is available
export const isBackendAvailable = async (): Promise<boolean> => {
  try {
    const response = await fetch(getHealthCheckUrl(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: AbortSignal.timeout(backendConfig.timeout),
    });
    return response.ok;
  } catch (error) {
    console.error('Backend health check failed:', error);
    return false;
  }
};

// Utility function to get backend status
export const getBackendStatus = async (): Promise<{
  available: boolean;
  responseTime?: number;
  error?: string;
}> => {
  const startTime = Date.now();
  
  try {
    const response = await fetch(getHealthCheckUrl(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: AbortSignal.timeout(backendConfig.timeout),
    });
    
    const responseTime = Date.now() - startTime;
    
    if (response.ok) {
      return {
        available: true,
        responseTime,
      };
    } else {
      return {
        available: false,
        responseTime,
        error: `HTTP ${response.status}: ${response.statusText}`,
      };
    }
  } catch (error) {
    const responseTime = Date.now() - startTime;
    return {
      available: false,
      responseTime,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
};
