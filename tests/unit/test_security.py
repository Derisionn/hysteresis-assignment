"""Unit tests for JWT utilities."""

import pytest
from datetime import timedelta
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_password,
    verify_password
)


def test_create_access_token():
    """Test access token creation."""
    data = {"sub": "user123"}
    token = create_access_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_refresh_token():
    """Test refresh token creation."""
    data = {"sub": "user123"}
    token = create_refresh_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_verify_valid_access_token():
    """Test verifying valid access token."""
    data = {"sub": "user123", "email": "test@example.com"}
    token = create_access_token(data)
    
    payload = verify_token(token, token_type="access")
    
    assert payload is not None
    assert payload["sub"] == "user123"
    assert payload["email"] == "test@example.com"
    assert payload["type"] == "access"


def test_verify_valid_refresh_token():
    """Test verifying valid refresh token."""
    data = {"sub": "user123"}
    token = create_refresh_token(data)
    
    payload = verify_token(token, token_type="refresh")
    
    assert payload is not None
    assert payload["sub"] == "user123"
    assert payload["type"] == "refresh"


def test_verify_invalid_token():
    """Test verifying invalid token."""
    invalid_token = "invalid.token.here"
    
    payload = verify_token(invalid_token)
    
    assert payload is None


def test_verify_wrong_token_type():
    """Test verifying token with wrong type."""
    data = {"sub": "user123"}
    access_token = create_access_token(data)
    
    # Try to verify access token as refresh token
    payload = verify_token(access_token, token_type="refresh")
    
    assert payload is None


def test_hash_password():
    """Test password hashing."""
    password = "SecurePassword123!"
    hashed = hash_password(password)
    
    assert hashed is not None
    assert hashed != password
    assert len(hashed) > 0


def test_verify_correct_password():
    """Test verifying correct password."""
    password = "SecurePassword123!"
    hashed = hash_password(password)
    
    assert verify_password(password, hashed) is True


def test_verify_incorrect_password():
    """Test verifying incorrect password."""
    password = "SecurePassword123!"
    wrong_password = "WrongPassword456!"
    hashed = hash_password(password)
    
    assert verify_password(wrong_password, hashed) is False


def test_token_expiration():
    """Test token with custom expiration."""
    data = {"sub": "user123"}
    # Create token with very short expiration
    token = create_access_token(data, expires_delta=timedelta(seconds=1))
    
    # Immediately verify - should work
    payload = verify_token(token)
    assert payload is not None
    
    # Note: Testing actual expiration would require time.sleep()
    # which we avoid in unit tests
