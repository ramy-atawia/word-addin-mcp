"""
Test cases for authentication API endpoints.

This module tests all authentication-related endpoints including:
- User registration and login
- JWT token management
- Password reset functionality
- User profile management
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.security import User, UserRole, Permission
from app.core.config import settings


class TestUserRegistration:
    """Test user registration endpoints."""

    def test_user_registration_success(self, test_client: TestClient, valid_user_data: dict):
        """Test successful user registration."""
        with patch('app.api.v1.auth.security_service.create_user') as mock_create:
            mock_create.return_value = User(
                id="new-user-id",
                email=valid_user_data["email"],
                username=valid_user_data["username"],
                full_name=valid_user_data["full_name"],
                role=UserRole.USER,
                is_active=True,
                created_at=datetime.utcnow()
            )

            response = test_client.post("/api/v1/auth/register", json=valid_user_data)

            assert response.status_code == 201
            data = response.json()
            assert data["email"] == valid_user_data["email"]
            assert data["username"] == valid_user_data["username"]
            assert data["full_name"] == valid_user_data["full_name"]
            assert data["role"] == UserRole.USER.value

    def test_user_registration_duplicate_email(self, test_client: TestClient, valid_user_data: dict):
        """Test user registration with duplicate email."""
        with patch('app.api.v1.auth.security_service.create_user') as mock_create:
            mock_create.side_effect = ValueError("Email already registered")

            response = test_client.post("/api/v1/auth/register", json=valid_user_data)

            assert response.status_code == 400
            data = response.json()
            assert "Email already registered" in data["detail"]

    def test_user_registration_duplicate_username(self, test_client: TestClient, valid_user_data: dict):
        """Test user registration with duplicate username."""
        with patch('app.api.v1.auth.security_service.create_user') as mock_create:
            mock_create.side_effect = ValueError("Username already taken")

            response = test_client.post("/api/v1/auth/register", json=valid_user_data)

            assert response.status_code == 400
            data = response.json()
            assert "Username already taken" in data["detail"]

    def test_user_registration_missing_fields(self, test_client: TestClient):
        """Test user registration with missing required fields."""
        required_fields = ["email", "username", "password"]
        valid_user_data = {
            'email': 'test@example.com', 
            'full_name': 'Test User', 
            'password': 'SecurePass123!', 
            'username': 'testuser'
        }

        for field in required_fields:
            user_data = valid_user_data.copy()
            del user_data[field]

            response = test_client.post("/api/v1/auth/register", json=user_data)

            assert response.status_code == 422  # Validation error
            data = response.json()
            assert "field required" in str(data).lower()


class TestUserLogin:
    """Test user login endpoints."""

    def test_user_login_success(self, test_client: TestClient, valid_login_data: dict, mock_user: User):
        """Test successful user login."""
        with patch('app.api.v1.auth.security_service.authenticate_user') as mock_auth:
            mock_auth.return_value = mock_user

            with patch('app.api.v1.auth.security_service.create_access_token') as mock_token:
                mock_token.return_value = "valid_access_token"

                response = test_client.post("/api/v1/auth/login", data=valid_login_data)

                assert response.status_code == 200
                data = response.json()
                assert "access_token" in data
                assert "refresh_token" in data
                assert data["token_type"] == "bearer"

    def test_user_login_invalid_credentials(self, test_client: TestClient, valid_login_data: dict):
        """Test user login with invalid credentials."""
        with patch('app.api.v1.auth.security_service.authenticate_user') as mock_auth:
            mock_auth.return_value = None

            response = test_client.post("/api/v1/auth/login", data=valid_login_data)

            assert response.status_code == 401
            data = response.json()
            assert "Invalid credentials" in data["detail"]

    def test_user_login_inactive_account(self, test_client: TestClient, valid_login_data: dict, mock_user: User):
        """Test user login with inactive account."""
        mock_user.is_active = False

        with patch('app.api.v1.auth.security_service.authenticate_user') as mock_auth:
            mock_auth.return_value = mock_user

            response = test_client.post("/api/v1/auth/login", data=valid_login_data)

            assert response.status_code == 400
            data = response.json()
            assert "Account is inactive" in data["detail"]

    def test_user_login_locked_account(self, test_client: TestClient, valid_login_data: dict):
        """Test user login with locked account."""
        with patch('app.api.v1.auth.security_service.is_account_locked') as mock_locked:
            mock_locked.return_value = True

            response = test_client.post("/api/v1/auth/login", data=valid_login_data)

            assert response.status_code == 423
            data = response.json()
            assert "Account is locked" in data["detail"]

    def test_user_login_missing_fields(self, test_client: TestClient):
        """Test user login with missing fields."""
        response = test_client.post("/api/v1/auth/login", data={})

        assert response.status_code == 422  # Validation error

    def test_user_login_form_data_required(self, test_client: TestClient, valid_login_data: dict):
        """Test that login requires form data, not JSON."""
        response = test_client.post("/api/v1/auth/login", json=valid_login_data)

        assert response.status_code == 422  # Form data required


class TestTokenManagement:
    """Test JWT token management endpoints."""

    def test_token_refresh_success(self, test_client: TestClient, mock_user: User):
        """Test successful token refresh."""
        refresh_token = "valid_refresh_token"

        with patch('app.api.v1.auth.security_service.verify_token') as mock_verify:
            mock_verify.return_value = Mock(
                user_id=mock_user.id,
                email=mock_user.email,
                role=mock_user.role
            )

            with patch('app.api.v1.auth.security_service.get_user_by_id') as mock_get_user:
                mock_get_user.return_value = mock_user

                with patch('app.api.v1.auth.security_service.create_access_token') as mock_create:
                    mock_create.return_value = "new_access_token"

                    response = test_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

                    assert response.status_code == 200
                    data = response.json()
                    assert "access_token" in data
                    assert "refresh_token" in data

    def test_token_refresh_invalid_token(self, test_client: TestClient):
        """Test token refresh with invalid token."""
        with patch('app.api.v1.auth.security_service.verify_token') as mock_verify:
            mock_verify.side_effect = HTTPException(status_code=401, detail="Invalid token")

            response = test_client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid_token"})

            assert response.status_code == 401
            data = response.json()
            assert "Invalid token" in data["detail"]

    def test_token_refresh_user_not_found(self, test_client: TestClient):
        """Test token refresh with non-existent user."""
        refresh_token = "valid_refresh_token"

        with patch('app.api.v1.auth.security_service.verify_token') as mock_verify:
            mock_verify.return_value = Mock(
                user_id="non-existent-user",
                email="nonexistent@example.com",
                role=UserRole.USER
            )

            with patch('app.api.v1.auth.security_service.get_user_by_id') as mock_get_user:
                mock_get_user.return_value = None

                response = test_client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

                assert response.status_code == 404
                data = response.json()
                assert "User not found" in data["detail"]


class TestUserProfile:
    """Test user profile management endpoints."""

    def test_get_user_profile_success(self, test_client: TestClient, mock_user: User):
        """Test successful user profile retrieval."""
        with patch('app.api.v1.auth.get_current_user') as mock_current_user:
            mock_current_user.return_value = mock_user

            response = test_client.get("/api/v1/auth/me")

            assert response.status_code == 200
            data = response.json()
            assert data["email"] == mock_user.email
            assert data["username"] == mock_user.username

    def test_get_user_profile_unauthorized(self, test_client: TestClient):
        """Test user profile retrieval without authentication."""
        response = test_client.get("/api/v1/auth/me")

        assert response.status_code == 401  # Unauthorized

    def test_update_user_profile_success(self, test_client: TestClient, mock_user: User):
        """Test successful user profile update."""
        update_data = {
            "full_name": "Updated Name",
            "username": "updateduser"
        }

        with patch('app.api.v1.auth.get_current_user') as mock_current_user:
            mock_current_user.return_value = mock_user

            with patch('app.api.v1.auth.security_service.update_user') as mock_update:
                updated_user = mock_user.model_copy()
                updated_user.full_name = update_data["full_name"]
                updated_user.username = update_data["username"]
                mock_update.return_value = updated_user

                response = test_client.put("/api/v1/auth/me", json=update_data)

                assert response.status_code == 200
                data = response.json()
                assert data["full_name"] == update_data["full_name"]
                assert data["username"] == update_data["username"]

    def test_update_user_profile_duplicate_username(self, test_client: TestClient, mock_user: User):
        """Test user profile update with duplicate username."""
        update_data = {"username": "existinguser"}

        with patch('app.api.v1.auth.get_current_user') as mock_current_user:
            mock_current_user.return_value = mock_user

            with patch('app.api.v1.auth.security_service.update_user') as mock_update:
                mock_update.side_effect = ValueError("Username already taken")

                response = test_client.put("/api/v1/auth/me", json=update_data)

                assert response.status_code == 400
                data = response.json()
                assert "Username already taken" in data["detail"]

    def test_change_password_success(self, test_client: TestClient, mock_user: User):
        """Test successful password change."""
        password_data = {
            "current_password": "OldPass123!",
            "new_password": "NewPass456!"
        }

        with patch('app.api.v1.auth.get_current_user') as mock_current_user:
            mock_current_user.return_value = mock_user

            with patch('app.api.v1.auth.security_service.verify_password') as mock_verify:
                mock_verify.return_value = True

                with patch('app.api.v1.auth.security_service.update_user') as mock_update:
                    mock_update.return_value = mock_user

                    response = test_client.post("/api/v1/auth/change-password", json=password_data)

                    assert response.status_code == 200
                    data = response.json()
                    assert data["message"] == "Password changed successfully"

    def test_change_password_wrong_current_password(self, test_client: TestClient, mock_user: User):
        """Test password change with wrong current password."""
        password_data = {
            "current_password": "WrongPass123!",
            "new_password": "NewPass456!"
        }

        with patch('app.api.v1.auth.get_current_user') as mock_current_user:
            mock_current_user.return_value = mock_user

            with patch('app.api.v1.auth.security_service.verify_password') as mock_verify:
                mock_verify.return_value = False

                response = test_client.post("/api/v1/auth/change-password", json=password_data)

                assert response.status_code == 400
                data = response.json()
                assert "Current password is incorrect" in data["detail"]

    def test_change_password_invalid_new_password(self, test_client: TestClient, mock_user: User):
        """Test password change with invalid new password."""
        password_data = {
            "current_password": "OldPass123!",
            "new_password": "weak"  # Too weak
        }

        with patch('app.api.v1.auth.get_current_user') as mock_current_user:
            mock_current_user.return_value = mock_user

            response = test_client.post("/api/v1/auth/change-password", json=password_data)

            assert response.status_code == 422  # Validation error


class TestUserManagement:
    """Test user management endpoints (admin only)."""

    def test_get_users_list_success(self, test_client: TestClient, mock_user: User):
        """Test successful users list retrieval (admin)."""
        admin_user = mock_user.model_copy()
        admin_user.role = UserRole.ADMIN

        with patch('app.api.v1.auth.get_current_user') as mock_current_user:
            mock_current_user.return_value = admin_user

            with patch('app.api.v1.auth.security_service.get_users') as mock_get_users:
                mock_get_users.return_value = [mock_user, admin_user]

                response = test_client.get("/api/v1/auth/users")

                assert response.status_code == 200
                data = response.json()
                assert len(data) == 2
                assert data[0]["email"] == mock_user.email
                assert data[1]["email"] == admin_user.email

    def test_get_user_by_id_success(self, test_client: TestClient, mock_user: User):
        """Test successful user retrieval by ID (admin)."""
        admin_user = mock_user.model_copy()
        admin_user.role = UserRole.ADMIN

        with patch('app.api.v1.auth.get_current_user') as mock_current_user:
            mock_current_user.return_value = admin_user

            with patch('app.api.v1.auth.security_service.get_user_by_id') as mock_get_user:
                mock_get_user.return_value = mock_user

                response = test_client.get(f"/api/v1/auth/users/{mock_user.id}")

                assert response.status_code == 200
                data = response.json()
                assert data["email"] == mock_user.email
                assert data["username"] == mock_user.username

    def test_get_user_by_id_not_found(self, test_client: TestClient, mock_user: User):
        """Test user retrieval with non-existent ID."""
        admin_user = mock_user.model_copy()
        admin_user.role = UserRole.ADMIN

        with patch('app.api.v1.auth.get_current_user') as mock_current_user:
            mock_current_user.return_value = admin_user

            with patch('app.api.v1.auth.security_service.get_user_by_id') as mock_get_user:
                mock_get_user.return_value = None

                response = test_client.get("/api/v1/auth/users/non-existent-id")

                assert response.status_code == 404
                data = response.json()
                assert "User not found" in data["detail"]

    def test_update_user_success(self, test_client: TestClient, mock_user: User):
        """Test successful user update (admin)."""
        admin_user = mock_user.model_copy()
        admin_user.role = UserRole.ADMIN

        update_data = {
            "role": UserRole.ADMIN.value,
            "is_active": False
        }

        with patch('app.api.v1.auth.get_current_user') as mock_current_user:
            mock_current_user.return_value = admin_user

            with patch('app.api.v1.auth.security_service.update_user') as mock_update:
                updated_user = mock_user.model_copy()
                updated_user.role = UserRole.ADMIN
                updated_user.is_active = False
                mock_update.return_value = updated_user

                response = test_client.put(f"/api/v1/auth/users/{mock_user.id}", json=update_data)

                assert response.status_code == 200
                data = response.json()
                assert data["role"] == UserRole.ADMIN.value
                assert data["is_active"] == False

    def test_delete_user_success(self, test_client: TestClient, mock_user: User):
        """Test successful user deletion (admin)."""
        admin_user = mock_user.model_copy()
        admin_user.role = UserRole.ADMIN

        with patch('app.api.v1.auth.get_current_user') as mock_current_user:
            mock_current_user.return_value = admin_user

            with patch('app.api.v1.auth.security_service.delete_user') as mock_delete:
                mock_delete.return_value = True

                response = test_client.delete(f"/api/v1/auth/users/{mock_user.id}")

                assert response.status_code == 200
                data = response.json()
                assert data["message"] == "User deleted successfully"

    def test_delete_user_not_found(self, test_client: TestClient, mock_user: User):
        """Test user deletion with non-existent ID."""
        admin_user = mock_user.model_copy()
        admin_user.role = UserRole.ADMIN

        with patch('app.api.v1.auth.security_service.delete_user') as mock_delete:
            mock_delete.return_value = False

            response = test_client.delete("/api/v1/auth/users/non-existent-id")

            assert response.status_code == 404
            data = response.json()
            assert "User not found" in data["detail"]


class TestAuthIntegration:
    """Test complete authentication flows."""

    def test_complete_auth_flow(self, test_client: TestClient, valid_user_data: dict, valid_login_data: dict):
        """Test complete authentication flow: register -> login -> profile."""
        # Step 1: Register user
        with patch('app.api.v1.auth.security_service.create_user') as mock_create:
            mock_create.return_value = User(
                id="new-user-id",
                email=valid_user_data["email"],
                username=valid_user_data["username"],
                full_name=valid_user_data["full_name"],
                role=UserRole.USER,
                is_active=True,
                created_at=datetime.utcnow()
            )

            register_response = test_client.post("/api/v1/auth/register", json=valid_user_data)
            assert register_response.status_code == 201

        # Step 2: Login user
        with patch('app.api.v1.auth.security_service.authenticate_user') as mock_auth:
            mock_auth.return_value = User(
                id="new-user-id",
                email=valid_user_data["email"],
                username=valid_user_data["username"],
                full_name=valid_user_data["full_name"],
                role=UserRole.USER,
                is_active=True,
                created_at=datetime.utcnow()
            )

            with patch('app.api.v1.auth.security_service.create_access_token') as mock_token:
                mock_token.return_value = "valid_access_token"

                login_response = test_client.post("/api/v1/auth/login", data=valid_login_data)
                assert login_response.status_code == 200

                login_data = login_response.json()
                access_token = login_data["access_token"]

        # Step 3: Get user profile
        with patch('app.api.v1.auth.get_current_user') as mock_current_user:
            mock_current_user.return_value = User(
                id="new-user-id",
                email=valid_user_data["email"],
                username=valid_user_data["username"],
                full_name=valid_user_data["full_name"],
                role=UserRole.USER,
                is_active=True,
                created_at=datetime.utcnow()
            )

            headers = {"Authorization": f"Bearer {access_token}"}
            profile_response = test_client.get("/api/v1/auth/me", headers=headers)
            assert profile_response.status_code == 200

            profile_data = profile_response.json()
            assert profile_data["email"] == valid_user_data["email"]
            assert profile_data["username"] == valid_user_data["username"]

    def test_rate_limiting_on_auth_endpoints(self, test_client: TestClient, valid_user_data: dict, valid_login_data: dict):
        """Test that rate limiting is applied to authentication endpoints."""
        # Test rate limiting on registration
        with patch('app.api.v1.auth.security_service.create_user') as mock_create:
            mock_create.return_value = User(
                id="user-1",
                email="user1@example.com",
                username="user1",
                full_name="User 1",
                role=UserRole.USER,
                is_active=True,
                created_at=datetime.utcnow()
            )

            # Make multiple registration attempts
            for i in range(15):  # Exceed auth rate limit (10 per 5 minutes)
                user_data = valid_user_data.copy()
                user_data["email"] = f"user{i}@example.com"
                user_data["username"] = f"user{i}"

                response = test_client.post("/api/v1/auth/register", json=user_data)

                if i < 10:
                    assert response.status_code in [201, 400]  # Success or validation error
                else:
                    assert response.status_code == 429  # Too many requests


# Test fixtures
@pytest.fixture
def valid_user_data():
    """Valid user data for testing."""
    return {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "SecurePass123!",
        "username": "testuser"
    }


@pytest.fixture
def valid_login_data():
    """Valid login data for testing."""
    return {
        "username": "test@example.com",
        "password": "SecurePass123!"
    }


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
