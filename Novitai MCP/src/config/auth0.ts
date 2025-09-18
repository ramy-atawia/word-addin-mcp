// Get Auth0 configuration from window globals
const config = {
  auth0: {
    domain: (window as any).AUTH0_DOMAIN || 'dev-bktskx5kbc655wcl.us.auth0.com',
    clientId: (window as any).AUTH0_CLIENT_ID || 'INws849yDXaC6MZVXnLhMJi6CZC4nx6U',
    audience: (window as any).AUTH0_AUDIENCE || 'INws849yDXaC6MZVXnLhMJi6CZC4nx6U'
  },
  frontend: {
    baseUrl: (window as any).FRONTEND_URL || 'https://localhost:3000'
  }
};

export const auth0Config = {
  domain: config.auth0.domain,
  clientId: config.auth0.clientId,
  redirectUri: `${config.frontend.baseUrl}/auth-callback.html`,
  scope: "openid profile email",
  audience: config.auth0.audience,
  cacheLocation: "memory" as const,
  useRefreshTokens: true,
};

export interface Auth0Config {
  domain: string;
  clientId: string;
  redirectUri: string;
  scope: string;
  audience: string;
  cacheLocation: "memory" | "localstorage";
  useRefreshTokens: boolean;
}
