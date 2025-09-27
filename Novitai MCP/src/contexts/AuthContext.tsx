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
  isAuth0Initialized: boolean;
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
  const [isAuth0Initialized, setIsAuth0Initialized] = useState<boolean>(false);

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
          // Check mounted status before any state updates
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

        // Check mounted status before proceeding with Auth0 initialization
        if (!mounted) return;

        // FIX: Actually initialize Auth0 client instead of setting to null
        try {
          const { createAuth0Client } = await import('@auth0/auth0-spa-js');
          const auth0Client = await createAuth0Client({
            domain,
            clientId,
            authorizationParams: {
              redirect_uri: redirectUri,
              scope
            }
          });
          
          // Check mounted status again after async Auth0 initialization
          if (!mounted) return;
          
          setAuth0Client(auth0Client);
          setIsAuth0Initialized(true);
          setIsAuthenticated(false);
        } catch (auth0Error) {
          console.error('Auth0 client initialization failed:', auth0Error);
          // Check mounted status before setting error state
          if (!mounted) return;
          setAuth0Client(null);
          setIsAuth0Initialized(false);
          setIsAuthenticated(false);
        }
      } catch (e) {
        console.error('Auth initialization failed', e);
        // Check mounted status before setting error state
        if (!mounted) return;
        setAuth0Client(null);
        setIsAuth0Initialized(false);
        setIsAuthenticated(false);
      } finally {
        // Check mounted status before final state update
        if (mounted) {
          setLoading(false);
        }
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
    if (!auth0Client || !isAuth0Initialized) {
      console.error('Auth0 client not initialized. Please wait for initialization to complete.');
      throw new Error('Auth0 client not initialized. Please wait for initialization to complete.');
    }
    try {
      await auth0Client.loginWithRedirect();
    } catch (error) {
      console.error('Login redirect failed:', error);
      throw error;
    }
  };

  const handleRedirectCallback = async (): Promise<void> => {
    if (!auth0Client || !isAuth0Initialized) {
      console.error('Auth0 client not initialized. Please wait for initialization to complete.');
      throw new Error('Auth0 client not initialized. Please wait for initialization to complete.');
    }
    setLoading(true);
    try {
      await auth0Client.handleRedirectCallback();
      const silentToken = await auth0Client.getTokenSilently();
      setToken(silentToken);
      const profile = await auth0Client.getUser();
      setUser(profile || null);
      setIsAuthenticated(true);
    } catch (error) {
      console.error('Redirect callback handling failed:', error);
      throw error;
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
    isAuth0Initialized,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
