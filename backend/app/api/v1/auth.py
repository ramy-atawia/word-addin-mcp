"""
Authentication API endpoints for Word Add-in MCP Project.

This module provides authentication endpoints including:
- User registration and login
- JWT token management
- Password reset functionality
- User profile management
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional
import structlog
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, validator

from app.core.security import (
    security_service, User, TokenData, UserRole, Permission,
    get_current_user, get_current_active_user, require_permission,
    require_role, rate_limit, sanitize_input, validate_email
)
from app.core.config import settings

logger = structlog.get_logger()

router = APIRouter()


# Request/Response Models
class UserCreate(BaseModel):
    """User registration request model."""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=255)
    role: UserRole = UserRole.USER

    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        if not v.isalnum():
            raise ValueError('Username must contain only alphanumeric characters')
        return sanitize_input(v)

    @validator('email')
    def validate_email(cls, v):
        """Validate email format."""
        if not validate_email(v):
            raise ValueError('Invalid email format')
        return v.lower()

    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if not security_service.validate_password(v):
            raise ValueError('Password does not meet security requirements')
        return v


class UserLogin(BaseModel):
    """User login request model."""
    username: str
    password: str


class UserUpdate(BaseModel):
    """User update request model."""
    full_name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

    @validator('email')
    def validate_email(cls, v):
        """Validate email format if provided."""
        if v is not None and not validate_email(v):
            raise ValueError('Invalid email format')
        return v.lower() if v else v


class PasswordChange(BaseModel):
    """Password change request model."""
    current_password: str
    new_password: str

    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if not security_service.validate_password(v):
            raise ValueError('Password does not meet security requirements')
        return v


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request model."""
    email: str

    @validator('email')
    def validate_email(cls, v):
        """Validate email format."""
        if not validate_email(v):
            raise ValueError('Invalid email format')
        return v.lower()


class PasswordReset(BaseModel):
    """Password reset model."""
    token: str
    new_password: str

    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if not security_service.validate_password(v):
            raise ValueError('Password does not meet security requirements')
        return v


# In-memory user storage (replace with database in production)
users_db: dict[str, User] = {}
refresh_tokens_db: dict[str, dict] = {}
password_reset_tokens_db: dict[str, dict] = {}


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
# @rate_limit(max_requests=5, window_seconds=300)  # 5 requests per 5 minutes - temporarily disabled
async def register_user(user_data: UserCreate):
    """Register a new user."""
    # Check if username already exists
    if any(user.username == user_data.username for user in users_db.values()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    if any(user.email == user_data.email for user in users_db.values()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = security_service.get_password_hash(user_data.password)
    
    user = User(
        id=user_id,
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role,
        created_at=datetime.utcnow(),
        permissions=[]  # Will be set by validator
    )
    
    users_db[user_id] = user
    
    logger.info(f"New user registered: {user.username}", user_id=user_id, role=user.role)
    
    return user


@router.post("/login", response_model=TokenResponse)
# @rate_limit(max_requests=10, window_seconds=300)  # 10 requests per 5 minutes - temporarily disabled
async def login_user(user_credentials: UserLogin):
    """Authenticate user and return JWT tokens."""
    # Check if account is locked
    if security_service.is_account_locked(user_credentials.username):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked due to too many failed login attempts"
        )
    
    # Find user by username
    user = None
    for u in users_db.values():
        if u.username == user_credentials.username:
            user = u
            break
    
    if not user:
        # Record failed attempt for non-existent user
        security_service.record_failed_login(user_credentials.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Verify password
    if not security_service.verify_password(user_credentials.password, user.password):
        # Record failed attempt
        is_locked = security_service.record_failed_login(user_credentials.username)
        if is_locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account locked due to too many failed login attempts"
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    # Reset failed attempts on successful login
    security_service.reset_failed_attempts(user_credentials.username)
    
    # Update last login
    user.last_login = datetime.utcnow()
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security_service.create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value,
            "permissions": [p.value for p in user.permissions]
        },
        expires_delta=access_token_expires
    )
    
    refresh_token = security_service.create_refresh_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value
        }
    )
    
    # Store refresh token
    refresh_tokens_db[refresh_token] = {
        "user_id": user.id,
        "created_at": datetime.utcnow(),
        "is_revoked": False
    }
    
    logger.info(f"User logged in: {user.username}", user_id=user.id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(refresh_request: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    # Verify refresh token
    try:
        payload = security_service.verify_token(refresh_request.refresh_token)
        if payload.username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Check if refresh token exists and is not revoked
    if (refresh_request.refresh_token not in refresh_tokens_db or
        refresh_tokens_db[refresh_request.refresh_token]["is_revoked"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked refresh token"
        )
    
    # Get user
    user = None
    for u in users_db.values():
        if u.username == payload.username:
            user = u
            break
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found or inactive"
        )
    
    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security_service.create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value,
            "permissions": [p.value for p in user.permissions]
        },
        expires_delta=access_token_expires
    )
    
    logger.info(f"Access token refreshed for user: {user.username}", user_id=user.id)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_request.refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user
    )


@router.post("/logout")
async def logout_user(current_user: TokenData = Depends(get_current_user)):
    """Logout user by revoking refresh token."""
    # Find and revoke refresh token
    for token, data in refresh_tokens_db.items():
        if data["user_id"] == current_user.user_id:
            data["is_revoked"] = True
            break
    
    logger.info(f"User logged out: {current_user.username}", user_id=current_user.user_id)
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user


@router.put("/me", response_model=User)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update current user information."""
    # Update user fields
    if user_update.full_name is not None:
        current_user.full_name = sanitize_input(user_update.full_name)
    
    if user_update.email is not None:
        # Check if email is already taken by another user
        if any(u.email == user_update.email and u.id != current_user.id for u in users_db.values()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken"
            )
        current_user.email = user_update.email
    
    # Update in database
    users_db[current_user.id] = current_user
    
    logger.info(f"User updated: {current_user.username}", user_id=current_user.id)
    
    return current_user


@router.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_active_user)
):
    """Change user password."""
    # Verify current password
    if not security_service.verify_password(password_change.current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    current_user.password = security_service.get_password_hash(password_change.new_password)
    users_db[current_user.id] = current_user
    
    # Revoke all refresh tokens for this user
    for token, data in refresh_tokens_db.items():
        if data["user_id"] == current_user.id:
            data["is_revoked"] = True
    
    logger.info(f"Password changed for user: {current_user.username}", user_id=current_user.id)
    
    return {"message": "Password changed successfully"}


@router.post("/request-password-reset")
@rate_limit(max_requests=3, window_seconds=3600)  # 3 requests per hour
async def request_password_reset(reset_request: PasswordResetRequest):
    """Request password reset token."""
    # Find user by email
    user = None
    for u in users_db.values():
        if u.email == reset_request.email:
            user = u
            break
    
    if not user:
        # Don't reveal if email exists or not
        return {"message": "If the email exists, a password reset link has been sent"}
    
    # Generate reset token
    reset_token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    password_reset_tokens_db[reset_token] = {
        "user_id": user.id,
        "expires_at": expires_at,
        "used": False
    }
    
    # In production, send email with reset link
    logger.info(f"Password reset requested for user: {user.username}", user_id=user.id)
    
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
async def reset_password(reset_data: PasswordReset):
    """Reset password using reset token."""
    # Verify reset token
    if reset_data.token not in password_reset_tokens_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
    
    token_data = password_reset_tokens_db[reset_data.token]
    
    # Check if token is expired
    if datetime.utcnow() > token_data["expires_at"]:
        del password_reset_tokens_db[reset_data.token]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )
    
    # Check if token already used
    if token_data["used"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token already used"
        )
    
    # Get user
    user = users_db.get(token_data["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    # Update password
    user.password = security_service.get_password_hash(reset_data.new_password)
    users_db[user.id] = user
    
    # Mark token as used
    token_data["used"] = True
    
    # Revoke all refresh tokens for this user
    for token, data in refresh_tokens_db.items():
        if data["user_id"] == user.id:
            data["is_revoked"] = True
    
    logger.info(f"Password reset for user: {user.username}", user_id=user.id)
    
    return {"message": "Password reset successfully"}


# Admin endpoints
@router.get("/users", response_model=list[User])
async def get_users(current_user: TokenData = Depends(require_permission(Permission.READ_USERS))):
    """Get all users (admin only)."""
    return list(users_db.values())


@router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str, current_user: TokenData = Depends(require_permission(Permission.READ_USERS))):
    """Get user by ID (admin only)."""
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return users_db[user_id]


@router.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: TokenData = Depends(require_permission(Permission.UPDATE_USERS))
):
    """Update user (admin only)."""
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = users_db[user_id]
    
    # Update user fields
    if user_update.full_name is not None:
        user.full_name = sanitize_input(user_update.full_name)
    
    if user_update.email is not None:
        # Check if email is already taken by another user
        if any(u.email == user_update.email and u.id != user_id for u in users_db.values()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken"
            )
        user.email = user_update.email
    
    if user_update.role is not None:
        user.role = user_update.role
        # Update permissions based on new role
        user.permissions = []  # Will be set by validator
    
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    
    # Update in database
    users_db[user_id] = user
    
    logger.info(f"User updated by admin: {user.username}", 
                user_id=user_id, admin_user=current_user.username)
    
    return user


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: TokenData = Depends(require_permission(Permission.DELETE_USERS))):
    """Delete user (admin only)."""
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user = users_db[user_id]
    
    # Prevent self-deletion
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Delete user
    del users_db[user_id]
    
    # Revoke all refresh tokens for this user
    for token, data in refresh_tokens_db.items():
        if data["user_id"] == user_id:
            data["is_revoked"] = True
    
    logger.info(f"User deleted by admin: {user.username}", 
                user_id=user_id, admin_user=current_user.username)
    
    return {"message": "User deleted successfully"}


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "authentication"
    }
