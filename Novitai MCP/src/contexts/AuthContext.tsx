import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Auth0Client, User } from '@auth0/auth0-spa-js';
import { setAuthTokens, getAccessToken, getUserProfile, clearAuthTokens } from '../services/authTokenStore';
import { auth0Config } from '../config/auth0';

interface AuthContextType {
  isAuthenticated: boolean;
  token: string | null;
  user: User | null;
  loginWithRedirect: () => Promise<void>;
  handleRedirectCallback: () => Promise<void>;
  logout: () => void;
  loading: boolean;
  refreshFromStorage: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [auth0Client, setAuth0Client] = useState<Auth0Client | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    // Listen to global auth-tokens event dispatched by dialog/popup
    const onAuthTokens = (e: Event): void => {
      try {
        const detail = (e as CustomEvent).detail || {};
        setAuthTokens({ 
          accessToken: detail.accessToken || null, 
          idToken: detail.idToken || null, 
          userProfile: detail.userProfile || null 
        });
        refreshFromStorage();
      } catch (err) {
        console.warn('Failed to process auth-tokens event', err);
      }
    };
    
    window.addEventListener('auth-tokens', onAuthTokens as EventListener);
    
    let mounted = true;
    const initAuth = async (): Promise<void> => {
      try {
        const config = (window as any).__AUTH0_CONFIG__ || auth0Config;

        // Use in-memory token store instead of sessionStorage
        const storedAccess = getAccessToken();
        const storedProfile = getUserProfile();
        if (storedAccess) {
          if (!mounted) return;
          setToken(storedAccess);
          try { 
            setUser(storedProfile || null); 
          } catch (e) { 
            setUser(null); 
          }
          setIsAuthenticated(true);
          setLoading(false);
          return;
        }

        // No stored tokens: initialize Auth0 SPA client
        const domain = config.domain || auth0Config.domain;
        const clientId = config.clientId || auth0Config.clientId;
        const redirectUri = config.redirectUri || auth0Config.redirectUri;
        const scope = config.scope || auth0Config.scope;

        if (!mounted) return;
        setAuth0Client(null);
        setIsAuthenticated(false);
      } catch (e) {
        console.error('Auth initialization failed', e);
      } finally {
        setLoading(false);
      }
    };
    
    initAuth();
    
    return () => {
      mounted = false;
      try { 
        window.removeEventListener('auth-tokens', onAuthTokens as EventListener); 
      } catch (e) {}
    };
  }, []);

  const loginWithRedirect = async (): Promise<void> => {
    if (!auth0Client) throw new Error('Auth0 client not initialized');
    await auth0Client.loginWithRedirect();
  };

  const handleRedirectCallback = async (): Promise<void> => {
    if (!auth0Client) throw new Error('Auth0 client not initialized');
    setLoading(true);
    try {
      await auth0Client.handleRedirectCallback();
      const silentToken = await auth0Client.getTokenSilently();
      setToken(silentToken);
      const profile = await auth0Client.getUser();
      setUser(profile || null);
      setIsAuthenticated(true);
    } finally {
      setLoading(false);
    }
  };

  const logout = (): void => {
    if (auth0Client) {
      auth0Client.logout({ logoutParams: { returnTo: window.location.origin } });
    }
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
  };

  const refreshFromStorage = (): void => {
    const storedAccess = getAccessToken();
    const storedProfile = getUserProfile();
    if (storedAccess) {
      setToken(storedAccess);
      try { 
        setUser(storedProfile || null); 
      } catch (e) { 
        setUser(null); 
      }
      setIsAuthenticated(true);
    }
  };

  const value: AuthContextType = {
    isAuthenticated,
    token,
    user,
    loginWithRedirect,
    handleRedirectCallback,
    logout,
    loading,
    refreshFromStorage,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
