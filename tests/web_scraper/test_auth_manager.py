"""Tests for authentication management."""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from research_scrapers.web_scraper.auth_manager import (
    AuthManager, BearerAuth
)


class TestBearerAuth:
    """Test BearerAuth class."""
    
    def test_bearer_auth_initialization(self):
        """Test BearerAuth initialization."""
        auth = BearerAuth("test_token_123")
        assert auth.token == "test_token_123"
    
    def test_bearer_auth_call(self):
        """Test BearerAuth adds authorization header."""
        auth = BearerAuth("test_token_123")
        
        # Create a mock request
        request = Mock(spec=requests.PreparedRequest)
        request.headers = {}
        
        # Call the auth handler
        result = auth(request)
        
        assert result.headers["Authorization"] == "Bearer test_token_123"
        assert result is request  # Should return same request object


class TestAuthManagerInitialization:
    """Test AuthManager initialization."""
    
    def test_default_initialization(self):
        """Test default initialization with no auth."""
        manager = AuthManager()
        
        assert manager.auth_type == "none"
        assert manager.username is None
        assert manager.password is None
        assert manager.token is None
        assert manager.cookies == {}
        assert manager.headers == {}
        assert manager.session is None
        assert manager._authenticated is False
    
    def test_basic_auth_initialization(self):
        """Test initialization with basic auth."""
        manager = AuthManager(
            auth_type="basic",
            username="testuser",
            password="testpass"
        )
        
        assert manager.auth_type == "basic"
        assert manager.username == "testuser"
        assert manager.password == "testpass"
    
    def test_bearer_auth_initialization(self):
        """Test initialization with bearer token."""
        manager = AuthManager(
            auth_type="bearer",
            token="test_token_123"
        )
        
        assert manager.auth_type == "bearer"
        assert manager.token == "test_token_123"
    
    def test_cookie_auth_initialization(self):
        """Test initialization with cookies."""
        cookies = {"session_id": "abc123", "user_token": "xyz789"}
        manager = AuthManager(
            auth_type="cookie",
            cookies=cookies
        )
        
        assert manager.auth_type == "cookie"
        assert manager.cookies == cookies
    
    def test_form_auth_initialization(self):
        """Test initialization with form auth."""
        manager = AuthManager(
            auth_type="form",
            username="testuser",
            password="testpass",
            form_login_url="https://example.com/login",
            form_fields={"csrf_token": "token123"}
        )
        
        assert manager.auth_type == "form"
        assert manager.form_login_url == "https://example.com/login"
        assert manager.form_fields == {"csrf_token": "token123"}
    
    def test_custom_headers_initialization(self):
        """Test initialization with custom headers."""
        headers = {"X-API-Key": "key123", "X-Client-ID": "client456"}
        manager = AuthManager(
            auth_type="none",
            headers=headers
        )
        
        assert manager.headers == headers
    
    def test_auth_type_case_insensitive(self):
        """Test that auth_type is case insensitive."""
        manager1 = AuthManager(auth_type="BASIC", username="user", password="pass")
        manager2 = AuthManager(auth_type="Basic", username="user", password="pass")
        manager3 = AuthManager(auth_type="basic", username="user", password="pass")
        
        assert manager1.auth_type == "basic"
        assert manager2.auth_type == "basic"
        assert manager3.auth_type == "basic"


class TestAuthManagerSession:
    """Test AuthManager session management."""
    
    def test_get_session_creates_session(self):
        """Test that get_session creates a new session."""
        manager = AuthManager()
        session = manager.get_session()
        
        assert isinstance(session, requests.Session)
        assert manager.session is not None
        assert manager.session is session
    
    def test_get_session_returns_existing_session(self):
        """Test that get_session returns existing session."""
        manager = AuthManager()
        session1 = manager.get_session()
        session2 = manager.get_session()
        
        assert session1 is session2
    
    def test_close_session(self):
        """Test closing authentication session."""
        manager = AuthManager()
        session = manager.get_session()
        
        assert manager.session is not None
        
        manager.close()
        
        assert manager.session is None
        assert manager._authenticated is False


class TestNoAuth:
    """Test no authentication."""
    
    def test_no_auth_setup(self):
        """Test setup with no authentication."""
        manager = AuthManager(auth_type="none")
        session = manager.get_session()
        
        assert manager.is_authenticated() is True
        assert session.auth is None
    
    def test_no_auth_headers(self):
        """Test get_auth_headers with no auth."""
        manager = AuthManager(auth_type="none")
        headers = manager.get_auth_headers()
        
        assert headers == {}
    
    def test_no_auth_cookies(self):
        """Test get_cookies with no auth."""
        manager = AuthManager(auth_type="none")
        cookies = manager.get_cookies()
        
        assert cookies == {}


class TestBasicAuth:
    """Test HTTP Basic authentication."""
    
    def test_basic_auth_setup(self):
        """Test setup with basic authentication."""
        manager = AuthManager(
            auth_type="basic",
            username="testuser",
            password="testpass"
        )
        session = manager.get_session()
        
        assert manager.is_authenticated() is True
        assert isinstance(session.auth, requests.auth.HTTPBasicAuth)
    
    def test_basic_auth_missing_username(self):
        """Test basic auth fails without username."""
        manager = AuthManager(
            auth_type="basic",
            password="testpass"
        )
        
        with pytest.raises(ValueError, match="Username and password required"):
            manager.get_session()
    
    def test_basic_auth_missing_password(self):
        """Test basic auth fails without password."""
        manager = AuthManager(
            auth_type="basic",
            username="testuser"
        )
        
        with pytest.raises(ValueError, match="Username and password required"):
            manager.get_session()
    
    def test_basic_auth_missing_both(self):
        """Test basic auth fails without username and password."""
        manager = AuthManager(auth_type="basic")
        
        with pytest.raises(ValueError, match="Username and password required"):
            manager.get_session()


class TestBearerTokenAuth:
    """Test Bearer token authentication."""
    
    def test_bearer_auth_setup(self):
        """Test setup with bearer authentication."""
        manager = AuthManager(
            auth_type="bearer",
            token="test_token_123"
        )
        session = manager.get_session()
        
        assert manager.is_authenticated() is True
        assert isinstance(session.auth, BearerAuth)
    
    def test_bearer_auth_missing_token(self):
        """Test bearer auth fails without token."""
        manager = AuthManager(auth_type="bearer")
        
        with pytest.raises(ValueError, match="Token required"):
            manager.get_session()
    
    def test_bearer_auth_headers(self):
        """Test get_auth_headers with bearer token."""
        manager = AuthManager(
            auth_type="bearer",
            token="test_token_123"
        )
        headers = manager.get_auth_headers()
        
        assert headers["Authorization"] == "Bearer test_token_123"
    
    def test_bearer_auth_with_custom_headers(self):
        """Test bearer auth with additional custom headers."""
        manager = AuthManager(
            auth_type="bearer",
            token="test_token_123",
            headers={"X-API-Key": "key456"}
        )
        headers = manager.get_auth_headers()
        
        assert headers["Authorization"] == "Bearer test_token_123"
        assert headers["X-API-Key"] == "key456"


class TestCookieAuth:
    """Test cookie-based authentication."""
    
    def test_cookie_auth_setup(self):
        """Test setup with cookie authentication."""
        cookies = {"session_id": "abc123"}
        manager = AuthManager(
            auth_type="cookie",
            cookies=cookies
        )
        session = manager.get_session()
        
        assert manager.is_authenticated() is True
        assert "session_id" in session.cookies
    
    def test_cookie_auth_missing_cookies(self):
        """Test cookie auth fails without cookies."""
        manager = AuthManager(auth_type="cookie")
        
        with pytest.raises(ValueError, match="Cookies required"):
            manager.get_session()
    
    def test_cookie_auth_empty_cookies(self):
        """Test cookie auth fails with empty cookies dict."""
        manager = AuthManager(auth_type="cookie", cookies={})
        
        with pytest.raises(ValueError, match="Cookies required"):
            manager.get_session()
    
    def test_get_cookies(self):
        """Test get_cookies returns cookie dict."""
        cookies = {"session_id": "abc123", "user_token": "xyz789"}
        manager = AuthManager(
            auth_type="cookie",
            cookies=cookies
        )
        
        retrieved_cookies = manager.get_cookies()
        assert retrieved_cookies == cookies
    
    def test_get_cookies_from_session(self):
        """Test get_cookies returns cookies from session."""
        cookies = {"session_id": "abc123"}
        manager = AuthManager(
            auth_type="cookie",
            cookies=cookies
        )
        session = manager.get_session()
        
        # Add a cookie to the session
        session.cookies.set("new_cookie", "new_value")
        
        retrieved_cookies = manager.get_cookies()
        assert "session_id" in retrieved_cookies
        assert "new_cookie" in retrieved_cookies


class TestFormAuth:
    """Test form-based authentication."""
    
    @patch('requests.Session.post')
    def test_form_auth_successful(self, mock_post):
        """Test successful form authentication."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        manager = AuthManager(
            auth_type="form",
            username="testuser",
            password="testpass",
            form_login_url="https://example.com/login"
        )
        session = manager.get_session()
        
        assert manager.is_authenticated() is True
        mock_post.assert_called_once()
    
    @patch('requests.Session.post')
    def test_form_auth_failed(self, mock_post):
        """Test failed form authentication."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        manager = AuthManager(
            auth_type="form",
            username="testuser",
            password="testpass",
            form_login_url="https://example.com/login"
        )
        session = manager.get_session()
        
        assert manager.is_authenticated() is False
    
    @patch('requests.Session.post')
    def test_form_auth_with_custom_fields(self, mock_post):
        """Test form auth with custom form fields."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        form_fields = {"csrf_token": "token123", "remember_me": "true"}
        manager = AuthManager(
            auth_type="form",
            username="testuser",
            password="testpass",
            form_login_url="https://example.com/login",
            form_fields=form_fields
        )
        manager.get_session()
        
        # Verify the form data includes custom fields
        call_args = mock_post.call_args
        form_data = call_args.kwargs['data']
        
        assert form_data["username"] == "testuser"
        assert form_data["password"] == "testpass"
        assert form_data["csrf_token"] == "token123"
        assert form_data["remember_me"] == "true"
    
    @patch('requests.Session.post')
    def test_form_auth_exception_handling(self, mock_post):
        """Test form auth handles exceptions."""
        mock_post.side_effect = requests.RequestException("Network error")
        
        manager = AuthManager(
            auth_type="form",
            username="testuser",
            password="testpass",
            form_login_url="https://example.com/login"
        )
        session = manager.get_session()
        
        assert manager.is_authenticated() is False
    
    def test_form_auth_missing_url(self):
        """Test form auth fails without login URL."""
        manager = AuthManager(
            auth_type="form",
            username="testuser",
            password="testpass"
        )
        
        with pytest.raises(ValueError, match="Form login URL required"):
            manager.get_session()
    
    def test_form_auth_missing_username(self):
        """Test form auth fails without username."""
        manager = AuthManager(
            auth_type="form",
            password="testpass",
            form_login_url="https://example.com/login"
        )
        
        with pytest.raises(ValueError, match="Username and password required"):
            manager.get_session()
    
    def test_form_auth_missing_password(self):
        """Test form auth fails without password."""
        manager = AuthManager(
            auth_type="form",
            username="testuser",
            form_login_url="https://example.com/login"
        )
        
        with pytest.raises(ValueError, match="Username and password required"):
            manager.get_session()


class TestCustomHeaders:
    """Test custom headers functionality."""
    
    def test_custom_headers_applied_to_session(self):
        """Test custom headers are applied to session."""
        headers = {"X-API-Key": "key123", "User-Agent": "CustomBot/1.0"}
        manager = AuthManager(
            auth_type="none",
            headers=headers
        )
        session = manager.get_session()
        
        assert session.headers["X-API-Key"] == "key123"
        assert session.headers["User-Agent"] == "CustomBot/1.0"
    
    def test_update_headers(self):
        """Test updating headers."""
        manager = AuthManager(
            auth_type="none",
            headers={"X-API-Key": "key123"}
        )
        
        new_headers = {"X-Client-ID": "client456"}
        manager.update_headers(new_headers)
        
        assert manager.headers["X-API-Key"] == "key123"
        assert manager.headers["X-Client-ID"] == "client456"
    
    def test_update_headers_with_session(self):
        """Test updating headers updates existing session."""
        manager = AuthManager(auth_type="none")
        session = manager.get_session()
        
        new_headers = {"X-Custom-Header": "value"}
        manager.update_headers(new_headers)
        
        assert session.headers["X-Custom-Header"] == "value"
    
    def test_headers_with_bearer_auth(self):
        """Test custom headers work with bearer auth."""
        manager = AuthManager(
            auth_type="bearer",
            token="test_token_123",
            headers={"X-API-Version": "v2"}
        )
        session = manager.get_session()
        
        assert session.headers["X-API-Version"] == "v2"


class TestCookieManagement:
    """Test cookie management functionality."""
    
    def test_update_cookies(self):
        """Test updating cookies."""
        manager = AuthManager(
            auth_type="cookie",
            cookies={"session_id": "abc123"}
        )
        
        new_cookies = {"user_token": "xyz789"}
        manager.update_cookies(new_cookies)
        
        assert manager.cookies["session_id"] == "abc123"
        assert manager.cookies["user_token"] == "xyz789"
    
    def test_update_cookies_with_session(self):
        """Test updating cookies updates existing session."""
        manager = AuthManager(
            auth_type="cookie",
            cookies={"session_id": "abc123"}
        )
        session = manager.get_session()
        
        new_cookies = {"user_token": "xyz789"}
        manager.update_cookies(new_cookies)
        
        cookies_dict = dict(session.cookies)
        assert "session_id" in cookies_dict
        assert "user_token" in cookies_dict
    
    def test_get_cookies_returns_copy(self):
        """Test that get_cookies returns a copy, not reference."""
        cookies = {"session_id": "abc123"}
        manager = AuthManager(auth_type="cookie", cookies=cookies)
        
        retrieved_cookies = manager.get_cookies()
        retrieved_cookies["new_key"] = "new_value"
        
        # Original cookies should not be modified
        assert "new_key" not in manager.cookies


class TestInvalidAuthType:
    """Test handling of invalid authentication types."""
    
    def test_invalid_auth_type(self):
        """Test that invalid auth type raises ValueError."""
        manager = AuthManager(auth_type="invalid_type")
        
        with pytest.raises(ValueError, match="Unknown auth type"):
            manager.get_session()


class TestAuthenticationStatus:
    """Test authentication status checking."""
    
    def test_is_authenticated_initially_false(self):
        """Test authentication status is initially false."""
        manager = AuthManager(auth_type="basic", username="user", password="pass")
        assert manager.is_authenticated() is False
    
    def test_is_authenticated_after_setup(self):
        """Test authentication status after setup."""
        manager = AuthManager(auth_type="none")
        manager.get_session()
        assert manager.is_authenticated() is True
    
    def test_is_authenticated_reset_on_close(self):
        """Test authentication status reset on close."""
        manager = AuthManager(auth_type="none")
        manager.get_session()
        assert manager.is_authenticated() is True
        
        manager.close()
        assert manager.is_authenticated() is False


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_multiple_get_session_calls(self):
        """Test multiple calls to get_session."""
        manager = AuthManager(
            auth_type="basic",
            username="testuser",
            password="testpass"
        )
        
        session1 = manager.get_session()
        session2 = manager.get_session()
        session3 = manager.get_session()
        
        # All should return the same session instance
        assert session1 is session2
        assert session2 is session3
    
    def test_close_and_reopen_session(self):
        """Test closing and reopening session."""
        manager = AuthManager(
            auth_type="basic",
            username="testuser",
            password="testpass"
        )
        
        session1 = manager.get_session()
        manager.close()
        session2 = manager.get_session()
        
        # Should create new session after close
        assert session1 is not session2
        assert isinstance(session2, requests.Session)
    
    def test_empty_custom_headers(self):
        """Test with empty custom headers dict."""
        manager = AuthManager(auth_type="none", headers={})
        session = manager.get_session()
        
        assert manager.is_authenticated() is True
    
    def test_empty_form_fields(self):
        """Test form auth with empty form_fields dict."""
        with patch('requests.Session.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            manager = AuthManager(
                auth_type="form",
                username="testuser",
                password="testpass",
                form_login_url="https://example.com/login",
                form_fields={}
            )
            manager.get_session()
            
            # Should still include username and password
            call_args = mock_post.call_args
            form_data = call_args.kwargs['data']
            assert form_data["username"] == "testuser"
            assert form_data["password"] == "testpass"
    
    def test_bearer_token_with_spaces(self):
        """Test bearer token containing spaces."""
        manager = AuthManager(
            auth_type="bearer",
            token="token with spaces"
        )
        headers = manager.get_auth_headers()
        
        assert headers["Authorization"] == "Bearer token with spaces"
    
    def test_special_characters_in_credentials(self):
        """Test special characters in username and password."""
        manager = AuthManager(
            auth_type="basic",
            username="user@example.com",
            password="p@$$w0rd!#$%"
        )
        session = manager.get_session()
        
        assert manager.is_authenticated() is True
        assert isinstance(session.auth, requests.auth.HTTPBasicAuth)


class TestIntegration:
    """Integration tests for AuthManager."""
    
    def test_bearer_auth_end_to_end(self):
        """Test complete bearer auth workflow."""
        manager = AuthManager(
            auth_type="bearer",
            token="test_token_123",
            headers={"X-API-Version": "v2"}
        )
        
        # Get session
        session = manager.get_session()
        assert manager.is_authenticated() is True
        
        # Check headers
        headers = manager.get_auth_headers()
        assert headers["Authorization"] == "Bearer test_token_123"
        assert headers["X-API-Version"] == "v2"
        
        # Update headers
        manager.update_headers({"X-Client-ID": "client789"})
        assert session.headers["X-Client-ID"] == "client789"
        
        # Close session
        manager.close()
        assert manager.session is None
        assert manager.is_authenticated() is False
    
    def test_cookie_auth_end_to_end(self):
        """Test complete cookie auth workflow."""
        initial_cookies = {"session_id": "abc123"}
        manager = AuthManager(
            auth_type="cookie",
            cookies=initial_cookies
        )
        
        # Get session
        session = manager.get_session()
        assert manager.is_authenticated() is True
        
        # Get cookies
        cookies = manager.get_cookies()
        assert cookies["session_id"] == "abc123"
        
        # Update cookies
        manager.update_cookies({"user_token": "xyz789"})
        cookies = manager.get_cookies()
        assert cookies["session_id"] == "abc123"
        assert cookies["user_token"] == "xyz789"
        
        # Close session
        manager.close()
        assert manager.session is None
