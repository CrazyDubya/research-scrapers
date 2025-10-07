"""Authentication management for web scraping."""

import requests
from typing import Optional, Dict, Any
from loguru import logger
from requests.auth import HTTPBasicAuth, AuthBase


class BearerAuth(AuthBase):
    """Bearer token authentication."""
    
    def __init__(self, token: str):
        self.token = token
    
    def __call__(self, r: requests.PreparedRequest) -> requests.PreparedRequest:
        r.headers["Authorization"] = f"Bearer {self.token}"
        return r


class AuthManager:
    """Manage authentication for web scraping."""
    
    def __init__(
        self,
        auth_type: str = "none",
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        form_login_url: Optional[str] = None,
        form_fields: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize authentication manager.
        
        Args:
            auth_type: Type of authentication (none, basic, bearer, cookie, form)
            username: Username for basic/form auth
            password: Password for basic/form auth
            token: Bearer token
            cookies: Cookie dictionary
            headers: Additional headers
            form_login_url: URL for form-based login
            form_fields: Form field mapping for login
        """
        self.auth_type = auth_type.lower()
        self.username = username
        self.password = password
        self.token = token
        self.cookies = cookies or {}
        self.headers = headers or {}
        self.form_login_url = form_login_url
        self.form_fields = form_fields or {}
        
        self.session: Optional[requests.Session] = None
        self._authenticated = False
        
        logger.info(f"Initialized AuthManager with type: {self.auth_type}")
    
    def get_session(self) -> requests.Session:
        """Get authenticated session."""
        if self.session is None:
            self.session = requests.Session()
            self._setup_auth()
        
        return self.session
    
    def _setup_auth(self) -> None:
        """Setup authentication on session."""
        if self.auth_type == "none":
            logger.debug("No authentication configured")
            self._authenticated = True
            return
        
        if self.auth_type == "basic":
            self._setup_basic_auth()
        elif self.auth_type == "bearer":
            self._setup_bearer_auth()
        elif self.auth_type == "cookie":
            self._setup_cookie_auth()
        elif self.auth_type == "form":
            self._setup_form_auth()
        else:
            raise ValueError(f"Unknown auth type: {self.auth_type}")
        
        # Apply custom headers
        if self.headers:
            self.session.headers.update(self.headers)
    
    def _setup_basic_auth(self) -> None:
        """Setup HTTP Basic authentication."""
        if not self.username or not self.password:
            raise ValueError("Username and password required for basic auth")
        
        self.session.auth = HTTPBasicAuth(self.username, self.password)
        logger.info(f"Setup basic auth for user: {self.username}")
        self._authenticated = True
    
    def _setup_bearer_auth(self) -> None:
        """Setup Bearer token authentication."""
        if not self.token:
            raise ValueError("Token required for bearer auth")
        
        self.session.auth = BearerAuth(self.token)
        logger.info("Setup bearer token auth")
        self._authenticated = True
    
    def _setup_cookie_auth(self) -> None:
        """Setup cookie-based authentication."""
        if not self.cookies:
            raise ValueError("Cookies required for cookie auth")
        
        self.session.cookies.update(self.cookies)
        logger.info(f"Setup cookie auth with {len(self.cookies)} cookies")
        self._authenticated = True
    
    def _setup_form_auth(self) -> None:
        """Setup form-based authentication."""
        if not self.form_login_url:
            raise ValueError("Form login URL required for form auth")
        
        if not self.username or not self.password:
            raise ValueError("Username and password required for form auth")
        
        # Prepare form data
        form_data = self.form_fields.copy()
        form_data.update({
            "username": self.username,
            "password": self.password,
        })
        
        try:
            logger.info(f"Attempting form login to {self.form_login_url}")
            response = self.session.post(
                self.form_login_url,
                data=form_data,
                headers=self.headers,
            )
            
            if response.status_code == 200:
                logger.info("Form login successful")
                self._authenticated = True
            else:
                logger.error(
                    f"Form login failed with status {response.status_code}"
                )
                self._authenticated = False
        
        except Exception as e:
            logger.error(f"Form login error: {e}")
            self._authenticated = False
    
    def is_authenticated(self) -> bool:
        """Check if authenticated."""
        return self._authenticated
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        headers = self.headers.copy()
        
        if self.auth_type == "bearer" and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        return headers
    
    def get_cookies(self) -> Dict[str, str]:
        """Get authentication cookies."""
        if self.session:
            return dict(self.session.cookies)
        return self.cookies.copy()
    
    def update_cookies(self, cookies: Dict[str, str]) -> None:
        """Update session cookies."""
        self.cookies.update(cookies)
        if self.session:
            self.session.cookies.update(cookies)
        logger.debug(f"Updated {len(cookies)} cookies")
    
    def update_headers(self, headers: Dict[str, str]) -> None:
        """Update session headers."""
        self.headers.update(headers)
        if self.session:
            self.session.headers.update(headers)
        logger.debug(f"Updated {len(headers)} headers")
    
    def close(self) -> None:
        """Close authentication session."""
        if self.session:
            self.session.close()
            self.session = None
            self._authenticated = False
            logger.debug("Closed auth session")
