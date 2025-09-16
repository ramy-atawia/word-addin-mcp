"""
Auth0 JWT Middleware for FastAPI
Implements "secure by default" approach - protects all endpoints except excluded paths
"""

import logging
import time
from typing import List, Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
import requests
from jwt import PyJWKClient
from jwt.exceptions import PyJWTError, ExpiredSignatureError, InvalidTokenError

logger = logging.getLogger(__name__)


class Auth0JWTMiddleware(BaseHTTPMiddleware):
    """
    Auth0 JWT Middleware that validates tokens for all requests except excluded paths.
    Implements "secure by default" approach.
    """
    
    def __init__(self, app, domain: str, audience: str, excluded_paths: List[str] = None, fallback_mode: bool = True):
        super().__init__(app)
        self.domain = domain.rstrip('/')  # Remove trailing slash if present
        self.audience = audience
        self.excluded_paths = excluded_paths or []
        self.jwks_url = f"https://{self.domain}/.well-known/jwks.json"
        self.issuer = f"https://{self.domain}/"
        self.fallback_mode = fallback_mode
        self.jwks_client = None
        
        # Normalize excluded paths - this is CRITICAL for proper matching
        self.excluded_paths = [self._normalize_path(path) for path in self.excluded_paths]
        
        # Initialize JWKS client
        try:
            self.jwks_client = PyJWKClient(self.jwks_url)  # Removed unsupported parameters
            logger.info(f"Auth0 JWT Middleware initialized for domain: {self.domain}")
            logger.info(f"JWKS URL: {self.jwks_url}")
            logger.info(f"Excluded paths (normalized): {self.excluded_paths}")
            logger.info(f"Fallback mode: {self.fallback_mode}")
        except Exception as e:
            if self.fallback_mode:
                logger.warning(f"JWKS client failed, using fallback mode: {e}")
                self.jwks_client = None
            else:
                logger.error(f"Failed to initialize JWKS client: {e}")
                raise
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path for consistent matching."""
        if not path:
            return "/"
        
        # Remove trailing slash unless it's the root path
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")
        
        # Ensure path starts with /
        if not path.startswith("/"):
            path = "/" + path
        
        return path
    
    def is_excluded_path(self, path: str) -> bool:
        """Check if the request path should be excluded from authentication."""
        normalized_path = self._normalize_path(path)
        
        logger.debug(f"Auth0 Middleware: Checking path exclusion")
        logger.debug(f"Auth0 Middleware: Original path: '{path}'")
        logger.debug(f"Auth0 Middleware: Normalized path: '{normalized_path}'")
        logger.debug(f"Auth0 Middleware: Excluded paths: {self.excluded_paths}")
        
        # Check exact matches first
        for excluded_path in self.excluded_paths:
            logger.debug(f"Auth0 Middleware: Comparing '{normalized_path}' with '{excluded_path}'")

            if excluded_path.endswith('*'):
                # Wildcard matching
                prefix = excluded_path[:-1]  # Remove the *
                if normalized_path.startswith(prefix):
                    logger.debug(f"Auth0 Middleware: MATCHED wildcard pattern '{excluded_path}'")
                    return True

            # Special-case root: only exact match for '/'
            if excluded_path == '/':
                if normalized_path == '/':
                    logger.debug("Auth0 Middleware: MATCHED root '/' exact path")
                    return True
                # do not treat '/' as a prefix for other paths
                continue

            if normalized_path == excluded_path:
                # Exact match
                logger.debug(f"Auth0 Middleware: MATCHED exact path '{excluded_path}'")
                return True

            # Subdirectory match (only for non-root excluded paths)
            if normalized_path.startswith(excluded_path + '/'):
                logger.debug(f"Auth0 Middleware: MATCHED subdirectory pattern '{excluded_path}'")
                return True
        
        logger.debug(f"Auth0 Middleware: Path '{normalized_path}' is NOT excluded - authentication required")
        return False
    
    def extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from Authorization header."""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
        
        # Check for Bearer token format
        if not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header[7:].strip()  # Remove "Bearer " prefix and trim
        return token if token else None
    
    async def validate_token_fallback(self, token: str) -> Dict[str, Any]:
        """
        Fallback token validation using manual JWKS fetching.
        """
        try:
            # Try python-jose first
            try:
                from jose import jwt as jose_jwt
                
                # Get JWKS manually
                response = requests.get(self.jwks_url, timeout=10)
                response.raise_for_status()
                jwks = response.json()
                
                # Decode and validate the token using python-jose
                payload = jose_jwt.decode(
                    token,
                    jwks,
                    algorithms=['RS256'],
                    audience=self.audience,
                    issuer=self.issuer,
                    options={
                        "verify_signature": True,
                        "verify_exp": True,
                        "verify_aud": True,
                        "verify_iss": True
                    }
                )
                
                logger.debug("Token validated successfully using jose fallback")
                return self._extract_user_info(payload)
                
            except ImportError:
                logger.warning("python-jose not available for fallback validation")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Token validation service unavailable"
                )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Fallback token validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    def _extract_user_info(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user information from JWT payload."""
        return {
            "sub": payload.get("sub"),  # User ID
            "email": payload.get("email"),
            "name": payload.get("name"),
            "nickname": payload.get("nickname"),
            "picture": payload.get("picture"),
            "aud": payload.get("aud"),
            "iss": payload.get("iss"),
            "exp": payload.get("exp"),
            "iat": payload.get("iat"),
            "scope": payload.get("scope", "").split(" ") if payload.get("scope") else [],
            # Include any custom claims
            **{k: v for k, v in payload.items() 
               if k not in ["sub", "email", "name", "nickname", "picture", 
                           "aud", "iss", "exp", "iat", "scope"]}
        }
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token using Auth0 JWKS.
        Returns user information from the token.
        """
        # Input validation
        if not token or not isinstance(token, str):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Use fallback if JWKS client is not available
        if not self.jwks_client:
            logger.debug("Using fallback token validation (no JWKS client)")
            return await self.validate_token_fallback(token)
        
        try:
            # Get the signing key from JWKS
            logger.debug(f"Getting signing key for token: {token[:20]}...")
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            
            if not signing_key or not hasattr(signing_key, 'key') or not signing_key.key:
                logger.error("Failed to get signing key from JWKS")
                if self.fallback_mode:
                    logger.info("Trying fallback validation due to signing key issue")
                    return await self.validate_token_fallback(token)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token validation failed - unable to get signing key",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            logger.debug(f"Signing key retrieved successfully: {type(signing_key.key)}")
            
            # Decode and validate the token
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True
                }
            )
            
            # Extract user information
            user_info = self._extract_user_info(payload)
            
            logger.debug(f"Token validated for user: {user_info.get('email', user_info.get('sub'))}")
            return user_info
            
        except ExpiredSignatureError:
            logger.warning("Token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except PyJWTError as e:
            logger.warning(f"JWT error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except Exception as e:
            logger.error(f"Unexpected error validating token: {str(e)}")
            if self.fallback_mode:
                logger.warning(f"Primary validation failed, trying fallback: {str(e)}")
                try:
                    return await self.validate_token_fallback(token)
                except Exception as fallback_error:
                    logger.error(f"Fallback validation also failed: {str(fallback_error)}")
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    async def dispatch(self, request: Request, call_next):
        """Main middleware logic - validates tokens for all non-excluded paths."""
        start_time = time.time()
        
        try:
            logger.debug(f"Auth0 Middleware: Processing request: {request.method} {request.url.path}")

            # Allow CORS preflight requests to pass through without authentication
            if request.method == "OPTIONS":
                logger.debug("Auth0 Middleware: OPTIONS preflight request - bypassing authentication")
                return await call_next(request)
            
            # Check if path should be excluded from authentication
            if self.is_excluded_path(request.url.path):
                logger.info(f"Auth0 Middleware: Excluded path accessed: {request.url.path}")
                response = await call_next(request)
                return response
            
            # Extract token from request
            logger.debug(f"Auth0 Middleware: Extracting token from request headers")
            token = self.extract_token(request)
            if not token:
                logger.warning(f"Auth0 Middleware: Missing token for protected path: {request.url.path}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "Authentication required",
                        "message": "Authorization header with Bearer token is required",
                        "path": request.url.path,
                        "timestamp": time.time()
                    },
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            logger.debug(f"Auth0 Middleware: Token extracted: {token[:20]}...")
            
            # Validate token
            logger.debug(f"Auth0 Middleware: Starting token validation")
            user_info = await self.validate_token(token)
            
            # Add user information to request state for use in endpoints
            request.state.user = user_info
            request.state.user_id = user_info.get("sub")
            request.state.user_email = user_info.get("email")
            
            logger.info(f"Auth0 Middleware: Authentication successful for user: {user_info.get('sub')}")
            
            # Process the request
            response = await call_next(request)
            
            # Add authentication info to response headers
            user_identifier = user_info.get("sub", "unknown")
            response.headers["X-Authenticated-User-ID"] = user_identifier
            
            # Log successful authentication
            process_time = time.time() - start_time
            logger.info(
                f"Auth0 Middleware: Authenticated request completed - User ID: {user_identifier}, "
                f"Path: {request.url.path}, Method: {request.method}, "
                f"Process time: {process_time:.3f}s"
            )
            
            return response
            
        except HTTPException as e:
            # Log and return HTTP exceptions (like 401, 403)
            logger.warning(f"Auth0 Middleware: Authentication failed for {request.url.path}: {e.detail}")
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": "Authentication failed",
                    "message": e.detail,
                    "path": request.url.path,
                    "timestamp": time.time()
                },
                headers=e.headers or {}
            )
        except Exception as e:
            logger.error(f"Auth0 Middleware: Unexpected error: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "message": "Authentication service error",
                    "timestamp": time.time()
                }
            )


def create_auth0_middleware(domain: str, audience: str, excluded_paths: List[str] = None, 
                          fallback_mode: bool = True):
    """
    Factory function to create Auth0 JWT middleware with configuration.
    
    Args:
        domain: Auth0 domain (e.g., 'your-tenant.auth0.com')
        audience: API identifier from Auth0 dashboard
        excluded_paths: List of paths to exclude from authentication
        fallback_mode: Enable fallback validation methods (recommended: True)
    """
    def middleware_factory(app):
        return Auth0JWTMiddleware(
            app=app, 
            domain=domain, 
            audience=audience, 
            excluded_paths=excluded_paths,
            fallback_mode=fallback_mode
        )
    
    return middleware_factory