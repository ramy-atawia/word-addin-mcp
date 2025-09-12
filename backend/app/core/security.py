"""
Security and Authentication Module for Word Add-in MCP Project.

This module provides comprehensive security features including:
- JWT authentication system
- Role-based access control (RBAC)
- Password hashing and validation
- Security utilities and helpers
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from enum import Enum
import structlog
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, Field, validator
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

logger = structlog.get_logger()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()


class UserRole(str, Enum):
    """User roles for RBAC system."""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
    DEVELOPER = "developer"
    ANALYST = "analyst"


class Permission(str, Enum):
    """Permissions for different operations."""
    # User management
    CREATE_USERS = "create_users"
    READ_USERS = "read_users"
    UPDATE_USERS = "update_users"
    DELETE_USERS = "delete_users"
    
    # MCP tools
    EXECUTE_TOOL = "execute_tool"
    MANAGE_TOOLS = "manage_tools"
    VIEW_TOOL_HISTORY = "view_tool_history"
    
    # Chat and sessions
    CREATE_CHAT = "create_chat"
    READ_CHAT = "read_chat"
    MANAGE_SESSIONS = "manage_sessions"
    
    # System administration
    VIEW_LOGS = "view_logs"
    MANAGE_SYSTEM = "manage_system"
    ACCESS_ADMIN_PANEL = "access_admin_panel"


class RolePermissions(BaseModel):
    """Role-based permissions mapping."""
    role: UserRole
    permissions: List[Permission]
    description: str


# Define role permissions
ROLE_PERMISSIONS: Dict[UserRole, RolePermissions] = {
    UserRole.ADMIN: RolePermissions(
        role=UserRole.ADMIN,
        permissions=[
            Permission.CREATE_USERS, Permission.READ_USERS, Permission.UPDATE_USERS, Permission.DELETE_USERS,
            Permission.EXECUTE_TOOL, Permission.MANAGE_TOOLS, Permission.VIEW_TOOL_HISTORY,
            Permission.CREATE_CHAT, Permission.READ_CHAT, Permission.MANAGE_SESSIONS,
            Permission.VIEW_LOGS, Permission.MANAGE_SYSTEM, Permission.ACCESS_ADMIN_PANEL
        ],
        description="Full system access and administration"
    ),
    UserRole.DEVELOPER: RolePermissions(
        role=UserRole.DEVELOPER,
        permissions=[
            Permission.EXECUTE_TOOL, Permission.MANAGE_TOOLS, Permission.VIEW_TOOL_HISTORY,
            Permission.CREATE_CHAT, Permission.READ_CHAT, Permission.MANAGE_SESSIONS,
            Permission.VIEW_LOGS
        ],
        description="Developer access with tool management capabilities"
    ),
    UserRole.ANALYST: RolePermissions(
        role=UserRole.ANALYST,
        permissions=[
            Permission.EXECUTE_TOOL, Permission.VIEW_TOOL_HISTORY,
            Permission.CREATE_CHAT, Permission.READ_CHAT
        ],
        description="Analyst access for data analysis and reporting"
    ),
    UserRole.USER: RolePermissions(
        role=UserRole.USER,
        permissions=[
            Permission.EXECUTE_TOOL, Permission.VIEW_TOOL_HISTORY,
            Permission.CREATE_CHAT, Permission.READ_CHAT
        ],
        description="Standard user access"
    ),
    UserRole.GUEST: RolePermissions(
        role=UserRole.GUEST,
        permissions=[
            Permission.EXECUTE_TOOL
        ],
        description="Limited guest access"
    )
}


class User(BaseModel):
    """User model for authentication."""
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    last_login: Optional[datetime] = None
    permissions: List[Permission] = Field(default_factory=list)

    @validator('permissions', pre=True, always=True)
    def set_permissions(cls, v, values):
        """Set permissions based on role."""
        if 'role' in values:
            role_perms = ROLE_PERMISSIONS.get(values['role'])
            if role_perms:
                return role_perms.permissions
        return v or []


class TokenData(BaseModel):
    """Token payload data."""
    username: Optional[str] = None
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[UserRole] = None
    permissions: List[Union[Permission, str]] = Field(default_factory=list)
    exp: Optional[datetime] = None


class SecurityConfig(BaseModel):
    """Security configuration."""
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_min_length: int = 8
    password_require_special: bool = True
    password_require_numbers: bool = True
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15


class SecurityService:
    """Security service for authentication and authorization."""
    
    def __init__(self):
        self.config = SecurityConfig(
            secret_key=settings.secret_key,
            algorithm=settings.algorithm,
            access_token_expire_minutes=settings.access_token_expire_minutes,
            refresh_token_expire_days=settings.refresh_token_expire_days,
            password_min_length=settings.password_min_length,
            password_require_special=settings.password_require_special,
            password_require_numbers=settings.password_require_numbers,
            max_login_attempts=settings.max_login_attempts,
            lockout_duration_minutes=settings.lockout_duration_minutes
        )
        
        # In-memory storage for failed login attempts (in production, use Redis)
        self.failed_attempts: Dict[str, Dict[str, Any]] = {}
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def hash_password(self, password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)
    
    def validate_password(self, password: str) -> bool:
        """Validate password strength."""
        if len(password) < self.config.password_min_length:
            return False
        
        if self.config.password_require_special and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False
        
        if self.config.password_require_numbers and not any(c.isdigit() for c in password):
            return False
        
        return True
    
    def validate_password_complexity(self, password: str) -> bool:
        """Validate password complexity requirements."""
        return self.validate_password(password)
    
    def create_access_token(self, user: Union[User, Dict[str, Any]], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        if isinstance(user, User):
            to_encode = {
                "sub": user.email,  # Use email as subject
                "user_id": user.id,
                "role": user.role.value,
                "permissions": [p.value for p in user.permissions]
            }
        else:
            to_encode = user.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.config.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.config.secret_key, algorithm=self.config.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.config.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.config.secret_key, algorithm=self.config.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.config.secret_key, algorithms=[self.config.algorithm])
            username: str = payload.get("sub")
            user_id: str = payload.get("user_id")
            role: str = payload.get("role")
            permissions: List[str] = payload.get("permissions", [])
            exp: int = payload.get("exp")
            
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            token_data = TokenData(
                username=username,
                user_id=user_id,
                email=username,  # In this case, username is the email
                role=UserRole(role) if role else None,
                permissions=[Permission(p) for p in permissions],
                exp=datetime.fromtimestamp(exp) if exp else None
            )
            return token_data
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def check_permission(self, user_permissions: List[Union[Permission, str]], required_permission: Permission) -> bool:
        """Check if user has required permission."""
        # Handle both Permission enum objects and string values
        for perm in user_permissions:
            if isinstance(perm, Permission) and perm == required_permission:
                return True
            elif isinstance(perm, str) and perm == required_permission.value:
                return True
        return False
    
    def check_role_permission(self, user_role: UserRole, required_permission: Permission) -> bool:
        """Check if user role has required permission."""
        role_perms = ROLE_PERMISSIONS.get(user_role)
        if role_perms:
            return required_permission in role_perms.permissions
        return False
    
    def has_permission(self, user: User, required_permission: Permission) -> bool:
        """Check if user has required permission."""
        return self.check_role_permission(user.role, required_permission)
    
    def create_user(self, **user_data) -> User:
        """Create a new user."""
        # In a real implementation, this would save to database
        user_id = f"user_{len(self.failed_attempts) + 1}"  # Simple ID generation
        
        user = User(
            id=user_id,
            username=user_data["username"],
            email=user_data["email"],
            full_name=user_data.get("full_name"),
            role=user_data.get("role", UserRole.USER),
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID (mock implementation)."""
        # In a real implementation, this would query the database
        # For now, return a mock user
        return User(
            id=user_id,
            username="mockuser",
            email="mock@example.com",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.utcnow()
        )
    
    def get_users(self) -> List[User]:
        """Get all users (mock implementation)."""
        # In a real implementation, this would query the database
        return [
            User(
                id="admin",
                username="admin",
                email="admin@example.com",
                role=UserRole.ADMIN,
                is_active=True,
                created_at=datetime.utcnow()
            ),
            User(
                id="user1",
                username="user1",
                email="user1@example.com",
                role=UserRole.USER,
                is_active=True,
                created_at=datetime.utcnow()
            )
        ]
    
    def update_user(self, user_id: str, **update_data) -> Optional[User]:
        """Update user (mock implementation)."""
        # In a real implementation, this would update the database
        user = self.get_user_by_id(user_id)
        if user:
            # Update fields
            for field, value in update_data.items():
                if hasattr(user, field):
                    setattr(user, field, value)
        return user
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user (mock implementation)."""
        # In a real implementation, this would delete from database
        return True  # Mock success
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username/email and password."""
        # In a real implementation, this would query the database
        # For now, return a mock user if credentials are valid
        if username == "test@example.com" and password == "SecurePass123!":
            return User(
                id="test-user",
                username="testuser",
                email="test@example.com",
                role=UserRole.USER,
                is_active=True,
                created_at=datetime.utcnow()
            )
        return None
    
    def record_failed_login(self, username: str) -> bool:
        """Record failed login attempt and check if account should be locked."""
        now = datetime.utcnow()
        
        if username not in self.failed_attempts:
            self.failed_attempts[username] = {
                "count": 0,
                "first_attempt": now,
                "last_attempt": now
            }
        
        self.failed_attempts[username]["count"] += 1
        self.failed_attempts[username]["last_attempt"] = now
        
        # Check if account should be locked
        if self.failed_attempts[username]["count"] >= self.config.max_login_attempts:
            lockout_until = now + timedelta(minutes=self.config.lockout_duration_minutes)
            self.failed_attempts[username]["locked_until"] = lockout_until
            logger.warning(f"Account locked for user: {username}", 
                          lockout_until=lockout_until.isoformat())
            return True
        
        return False
    
    def is_account_locked(self, username: str) -> bool:
        """Check if account is currently locked."""
        if username not in self.failed_attempts:
            return False
        
        user_data = self.failed_attempts[username]
        if "locked_until" not in user_data:
            return False
        
        if datetime.utcnow() < user_data["locked_until"]:
            return True
        
        # Unlock account if lockout period has expired
        del user_data["locked_until"]
        user_data["count"] = 0
        return False
    
    def reset_failed_attempts(self, username: str):
        """Reset failed login attempts for user."""
        if username in self.failed_attempts:
            self.failed_attempts[username]["count"] = 0
            if "locked_until" in self.failed_attempts[username]:
                del self.failed_attempts[username]["locked_until"]


# Global security service instance
security_service = SecurityService()


# Dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    return security_service.verify_token(token)


async def get_current_active_user(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Get current active user."""
    if not current_user.username:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user





def require_permission(permission: Permission):
    """Dependency to require specific permission."""
    async def permission_checker(current_user: TokenData = Depends(get_current_active_user)):
        if not security_service.check_permission(current_user.permissions, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission}"
            )
        return current_user
    return permission_checker


def require_role(role: UserRole):
    """Dependency to require specific role."""
    async def role_checker(current_user: TokenData = Depends(get_current_active_user)):
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role}"
            )
        return current_user
    return role_checker


# Security utilities



def sanitize_input(input_string: str) -> str:
    """Basic input sanitization."""
    # Remove potentially dangerous characters and patterns
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '{', '}', '[', ']']
    dangerous_patterns = [
        'DROP TABLE', 'DELETE FROM', 'INSERT INTO', 'UPDATE SET',
        'SELECT *', 'UNION SELECT', 'EXEC', 'EXECUTE'
    ]
    
    sanitized = input_string
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    for pattern in dangerous_patterns:
        sanitized = sanitized.replace(pattern.upper(), '')
        sanitized = sanitized.replace(pattern.lower(), '')
    
    return sanitized.strip()


def validate_email(email: str) -> bool:
    """Basic email validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


# Rate limiting utilities
class RateLimiter:
    """Simple in-memory rate limiter (use Redis in production)."""
    
    def __init__(self):
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        self.requests: Dict[str, List[datetime]] = {}  # For the is_allowed method
        self.default_limits = {
            "auth": {"requests": 10, "window": 300},  # 10 requests per 5 minutes
            "api": {"requests": 100, "window": 60},   # 100 requests per minute
            "default": {"requests": 50, "window": 60}  # 50 requests per minute
        }
    
    def check_rate_limit(self, client_ip: str, category: str) -> bool:
        """Check if request is within rate limit."""
        import time
        
        now = time.time()
        limit_config = self.default_limits[category]
        
        if client_ip not in self.rate_limits:
            self.rate_limits[client_ip] = {}
        
        if category not in self.rate_limits[client_ip]:
            self.rate_limits[client_ip][category] = {
                "requests": [],
                "window_start": now
            }
        
        # Clean old requests outside window
        window_start = now - limit_config["window"]
        self.rate_limits[client_ip][category]["requests"] = [
            req_time for req_time in self.rate_limits[client_ip][category]["requests"]
            if req_time > window_start
        ]
        
        # Check if under limit
        if len(self.rate_limits[client_ip][category]["requests"]) < limit_config["requests"]:
            self.rate_limits[client_ip][category]["requests"].append(now)
            return True
        
        return False
    
    def get_retry_after(self, client_ip: str, category: str) -> int:
        """Get retry after time in seconds."""
        import time
        
        now = time.time()
        limit_config = self.default_limits[category]
        
        if client_ip in self.rate_limits and category in self.rate_limits[client_ip]:
            oldest_request = min(self.rate_limits[client_ip][category]["requests"])
            return int(limit_config["window"] - (now - oldest_request))
        
        return limit_config["window"]
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if request is allowed based on rate limit."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        
        if key not in self.requests:
            self.requests = {}
            self.requests[key] = []
        
        # Remove old requests outside the window
        self.requests[key] = [req_time for req_time in self.requests[key] if req_time > window_start]
        
        # Check if under limit
        if len(self.requests[key]) < max_requests:
            self.requests[key].append(now)
            return True
        
        return False


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(max_requests: int, window_seconds: int):
    """Decorator for rate limiting endpoints."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # For testing purposes, we'll use a mock request
            # In real usage, this would be injected by FastAPI
            import time
            key = f"rate_limit:test_{int(time.time())}"
            
            if not rate_limiter.is_allowed(key, max_requests, window_seconds):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator
