"""
Test cases for security components.

This module tests all security-related functionality including:
- Password hashing and validation
- JWT token management
- User authentication and authorization
- Permission and role checking
- Rate limiting
- Input sanitization
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import (
    SecurityService, User, TokenData, UserRole, Permission,
    get_current_user, get_current_active_user, require_permission,
    require_role, rate_limit, sanitize_input, validate_email,
    hash_password, verify_password, create_access_token, verify_token
)
from app.core.config import settings


class TestPasswordSecurity:
    """Test password security functionality."""

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "SecurePass123!"
        
        # Hash password
        hashed = hash_password(password)
        assert hashed != password
        assert len(hashed) > 0
        
        # Verify password
        assert verify_password(password, hashed) is True
        assert verify_password("WrongPassword", hashed) is False

    def test_password_complexity_validation(self):
        """Test password complexity requirements."""
        security_service = SecurityService()
        
        # Valid passwords
        valid_passwords = [
            "SecurePass123!",
            "ComplexP@ssw0rd",
            "MyP@ss123!"
        ]
        
        for password in valid_passwords:
            assert security_service.validate_password_complexity(password) is True
        
        # Invalid passwords
        invalid_passwords = [
            "short",  # Too short
            "nouppercase123!",  # No uppercase
            "NOLOWERCASE123!",  # No lowercase
            "NoNumbers!",  # No numbers
            "NoSpecial123"  # No special characters
        ]
        
        for password in invalid_passwords:
            assert security_service.validate_password_complexity(password) is False

    def test_password_validation_integration(self):
        """Test password validation integration."""
        security_service = SecurityService()
        
        # Test with valid password
        assert security_service.validate_password("SecurePass123!") is True
        
        # Test with invalid password
        assert security_service.validate_password("weak") is False


class TestJWTTokenManagement:
    """Test JWT token creation and validation."""

    def test_create_access_token(self):
        """Test access token creation."""
        user = User(
            id="test-user-id",
            email="test@example.com",
            username="testuser",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        token = create_access_token(user)
        assert token is not None
        assert len(token) > 0
        
        # Verify token structure
        parts = token.split('.')
        assert len(parts) == 3  # Header.Payload.Signature

    def test_verify_token(self):
        """Test token verification."""
        user = User(
            id="test-user-id",
            email="test@example.com",
            username="testuser",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        token = create_access_token(user)
        
        # Verify valid token
        token_data = verify_token(token)
        assert token_data is not None
        assert token_data.email == user.email
        assert token_data.user_id == user.id
        assert token_data.role == user.role

    def test_verify_expired_token(self):
        """Test expired token verification."""
        user = User(
            id="test-user-id",
            email="test@example.com",
            username="testuser",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # Create token with very short expiration
        with patch('app.core.security.settings.ACCESS_TOKEN_EXPIRE_MINUTES', 0):
            token = create_access_token(user)
        
        # Token should be expired
        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)
        
        assert exc_info.value.status_code == 401
        assert "Token has expired" in str(exc_info.value.detail)

    def test_verify_invalid_token(self):
        """Test invalid token verification."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(HTTPException) as exc_info:
            verify_token(invalid_token)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token" in str(exc_info.value.detail)


class TestUserAuthentication:
    """Test user authentication functionality."""

    def test_authenticate_user_success(self):
        """Test successful user authentication."""
        security_service = SecurityService()
        
        # Create test user
        user = User(
            id="test-user-id",
            email="test@example.com",
            username="testuser",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # Mock user retrieval
        with patch.object(security_service, 'get_user_by_email') as mock_get:
            mock_get.return_value = user
            
            # Mock password verification
            with patch.object(security_service, 'verify_password') as mock_verify:
                mock_verify.return_value = True
                
                result = security_service.authenticate_user("test@example.com", "password")
                assert result == user

    def test_authenticate_user_invalid_credentials(self):
        """Test user authentication with invalid credentials."""
        security_service = SecurityService()
        
        # Mock user retrieval
        with patch.object(security_service, 'get_user_by_email') as mock_get:
            mock_get.return_value = None
            
            result = security_service.authenticate_user("test@example.com", "password")
            assert result is None

    def test_authenticate_user_inactive_account(self):
        """Test authentication with inactive account."""
        security_service = SecurityService()
        
        # Create inactive user
        user = User(
            id="test-user-id",
            email="test@example.com",
            username="testuser",
            role=UserRole.USER,
            is_active=False,
            created_at=datetime.utcnow()
        )
        
        # Mock user retrieval
        with patch.object(security_service, 'get_user_by_email') as mock_get:
            mock_get.return_value = user
            
            result = security_service.authenticate_user("test@example.com", "password")
            assert result is None


class TestPermissionAndRoleChecking:
    """Test permission and role checking functionality."""

    def test_user_has_permission(self):
        """Test user permission checking."""
        security_service = SecurityService()
        
        # Create user with specific permissions
        user = User(
            id="test-user-id",
            email="test@example.com",
            username="testuser",
            role=UserRole.ADMIN,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # Admin should have READ_USERS permission
        assert security_service.has_permission(user, Permission.READ_USERS) is True
        
        # Admin should have CREATE_USERS permission
        assert security_service.has_permission(user, Permission.CREATE_USERS) is True
        
        # Regular user should not have these permissions
        regular_user = User(
            id="regular-user-id",
            email="regular@example.com",
            username="regularuser",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        assert security_service.has_permission(regular_user, Permission.READ_USERS) is False
        assert security_service.has_permission(regular_user, Permission.CREATE_USERS) is False

    def test_role_based_permissions(self):
        """Test role-based permission assignment."""
        security_service = SecurityService()
        
        # Test admin role permissions
        admin_user = User(
            id="admin-user-id",
            email="admin@example.com",
            username="adminuser",
            role=UserRole.ADMIN,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        admin_permissions = security_service.get_user_permissions(admin_user)
        assert Permission.READ_USERS in admin_permissions
        assert Permission.CREATE_USERS in admin_permissions
        assert Permission.MANAGE_SYSTEM in admin_permissions
        
        # Test regular user permissions
        regular_user = User(
            id="regular-user-id",
            email="regular@example.com",
            username="regularuser",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        user_permissions = security_service.get_user_permissions(regular_user)
        assert Permission.EXECUTE_TOOL in user_permissions
        assert Permission.CREATE_CHAT in user_permissions
        assert Permission.READ_USERS not in user_permissions


class TestSecurityDependencies:
    """Test security dependency functions."""

    @pytest.mark.asyncio
    async def test_require_permission_success(self):
        """Test successful permission requirement."""
        user = User(
            id="test-user-id",
            email="test@example.com",
            username="testuser",
            role=UserRole.ADMIN,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # Admin should have READ_USERS permission
        result = await require_permission(Permission.READ_USERS)(user)
        assert result == user

    @pytest.mark.asyncio
    async def test_require_permission_failure(self):
        """Test failed permission requirement."""
        user = User(
            id="test-user-id",
            email="test@example.com",
            username="testuser",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # Regular user should not have UPDATE_USERS permission
        with pytest.raises(HTTPException) as exc_info:
            await require_permission(Permission.UPDATE_USERS)(user)
        
        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_require_role_success(self):
        """Test successful role requirement."""
        user = User(
            id="test-user-id",
            email="test@example.com",
            username="testuser",
            role=UserRole.ADMIN,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # User should have ADMIN role
        result = await require_role(UserRole.ADMIN)(user)
        assert result == user

    @pytest.mark.asyncio
    async def test_require_role_failure(self):
        """Test failed role requirement."""
        user = User(
            id="test-user-id",
            email="test@example.com",
            username="testuser",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # User should not have ADMIN role
        with pytest.raises(HTTPException) as exc_info:
            await require_role(UserRole.ADMIN)(user)
        
        assert exc_info.value.status_code == 403
        assert "Insufficient role" in str(exc_info.value.detail)


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limit_decorator(self):
        """Test rate limit decorator."""
        @rate_limit(max_requests=5, window_seconds=60)
        def test_function():
            return "success"
        
        # First 5 calls should succeed
        for i in range(5):
            result = test_function()
            assert result == "success"
        
        # 6th call should be rate limited
        with pytest.raises(HTTPException) as exc_info:
            test_function()
        
        assert exc_info.value.status_code == 429
        assert "Rate limit exceeded" in str(exc_info.value.detail)

    def test_rate_limiter_class(self):
        """Test RateLimiter class functionality."""
        from app.core.security import RateLimiter
        
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        
        # First 3 requests should succeed
        for i in range(3):
            assert limiter.check_rate_limit(f"user_{i}") is True
        
        # 4th request should be blocked
        assert limiter.check_rate_limit("user_4") is False
        
        # Wait for window to reset (in test, we'll just reset manually)
        limiter.requests.clear()
        assert limiter.check_rate_limit("user_5") is True

    def test_rate_limiting_integration(self):
        """Test rate limiting integration with user tracking."""
        from app.core.security import RateLimiter
        
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        # Track requests for specific user
        user_id = "test-user-123"
        
        # First 2 requests should succeed
        assert limiter.check_rate_limit(user_id) is True
        assert limiter.check_rate_limit(user_id) is True
        
        # 3rd request should be blocked
        assert limiter.check_rate_limit(user_id) is False
        
        # Check that user is in the blocked list
        assert user_id in limiter.requests


class TestInputSanitization:
    """Test input sanitization functionality."""

    def test_sanitize_input(self):
        """Test input sanitization."""
        # Test SQL injection prevention
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "<script>alert('xss')</script>"
        ]
        
        for malicious_input in malicious_inputs:
            sanitized = sanitize_input(malicious_input)
            assert "DROP TABLE" not in sanitized
            assert "OR '1'='1" not in sanitized
            assert "<script>" not in sanitized
            assert sanitized != malicious_input

    def test_validate_email(self):
        """Test email validation."""
        # Valid emails
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org"
        ]
        
        for email in valid_emails:
            assert validate_email(email) is True
        
        # Invalid emails
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user.domain.com"
        ]
        
        for email in invalid_emails:
            assert validate_email(email) is False


class TestSecurityService:
    """Test SecurityService class methods."""

    def test_create_user(self):
        """Test user creation."""
        security_service = SecurityService()
        
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "full_name": "New User",
            "password": "SecurePass123!"
        }
        
        with patch.object(security_service, 'hash_password') as mock_hash:
            mock_hash.return_value = "hashed_password"
            
            user = security_service.create_user(**user_data)
            
            assert user.email == user_data["email"]
            assert user.username == user_data["username"]
            assert user.full_name == user_data["full_name"]
            assert user.role == UserRole.USER
            assert user.is_active is True

    def test_get_user_by_id(self):
        """Test user retrieval by ID."""
        security_service = SecurityService()
        
        # Mock database query
        with patch('app.core.security.get_db') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            mock_query = Mock()
            mock_session.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = None
            
            result = security_service.get_user_by_id("test-id")
            assert result is None

    def test_get_users(self):
        """Test users list retrieval."""
        security_service = SecurityService()
        
        # Mock database query
        with patch('app.core.security.get_db') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            mock_query = Mock()
            mock_session.query.return_value = mock_query
            mock_query.all.return_value = []
            
            result = security_service.get_users()
            assert result == []

    def test_update_user(self):
        """Test user update."""
        security_service = SecurityService()
        
        user = User(
            id="test-user-id",
            email="test@example.com",
            username="testuser",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        update_data = {"full_name": "Updated Name"}
        
        with patch('app.core.security.get_db') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            mock_session.commit.return_value = None
            
            result = security_service.update_user(user, **update_data)
            assert result.full_name == "Updated Name"

    def test_delete_user(self):
        """Test user deletion."""
        security_service = SecurityService()
        
        with patch('app.core.security.get_db') as mock_db:
            mock_session = Mock()
            mock_db.return_value = mock_session
            
            mock_session.delete.return_value = None
            mock_session.commit.return_value = None
            
            result = security_service.delete_user("test-id")
            assert result is True


class TestTokenData:
    """Test TokenData model."""

    def test_token_data_creation(self):
        """Test TokenData model creation."""
        token_data = TokenData(
            user_id="test-user-id",
            email="test@example.com",
            role=UserRole.USER,
            permissions=[Permission.EXECUTE_TOOL, Permission.CREATE_CHAT]
        )
        
        assert token_data.user_id == "test-user-id"
        assert token_data.email == "test@example.com"
        assert token_data.role == UserRole.USER
        assert len(token_data.permissions) == 2
        assert Permission.EXECUTE_TOOL in token_data.permissions

    def test_token_data_permissions_validation(self):
        """Test TokenData permissions validation."""
        # Test with string permissions
        token_data = TokenData(
            user_id="test-user-id",
            email="test@example.com",
            role=UserRole.USER,
            permissions=["execute_tool", "create_chat"]
        )
        
        assert len(token_data.permissions) == 2
        assert "execute_tool" in token_data.permissions
        assert "create_chat" in token_data.permissions


# Test fixtures
@pytest.fixture
def mock_user():
    """Mock user for testing."""
    return User(
        id="test-user-id",
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        role=UserRole.USER,
        is_active=True,
        created_at=datetime.utcnow()
    )


@pytest.fixture
def mock_admin_user():
    """Mock admin user for testing."""
    return User(
        id="admin-user-id",
        username="adminuser",
        email="admin@example.com",
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
        created_at=datetime.utcnow()
    )
