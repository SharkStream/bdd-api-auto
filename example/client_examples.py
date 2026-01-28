"""
Example usage guide for HTTPClient - showing all features and best practices.
"""

from utils.client import HTTPClient, ClientConfig, RequestMethod, ClientFactory


# ============================================================================
# BASIC USAGE
# ============================================================================

def example_basic_usage():
    """Basic client setup and simple requests."""
    
    # Initialize with configuration
    config = ClientConfig(
        base_url="https://api.example.com",
        timeout=30,
        rate_limit_delay=0.5,  # 500ms delay between requests
        max_retries=3,
        verify_ssl=True
    )
    
    client = HTTPClient(config)
    
    # Simple GET request
    response = client.get("/users")
    data = response.json()
    
    # Simple POST request
    response = client.post("/users", json_data={"name": "John", "email": "john@example.com"})
    
    client.close()


# ============================================================================
# OAUTH TOKEN MANAGEMENT
# ============================================================================

def example_oauth_flow():
    """Login and manage OAuth tokens."""
    
    config = ClientConfig(base_url="https://api.example.com")
    client = HTTPClient(config)
    
    # Step 1: Login and get token
    login_response = client.post(
        "/auth/login",
        json_data={"username": "user@example.com", "password": "password123"}
    )
    
    token = login_response.json().get("access_token")
    
    # Step 2: Set OAuth token for subsequent requests
    client.set_oauth_token(token)
    
    # Step 3: Now all requests include Authorization header
    response = client.get("/users/me")  # Token sent automatically
    
    # Step 4: Refresh token when needed
    refresh_response = client.post(
        "/auth/refresh",
        json_data={"refresh_token": login_response.json().get("refresh_token")}
    )
    new_token = refresh_response.json().get("access_token")
    client.set_oauth_token(new_token)
    
    client.close()


# ============================================================================
# CUSTOM HEADERS AND AUTHENTICATION
# ============================================================================

def example_custom_headers_auth():
    """Configure custom headers and authentication."""
    
    config = ClientConfig(
        base_url="https://api.example.com",
        headers={
            "X-API-Key": "your-api-key",
            "X-Custom-Header": "custom-value"
        }
    )
    
    client = HTTPClient(config)
    
    # Set individual header
    client.set_header("X-Request-ID", "12345-67890")
    
    # Set multiple headers
    client.set_headers({
        "X-Correlation-ID": "abc-def-ghi",
        "X-Client-Version": "1.0"
    })
    
    # Use Basic Authentication
    client.set_basic_auth("username", "password")
    
    # Set OAuth token
    client.set_oauth_token("eyJhbGc...")
    
    # Override headers for specific request
    response = client.get(
        "/data",
        headers={"X-Custom-Override": "value"}
    )
    
    client.close()


# ============================================================================
# RATE LIMITING AND TIMEOUTS
# ============================================================================

def example_rate_limiting():
    """Configure rate limiting and custom timeouts."""
    
    config = ClientConfig(
        base_url="https://api.example.com",
        rate_limit_delay=1.0,  # 1 second between requests
        timeout=15  # Global timeout
    )
    
    client = HTTPClient(config)
    
    # Update rate limit at runtime
    client.set_rate_limit_delay(2.0)
    
    # Make multiple requests with rate limiting applied
    for i in range(5):
        response = client.get(f"/endpoint{i}")
    
    # Override timeout for specific request
    response = client.get("/slow-endpoint", timeout=60)
    
    client.close()


# ============================================================================
# RETRY MECHANISM
# ============================================================================

def example_retry_mechanism():
    """Configure and use retry mechanism."""
    
    config = ClientConfig(
        base_url="https://api.example.com",
        max_retries=5,
        backoff_factor=0.5,  # Exponential backoff: 0.5s, 1s, 2s, 4s, 8s
        retry_status_codes=[429, 500, 502, 503, 504]
    )
    
    client = HTTPClient(config)
    
    # This will automatically retry on 5xx errors and rate limits
    response = client.get("/data")
    
    # The retry happens transparently with exponential backoff
    client.close()


# ============================================================================
# DIFFERENT HTTP METHODS
# ============================================================================

def example_http_methods():
    """Use different HTTP methods."""
    
    config = ClientConfig(base_url="https://api.example.com")
    client = HTTPClient(config)
    
    # GET
    response = client.get("/users", params={"page": 1, "limit": 10})
    
    # POST
    response = client.post("/users", json_data={"name": "Alice"})
    
    # PUT (full update)
    response = client.put("/users/123", json_data={"name": "Bob", "email": "bob@example.com"})
    
    # PATCH (partial update)
    response = client.patch("/users/123", json_data={"email": "newemail@example.com"})
    
    # DELETE
    response = client.delete("/users/123")
    
    # HEAD (check resource without body)
    response = client.head("/users/123")
    
    # OPTIONS (get allowed methods)
    response = client.options("/users")
    
    # Generic request method
    response = client.request(RequestMethod.GET, "/data", params={"key": "value"})
    
    client.close()


# ============================================================================
# REQUEST AND RESPONSE HOOKS
# ============================================================================

def example_hooks():
    """Register hooks for pre/post request processing."""
    
    config = ClientConfig(base_url="https://api.example.com")
    client = HTTPClient(config)
    
    # Hook to add timestamp to all requests
    def add_timestamp_hook(method, url, kwargs):
        import time
        if "headers" not in kwargs:
            kwargs["headers"] = {}
        kwargs["headers"]["X-Timestamp"] = str(int(time.time()))
        return kwargs
    
    # Hook to log response metrics
    def log_response_time(response):
        elapsed = response.elapsed.total_seconds()
        print(f"Response took {elapsed}s")
    
    # Register hooks
    client.register_request_hook(add_timestamp_hook)
    client.register_response_hook(log_response_time)
    
    # Now all requests include timestamp header and response time is logged
    response = client.get("/data")
    
    client.close()


# ============================================================================
# CONTEXT MANAGER (RESOURCE CLEANUP)
# ============================================================================

def example_context_manager():
    """Use client as context manager for automatic cleanup."""
    
    config = ClientConfig(base_url="https://api.example.com")
    
    # Session automatically closed when exiting the block
    with HTTPClient(config) as client:
        response = client.get("/data")
        print(response.json())
    
    # Session is closed here automatically


# ============================================================================
# CLIENT FACTORY (SINGLETON PATTERN)
# ============================================================================

def example_client_factory():
    """Use factory pattern to manage multiple client instances."""
    
    # Create first client
    client1 = ClientFactory.create_client(
        name="api_v1",
        base_url="https://api-v1.example.com",
        timeout=30
    )
    
    # Create second client
    client2 = ClientFactory.create_client(
        name="api_v2",
        base_url="https://api-v2.example.com",
        timeout=20
    )
    
    # Get existing client
    client1_again = ClientFactory.get_client("api_v1")
    
    # Use clients
    response1 = client1.get("/data")
    response2 = client2.get("/data")
    
    # Close all clients
    ClientFactory.close_all()


# ============================================================================
# COMPLEX WORKFLOW EXAMPLE
# ============================================================================

def example_complex_workflow():
    """Complete workflow combining multiple features."""
    
    # 1. Setup client with configuration
    config = ClientConfig(
        base_url="https://api.example.com",
        timeout=30,
        rate_limit_delay=0.5,
        max_retries=3,
        verify_ssl=True
    )
    
    with HTTPClient(config) as client:
        # 2. Login and get token
        login_response = client.post(
            "/auth/login",
            json_data={"email": "user@example.com", "password": "pass"}
        )
        token = login_response.json()["access_token"]
        client.set_oauth_token(token)
        
        # 3. Set custom headers
        client.set_headers({
            "X-Client-ID": "my-client",
            "X-API-Version": "v1"
        })
        
        # 4. Add hooks for monitoring
        def log_request_hook(method, url, kwargs):
            print(f"Making {method} request to {url}")
            return kwargs
        
        client.register_request_hook(log_request_hook)
        
        # 5. Make paginated requests with rate limiting
        page = 1
        all_users = []
        
        while True:
            response = client.get("/users", params={"page": page, "limit": 100})
            data = response.json()
            
            if not data["results"]:
                break
            
            all_users.extend(data["results"])
            page += 1
        
        # 6. Create new resource
        new_user = client.post(
            "/users",
            json_data={
                "name": "Jane Doe",
                "email": "jane@example.com"
            }
        )
        user_id = new_user.json()["id"]
        
        # 7. Update resource
        client.patch(
            f"/users/{user_id}",
            json_data={"status": "active"}
        )
        
        # 8. Delete resource
        client.delete(f"/users/{user_id}")
        
        print(f"Processed {len(all_users)} users successfully")


if __name__ == "__main__":
    # Run examples
    print("HTTP Client Examples\n")
    
    print("1. Basic Usage")
    # example_basic_usage()
    
    print("\n2. OAuth Flow")
    # example_oauth_flow()
    
    print("\n3. Custom Headers and Auth")
    # example_custom_headers_auth()
    
    print("\n4. Rate Limiting")
    # example_rate_limiting()
    
    print("\n5. Complex Workflow")
    # example_complex_workflow()
