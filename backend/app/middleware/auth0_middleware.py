"""
Auth0 Bearer Token Validation Middleware
Validates JWT tokens from Auth0 for API access
"""

import jwt
import requests
import logging
from typing import Optional
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Request, Response

logger = logging.getLogger(__name__)

class Auth0Middleware:
    """Middleware for Auth0 JWT token validation"""
    
    def __init__(self, domain: str, audience: str):
        self.domain = domain
        self.audience = audience
        self.jwks_url = f"https://{domain}/.well-known/jwks.json"
        self.issuer = f"https://{domain}/"
        self._jwks_cache = None
        self._jwks_cache_time = None
    
    def get_jwks(self) -> dict:
        """Get JWKS (JSON Web Key Set) from Auth0"""
        import time
        
        # Cache JWKS for 1 hour
        if (self._jwks_cache is None or 
            self._jwks_cache_time is None or 
            time.time() - self._jwks_cache_time > 3600):
            
            try:
                response = requests.get(self.jwks_url, timeout=10)
                response.raise_for_status()
                self._jwks_cache = response.json()
                self._jwks_cache_time = time.time()
                logger.info("JWKS cache updated")
            except Exception as e:
                logger.error(f"Failed to fetch JWKS: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Unable to verify token"
                )
        
        return self._jwks_cache
    
    def get_signing_key(self, token: str) -> str:
        """Get the signing key for the token"""
        try:
            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')
            
            if not kid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token missing key ID"
                )
            
            # Get JWKS
            jwks = self.get_jwks()
            
            # Find the key
            for key in jwks.get('keys', []):
                if key.get('kid') == kid:
                    # Convert JWK to PEM format
                    from cryptography.hazmat.primitives import serialization
                    from cryptography.hazmat.primitives.asymmetric import rsa
                    import base64
                    
                    # Extract RSA components
                    n = base64.urlsafe_b64decode(key['n'] + '==')
                    e = base64.urlsafe_b64decode(key['e'] + '==')
                    
                    # Convert to integers
                    n_int = int.from_bytes(n, 'big')
                    e_int = int.from_bytes(e, 'big')
                    
                    # Create RSA public key
                    public_key = rsa.RSAPublicNumbers(e_int, n_int).public_key()
                    
                    # Serialize to PEM
                    pem_key = public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                    )
                    
                    return pem_key.decode('utf-8')
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate key"
            )
            
        except Exception as e:
            logger.error(f"Error getting signing key: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def validate_token(self, token: str) -> dict:
        """Validate the JWT token and return payload"""
        try:
            # Get signing key
            signing_key = self.get_signing_key(token)
            
            # Decode and validate token
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=['RS256'],
                audience=self.audience,
                issuer=self.issuer,
                options={"verify_exp": True}
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed"
            )

# Global Auth0 middleware instance
auth0_middleware = None

def init_auth0_middleware(domain: str, audience: str):
    """Initialize the Auth0 middleware"""
    global auth0_middleware
    auth0_middleware = Auth0Middleware(domain, audience)

def get_auth0_middleware() -> Auth0Middleware:
    """Get the Auth0 middleware instance"""
    if auth0_middleware is None:
        raise RuntimeError("Auth0 middleware not initialized")
    return auth0_middleware

# FastAPI dependency for token validation
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = security) -> dict:
    """FastAPI dependency to verify Auth0 token"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    token = credentials.credentials
    middleware = get_auth0_middleware()
    return middleware.validate_token(token)

# Optional token validation (for endpoints that can work with or without auth)
async def verify_token_optional(credentials: Optional[HTTPAuthorizationCredentials] = security) -> Optional[dict]:
    """FastAPI dependency for optional token verification"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        middleware = get_auth0_middleware()
        return middleware.validate_token(token)
    except HTTPException:
        return None
