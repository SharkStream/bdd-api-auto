"""
HTTP Request Client with retry mechanism, OAuth support, and rate limiting.
Designed for BDD API automation testing.
"""

import time
import json
from typing import Optional, Dict, Any, Union, List
from urllib.parse import urljoin
from dataclasses import dataclass
from enum import Enum

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry as URLRetry
from requests.auth import HTTPBasicAuth

from utils.logger import setup_logger

logger = setup_logger(__name__)


class RequestMethod(Enum):
    """Supported HTTP request methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class HTTPStatusCode(Enum):
    """Common HTTP status codes."""
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    RATE_LIMIT = 429
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503


@dataclass
class ClientConfig:
    """Configuration for HTTP client."""
    base_url: str
    timeout: int = 30
    rate_limit_delay: float = 0.0  # Delay between requests in seconds
    max_retries: int = 3
    backoff_factor: float = 0.5  # Exponential backoff multiplier
    retry_status_codes: List[int] = None
    verify_ssl: bool = True
    headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.retry_status_codes is None:
            # Retry on 5xx and rate limit (429) by default
            self.retry_status_codes = [429, 500, 502, 503, 504]
        if self.headers is None:
            self.headers = {}


class HTTPClient:
    """
    Production-ready HTTP client for API testing with:
    - Retry mechanism with exponential backoff
    - OAuth token management
    - Rate limiting
    - Request/Response logging
    - Connection pooling
    - Configurable timeouts
    """
    
    def __init__(self, config: ClientConfig):
        """
        Initialize HTTP client with configuration.
        
        Args:
            config: ClientConfig object with client settings
        """
        self.config = config
        self.base_url = config.base_url
        self.session = self._create_session()
        self.oauth_token: Optional[str] = None
        self.last_request_time: float = 0.0
        self.response_hooks: List[callable] = []
        self.request_hooks: List[callable] = []
        
        logger.info(f"🌐 HTTP Client initialized with base_url: {self.base_url}")
    
    def _create_session(self) -> requests.Session:
        """
        Create a requests session with connection pooling and retry strategy.
        
        Returns:
            Configured requests.Session with HTTPAdapter and retry strategy
        """
        session = requests.Session()
        
        # Configure retry strategy for urllib3
        retry_strategy = URLRetry(
            total=self.config.max_retries,
            status_forcelist=self.config.retry_status_codes,
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"],
            backoff_factor=self.config.backoff_factor
        )
        
        # Apply to both HTTP and HTTPS
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            "User-Agent": "BDD-API-Automation-Client/1.0",
            "Accept": "application/json",
            **self.config.headers
        })
        
        return session
    
    def set_oauth_token(self, token: str) -> None:
        """
        Set OAuth token for subsequent requests.
        
        Args:
            token: Bearer token string
        """
        self.oauth_token = token
        self._update_auth_header()
        logger.info("✅ OAuth token set successfully")
    
    def _update_auth_header(self) -> None:
        """Update Authorization header with current OAuth token."""
        if self.oauth_token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.oauth_token}"
            })
        else:
            self.session.headers.pop("Authorization", None)
    
    def set_header(self, key: str, value: str) -> None:
        """
        Set a custom header.
        
        Args:
            key: Header name
            value: Header value
        """
        self.session.headers.update({key: value})
        logger.info(f"📝 Header set: {key}")
    
    def set_headers(self, headers: Dict[str, str]) -> None:
        """
        Set multiple headers at once.
        
        Args:
            headers: Dictionary of headers
        """
        self.session.headers.update(headers)
        logger.info(f"📝 Headers updated: {list(headers.keys())}")
    
    def set_basic_auth(self, username: str, password: str) -> None:
        """
        Set HTTP Basic Authentication.
        
        Args:
            username: Username
            password: Password
        """
        self.session.auth = HTTPBasicAuth(username, password)
        logger.info("✅ Basic authentication configured")
    
    def set_base_url(self, base_url: str) -> None:
        """
        Update base URL.
        
        Args:
            base_url: New base URL
        """
        self.base_url = base_url
        logger.info(f"🔄 Base URL updated: {self.base_url}")
    
    def set_rate_limit_delay(self, delay: float) -> None:
        """
        Set rate limit delay between requests.
        
        Args:
            delay: Delay in seconds
        """
        self.config.rate_limit_delay = delay
        logger.info(f"🚀 Rate limit delay set to: {delay}s")
    
    def _apply_rate_limit(self) -> None:
        """Apply rate limiting by delaying requests if necessary."""
        if self.config.rate_limit_delay > 0:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.config.rate_limit_delay:
                sleep_time = self.config.rate_limit_delay - elapsed
                time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def register_request_hook(self, hook: callable) -> None:
        """
        Register a hook to be called before request.
        Useful for modifying request before sending.
        
        Args:
            hook: Callable that takes (method, url, kwargs) and returns modified kwargs
        """
        self.request_hooks.append(hook)
    
    def register_response_hook(self, hook: callable) -> None:
        """
        Register a hook to be called after response received.
        Useful for response preprocessing.
        
        Args:
            hook: Callable that takes response object
        """
        self.response_hooks.append(hook)
    
    def _execute_request_hooks(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Execute all registered request hooks."""
        for hook in self.request_hooks:
            kwargs = hook(method, url, kwargs) or kwargs
        return kwargs
    
    def _execute_response_hooks(self, response: requests.Response) -> None:
        """Execute all registered response hooks."""
        for hook in self.response_hooks:
            hook(response)
    
    def _build_url(self, endpoint: str) -> str:
        """
        Build complete URL from endpoint.
        
        Args:
            endpoint: API endpoint (relative or absolute)
        
        Returns:
            Complete URL
        """
        # If endpoint is already absolute, return as-is
        if endpoint.startswith(('http://', 'https://')):
            return endpoint
        
        # Otherwise, join with base URL
        return urljoin(self.base_url, endpoint)
    
    def request(
        self,
        method: Union[str, RequestMethod],
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        verify_ssl: Optional[bool] = None,
        **kwargs
    ) -> requests.Response:
        """
        Make an HTTP request with retry mechanism and rate limiting.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body (form data or string)
            json_data: JSON request body
            headers: Additional headers for this request
            timeout: Request timeout in seconds (uses config default if not specified)
            verify_ssl: SSL verification (uses config default if not specified)
            **kwargs: Additional arguments passed to requests
        
        Returns:
            requests.Response object
        
        Raises:
            requests.RequestException: If request fails after retries
        """
        # Convert method to string if RequestMethod enum
        if isinstance(method, RequestMethod):
            method = method.value
        
        method = method.upper()
        url = self._build_url(endpoint)
        
        # Apply rate limiting
        self._apply_rate_limit()
        
        # Prepare request kwargs
        request_kwargs = {
            "params": params,
            "timeout": timeout or self.config.timeout,
            "verify": verify_ssl if verify_ssl is not None else self.config.verify_ssl,
            **kwargs
        }
        
        # Set body
        if json_data:
            request_kwargs["json"] = json_data
        elif data:
            request_kwargs["data"] = data
        
        # Merge headers
        if headers:
            merged_headers = {**self.session.headers, **headers}
            request_kwargs["headers"] = merged_headers
        
        # Execute request hooks
        request_kwargs = self._execute_request_hooks(method, url, **request_kwargs)
        
        # Log request
        self._log_request(method, url, request_kwargs)
        
        try:
            response = self.session.request(method, url, **request_kwargs)
            
            # Execute response hooks
            self._execute_response_hooks(response)
            
            # Log response
            self._log_response(response)
            
            # Raise for HTTP errors
            response.raise_for_status()
            
            return response
        
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request failed: {str(e)}")
            raise
    
    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> requests.Response:
        """GET request."""
        return self.request(RequestMethod.GET, endpoint, params=params, headers=headers, **kwargs)
    
    def post(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> requests.Response:
        """POST request."""
        return self.request(
            RequestMethod.POST,
            endpoint,
            data=data,
            json_data=json_data,
            headers=headers,
            **kwargs
        )
    
    def put(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> requests.Response:
        """PUT request."""
        return self.request(
            RequestMethod.PUT,
            endpoint,
            data=data,
            json_data=json_data,
            headers=headers,
            **kwargs
        )
    
    def patch(
        self,
        endpoint: str,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> requests.Response:
        """PATCH request."""
        return self.request(
            RequestMethod.PATCH,
            endpoint,
            data=data,
            json_data=json_data,
            headers=headers,
            **kwargs
        )
    
    def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> requests.Response:
        """DELETE request."""
        return self.request(
            RequestMethod.DELETE,
            endpoint,
            params=params,
            headers=headers,
            **kwargs
        )
    
    def head(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> requests.Response:
        """HEAD request."""
        return self.request(
            RequestMethod.HEAD,
            endpoint,
            params=params,
            headers=headers,
            **kwargs
        )
    
    def options(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> requests.Response:
        """OPTIONS request."""
        return self.request(
            RequestMethod.OPTIONS,
            endpoint,
            params=params,
            headers=headers,
            **kwargs
        )
    
    def _log_request(self, method: str, url: str, kwargs: Dict[str, Any]) -> None:
        """Log HTTP request details."""
        logger.info(f"🌐 {method} {url}")
        
        if kwargs.get("params"):
            logger.info(f"   Params: {kwargs['params']}")
        
        if kwargs.get("headers") and kwargs["headers"]:
            safe_headers = {k: v for k, v in kwargs["headers"].items() if k != "Authorization"}
            logger.info(f"   Headers: {safe_headers}")
        
        if kwargs.get("json"):
            logger.info(f"   Body: {json.dumps(kwargs['json'], indent=2)}")
        elif kwargs.get("data") and isinstance(kwargs["data"], dict):
            logger.info(f"   Body: {json.dumps(kwargs['data'], indent=2)}")
    
    def _log_response(self, response: requests.Response) -> None:
        """Log HTTP response details."""
        status_emoji = "✅" if response.status_code < 400 else "❌"
        logger.info(f"{status_emoji} Response Status: {response.status_code}")
        
        if response.headers.get("content-type", "").startswith("application/json"):
            try:
                logger.info(f"   Response: {json.dumps(response.json(), indent=2)[:500]}")
            except (json.JSONDecodeError, ValueError):
                logger.info(f"   Response: {response.text[:500]}")
        else:
            logger.info(f"   Response: {response.text[:500]}")
    
    def close(self) -> None:
        """Close the session and cleanup resources."""
        self.session.close()
        logger.info("🔄 HTTP Client session closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class ClientFactory:
    """Factory for creating HTTP client instances."""
    
    _clients: Dict[str, HTTPClient] = {}
    
    @classmethod
    def create_client(
        cls,
        name: str,
        base_url: str,
        timeout: int = 30,
        rate_limit_delay: float = 0.0,
        max_retries: int = 3,
        **kwargs
    ) -> HTTPClient:
        """
        Create and cache HTTP client instance.
        
        Args:
            name: Client identifier
            base_url: Base URL for API
            timeout: Request timeout
            rate_limit_delay: Delay between requests
            max_retries: Maximum retry attempts
            **kwargs: Additional config parameters
        
        Returns:
            HTTPClient instance
        """
        if name not in cls._clients:
            config = ClientConfig(
                base_url=base_url,
                timeout=timeout,
                rate_limit_delay=rate_limit_delay,
                max_retries=max_retries,
                **kwargs
            )
            cls._clients[name] = HTTPClient(config)
        
        return cls._clients[name]
    
    @classmethod
    def get_client(cls, name: str) -> Optional[HTTPClient]:
        """
        Get existing client instance.
        
        Args:
            name: Client identifier
        
        Returns:
            HTTPClient instance or None if not found
        """
        return cls._clients.get(name)
    
    @classmethod
    def close_all(cls) -> None:
        """Close all client instances."""
        for client in cls._clients.values():
            client.close()
        cls._clients.clear()
