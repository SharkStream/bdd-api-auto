# HTTP Client Implementation Guide

## 📋 Overview

The `HTTPClient` is a production-ready HTTP request agent designed for BDD API automation testing. It provides enterprise-grade features like retry mechanisms, OAuth token management, rate limiting, and comprehensive logging.

---

## 🏗️ Architecture & Components

### 1. **ClientConfig** - Configuration Container
```python
config = ClientConfig(
    base_url="https://api.example.com",
    timeout=30,
    rate_limit_delay=0.5,
    max_retries=3,
    backoff_factor=0.5,
    verify_ssl=True,
    headers={"X-API-Key": "your-key"}
)
```

**Configuration Options:**
- `base_url`: API base URL (required)
- `timeout`: Request timeout in seconds (default: 30)
- `rate_limit_delay`: Delay between requests in seconds (default: 0.0)
- `max_retries`: Maximum retry attempts (default: 3)
- `backoff_factor`: Exponential backoff multiplier (default: 0.5)
- `retry_status_codes`: Status codes to retry on (default: [429, 500, 502, 503, 504])
- `verify_ssl`: Enable SSL verification (default: True)
- `headers`: Default headers to include in all requests

### 2. **HTTPClient** - Main Client Class

#### Initialization
```python
config = ClientConfig(base_url="https://api.example.com")
client = HTTPClient(config)
```

#### Key Features

##### A. Request Methods
```python
client.get(endpoint, params=None, headers=None)
client.post(endpoint, data=None, json_data=None, headers=None)
client.put(endpoint, data=None, json_data=None, headers=None)
client.patch(endpoint, data=None, json_data=None, headers=None)
client.delete(endpoint, params=None, headers=None)
client.head(endpoint, params=None, headers=None)
client.options(endpoint, params=None, headers=None)
client.request(method, endpoint, **kwargs)  # Generic method
```

##### B. OAuth Token Management
```python
# Set token after login
token = login_response.json()["access_token"]
client.set_oauth_token(token)

# Token is automatically included in Authorization header
response = client.get("/protected-resource")
```

##### C. Header Management
```python
# Set single header
client.set_header("X-Request-ID", "12345")

# Set multiple headers
client.set_headers({
    "X-Correlation-ID": "abc-123",
    "X-Client-Version": "1.0"
})

# Override headers for specific request
response = client.get("/data", headers={"X-Override": "value"})
```

##### D. Authentication Methods
```python
# OAuth Bearer Token (recommended for APIs)
client.set_oauth_token("your-token-here")

# HTTP Basic Auth
client.set_basic_auth("username", "password")

# Custom Headers
client.set_header("Authorization", "Custom your-token")
```

##### E. Rate Limiting & Timeout Control
```python
# Global rate limit delay
client.set_rate_limit_delay(1.0)  # 1 second between requests

# Per-request timeout override
response = client.get("/slow-endpoint", timeout=60)

# Global timeout in config
config = ClientConfig(base_url="...", timeout=30)
```

##### F. Retry Mechanism (Automatic)
```python
# Automatically handles retries with exponential backoff
# Retry strategy:
# - Retries on: 429, 500, 502, 503, 504
# - Backoff: 0.5s, 1s, 2s, 4s, 8s (for 3 retries)
# - No action needed - happens transparently!

response = client.get("/data")  # Retries handled automatically
```

##### G. Request/Response Hooks
```python
# Hook for pre-request processing
def add_custom_header(method, url, kwargs):
    if "headers" not in kwargs:
        kwargs["headers"] = {}
    kwargs["headers"]["X-Timestamp"] = str(time.time())
    return kwargs

# Hook for post-response processing
def log_response_details(response):
    print(f"Status: {response.status_code}")
    print(f"Time: {response.elapsed.total_seconds()}s")

client.register_request_hook(add_custom_header)
client.register_response_hook(log_response_details)
```

---

## 📝 Usage Patterns

### Pattern 1: Simple GET Request
```python
config = ClientConfig(base_url="https://api.example.com")
client = HTTPClient(config)

response = client.get("/users")
data = response.json()
```

### Pattern 2: OAuth Authentication Flow
```python
# 1. Login
login_response = client.post(
    "/auth/login",
    json_data={"email": "user@example.com", "password": "pass123"}
)

# 2. Extract token
token = login_response.json().get("access_token")

# 3. Set token for subsequent requests
client.set_oauth_token(token)

# 4. All requests now include token
user_data = client.get("/users/me").json()
```

### Pattern 3: Resource Management with Context Manager
```python
config = ClientConfig(base_url="https://api.example.com")

with HTTPClient(config) as client:
    response = client.get("/data")
    # Session automatically closed when exiting
```

### Pattern 4: Custom Headers with Each Request
```python
response = client.get(
    "/data",
    params={"id": 123},
    headers={"X-Custom": "value"},
    timeout=15
)
```

### Pattern 5: Batch Operations with Rate Limiting
```python
client.set_rate_limit_delay(1.0)  # 1 second between requests

for item_id in range(1, 101):
    response = client.get(f"/items/{item_id}")
    # Automatic 1-second delay between requests
```

### Pattern 6: Multiple Clients with Factory
```python
# Create named client instances
api_v1 = ClientFactory.create_client("v1", "https://api-v1.example.com")
api_v2 = ClientFactory.create_client("v2", "https://api-v2.example.com")

# Get existing client
api_v1_again = ClientFactory.get_client("v1")

# Close all clients
ClientFactory.close_all()
```

### Pattern 7: Error Handling
```python
try:
    response = client.post(
        "/users",
        json_data={"name": "John"}
    )
    response.raise_for_status()  # Raises HTTPError for bad status codes
    data = response.json()
except requests.exceptions.HTTPError as e:
    logger.error(f"HTTP Error: {e}")
except requests.exceptions.Timeout as e:
    logger.error(f"Timeout: {e}")
except requests.exceptions.RequestException as e:
    logger.error(f"Request Error: {e}")
```

---

## 🔄 Retry Mechanism Details

### How It Works
The client uses `urllib3`'s built-in retry mechanism with the following defaults:

**Default Configuration:**
- Max retries: 3
- Retry on status codes: 429 (Rate Limit), 500, 502, 503, 504 (Server Errors)
- Backoff factor: 0.5 (exponential)
- Backoff progression: 0.5s → 1s → 2s → 4s → 8s

### Custom Retry Configuration
```python
config = ClientConfig(
    base_url="https://api.example.com",
    max_retries=5,
    backoff_factor=1.0,  # Slower backoff
    retry_status_codes=[429, 500, 502, 503, 504, 503]
)
client = HTTPClient(config)
```

### Backoff Calculation
```
wait_time = backoff_factor * (2 ^ (attempt - 1))

Example with backoff_factor=0.5:
Attempt 1: 0.5 * (2 ^ 0) = 0.5s
Attempt 2: 0.5 * (2 ^ 1) = 1.0s
Attempt 3: 0.5 * (2 ^ 2) = 2.0s
Attempt 4: 0.5 * (2 ^ 3) = 4.0s
Attempt 5: 0.5 * (2 ^ 4) = 8.0s
```

---

## 🔐 OAuth Token Management

### Flow 1: Manual Token Management
```python
# Login and get token
response = client.post(
    "/auth/login",
    json_data={"username": "user", "password": "pass"}
)
token = response.json()["access_token"]

# Set for all requests
client.set_oauth_token(token)

# Make authenticated requests
response = client.get("/protected")
```

### Flow 2: Automatic Token Refresh
```python
# Store refresh token
refresh_token = login_response.json()["refresh_token"]

# When token expires, refresh it
refresh_response = client.post(
    "/auth/refresh",
    json_data={"refresh_token": refresh_token}
)
new_token = refresh_response.json()["access_token"]
client.set_oauth_token(new_token)
```

### Implementation Tip for BDD Steps
```python
@given('I am logged in as "{username}"')
def step_login(context, username):
    config = ClientConfig(base_url=context.api_base_url)
    context.client = HTTPClient(config)
    
    # Get credentials from config
    password = context.config.user_credentials[username]
    
    # Login
    response = context.client.post(
        "/auth/login",
        json_data={"username": username, "password": password}
    )
    
    # Set token
    token = response.json()["access_token"]
    context.client.set_oauth_token(token)
```

---

## 📊 Request/Response Logging

### Automatic Logging
All requests and responses are automatically logged:
```
🌐 GET https://api.example.com/users
   Params: {'page': 1}
   Headers: {'X-API-Key': '...'}
✅ Response Status: 200
   Response: {"users": [...]}
```

### Custom Logging via Hooks
```python
def log_performance(response):
    elapsed = response.elapsed.total_seconds()
    if elapsed > 5:
        logger.warning(f"⚠️  Slow response: {elapsed}s for {response.url}")

client.register_response_hook(log_performance)
```

---

## 💡 Best Practices

### 1. **Always Use Context Manager**
```python
# ✅ Good
with HTTPClient(config) as client:
    response = client.get("/data")

# ⚠️ Avoid (may leak resources)
client = HTTPClient(config)
response = client.get("/data")
```

### 2. **Reuse Client Instances**
```python
# ✅ Good - reuse single client
client = HTTPClient(config)
for i in range(100):
    response = client.get(f"/items/{i}")

# ⚠️ Avoid - creates new client each iteration
for i in range(100):
    client = HTTPClient(config)
    response = client.get(f"/items/{i}")
```

### 3. **Use Factory for Multiple APIs**
```python
# ✅ Good
github_client = ClientFactory.create_client("github", "https://api.github.com")
slack_client = ClientFactory.create_client("slack", "https://slack.com/api")
```

### 4. **Configure Rate Limiting**
```python
# ✅ Good - respects API rate limits
client.set_rate_limit_delay(1.0)

# ⚠️ Bad - may hit rate limit
client = HTTPClient(ClientConfig(base_url="...", rate_limit_delay=0))
```

### 5. **Handle Exceptions Properly**
```python
# ✅ Good
try:
    response = client.post("/users", json_data={...})
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    logger.error(f"HTTP {e.response.status_code}: {e}")
except requests.exceptions.Timeout:
    logger.error("Request timeout")

# ⚠️ Bad
response = client.post("/users", json_data={...})
data = response.json()  # May crash if response is error
```

### 6. **Set Appropriate Timeouts**
```python
# ✅ Good - explicit timeouts
response = client.get("/quick-endpoint", timeout=5)
response = client.get("/slow-endpoint", timeout=60)

# ⚠️ Bad - no timeout
response = client.get("/any-endpoint")  # Uses default 30s
```

---

## 🧪 Integration with BDD Steps

### Example BDD Feature File
```gherkin
Feature: User API
    Background:
        Given the base API URL is "https://api.example.com"
        And I set the request timeout to 30 seconds

    Scenario: Create a new user
        Given I am logged in as "admin"
        When I create a user with name "John Doe" and email "john@example.com"
        Then the response status code is 201
        And the response contains user ID
        And the new user can be retrieved by ID

    Scenario: Rate-limited API calls
        Given I set rate limit delay to 1 second
        When I fetch 10 users sequentially
        Then all requests should complete
        And request delays should be respected
```

### Example Step Implementation
```python
from behave import given, when, then
from utils.client import HTTPClient, ClientConfig

@given('the base API URL is "{base_url}"')
def step_set_base_url(context, base_url):
    config = ClientConfig(base_url=base_url, timeout=30)
    context.client = HTTPClient(config)

@given('I am logged in as "{username}"')
def step_login(context, username):
    response = context.client.post(
        "/auth/login",
        json_data=get_credentials(username)
    )
    token = response.json()["access_token"]
    context.client.set_oauth_token(token)

@when('I create a user with name "{name}" and email "{email}"')
def step_create_user(context, name, email):
    context.response = context.client.post(
        "/users",
        json_data={"name": name, "email": email}
    )

@then('the response status code is {code:d}')
def step_check_status(context, code):
    assert context.response.status_code == code
```

---

## 📋 Features Summary

| Feature | Status | Details |
|---------|--------|---------|
| HTTP Methods | ✅ | GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS |
| Base URL | ✅ | Configurable, updatable at runtime |
| Headers | ✅ | Default headers, per-request override |
| Timeout | ✅ | Global + per-request configuration |
| Rate Limiting | ✅ | Configurable delay between requests |
| Retry Mechanism | ✅ | Exponential backoff, configurable |
| OAuth Tokens | ✅ | Set/update tokens, auto-include in requests |
| Basic Auth | ✅ | Built-in HTTP Basic Authentication |
| Connection Pooling | ✅ | Automatic via HTTPAdapter |
| Request/Response Hooks | ✅ | Pre/post request processing |
| Logging | ✅ | Integrated with project logger |
| Context Manager | ✅ | Automatic resource cleanup |
| Client Factory | ✅ | Manage multiple clients |
| SSL Verification | ✅ | Configurable verification |

---

## 🚀 Performance Tips

1. **Reuse single client instance** - Better connection pooling
2. **Set appropriate rate limits** - Avoid hammering APIs
3. **Use connection pooling** - Already configured by default
4. **Cache tokens** - Avoid re-authentication
5. **Monitor response times** - Use response hooks
6. **Batch requests efficiently** - Group by rate limit

---

## ❌ Common Pitfalls & Solutions

| Problem | Cause | Solution |
|---------|-------|----------|
| Connection leaks | Not closing client | Use context manager |
| Slow tests | No rate limiting | Set `rate_limit_delay` |
| Token expired | Stale OAuth token | Refresh before API calls |
| Timeout errors | Default 30s too short | Override with `timeout` param |
| 401 Unauthorized | Token not set | Call `set_oauth_token()` |
| Rate limit hit | No delays between requests | Use rate limiting |
| SSL errors | Verification enabled | Set `verify_ssl=False` in config |

---

## 📚 References

- [Requests Library Documentation](https://docs.python-requests.org/)
- [urllib3 Retry Documentation](https://urllib3.readthedocs.io/en/latest/reference/urllib3.util.retry.html)
- [OAuth 2.0 Bearer Token RFC](https://tools.ietf.org/html/rfc6750)
- [BDD/Behave Documentation](https://behave.readthedocs.io/)
