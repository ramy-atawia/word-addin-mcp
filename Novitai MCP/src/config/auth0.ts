import { getEnvironmentConfig } from './environment';

const config = getEnvironmentConfig();

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
