// Simple in-memory auth token store to avoid using browser storage in artifact environments
let accessToken: string | null = null;
let idToken: string | null = null;
let userProfile: any = null;

export interface AuthTokens {
  accessToken?: string | null;
  idToken?: string | null;
  userProfile?: any | null;
}

export function setAuthTokens(tokens: AuthTokens): void {
  accessToken = tokens.accessToken || null;
  idToken = tokens.idToken || null;
  userProfile = tokens.userProfile || null;
}

export function getAccessToken(): string | null {
  return accessToken;
}

export function getIdToken(): string | null {
  return idToken;
}

export function getUserProfile(): any | null {
  return userProfile;
}

export function clearAuthTokens(): void {
  accessToken = null;
  idToken = null;
  userProfile = null;
}

export function hasValidToken(): boolean {
  return accessToken !== null && accessToken.length > 0;
}
