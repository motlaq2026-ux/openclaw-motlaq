"""Authentication and security middleware for OpenClaw API."""

import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
import json
from pathlib import Path

# Security configuration
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
JWT_BEARER = HTTPBearer(auto_error=False)

# Store API keys securely
AUTH_FILE = Path("/app/data/auth.json")
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=15)


class SecurityManager:
    """Manages authentication and security policies."""

    def __init__(self):
        self._api_keys = {}
        self._failed_attempts = {}
        self._load_keys()

    def _load_keys(self):
        """Load API keys from secure storage."""
        if AUTH_FILE.exists():
            with open(AUTH_FILE) as f:
                data = json.load(f)
                self._api_keys = data.get("keys", {})
        else:
            # Generate initial admin key
            admin_key = self._generate_key("admin")
            self._api_keys = {
                "admin": {
                    "key_hash": self._hash_key(admin_key),
                    "created": datetime.utcnow().isoformat(),
                    "last_used": None,
                    "permissions": ["*"],
                }
            }
            self._save_keys()
            print(f"🔐 Generated admin API key: {admin_key}")
            print("⚠️  Save this key securely - it won't be shown again!")

    def _save_keys(self):
        """Save API keys to secure storage."""
        AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(AUTH_FILE, "w") as f:
            json.dump({"keys": self._api_keys}, f, indent=2)

    def _generate_key(self, name: str) -> str:
        """Generate a secure API key."""
        random_part = secrets.token_urlsafe(32)
        return f"oc_{name}_{random_part}"

    def _hash_key(self, key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(key.encode()).hexdigest()

    def verify_key(self, key: str) -> Optional[dict]:
        """Verify an API key and return permissions."""
        if not key:
            return None

        # Check for brute force
        client_ip = "default"  # In production, get from request
        if self._is_locked_out(client_ip):
            raise HTTPException(
                status_code=429, detail="Too many failed attempts. Try again later."
            )

        key_hash = self._hash_key(key)
        for name, data in self._api_keys.items():
            if hmac.compare_digest(data["key_hash"], key_hash):
                self._failed_attempts.pop(client_ip, None)
                data["last_used"] = datetime.utcnow().isoformat()
                self._save_keys()
                return {"name": name, "permissions": data["permissions"]}

        self._record_failed_attempt(client_ip)
        return None

    def _is_locked_out(self, client_ip: str) -> bool:
        """Check if client is locked out due to failed attempts."""
        if client_ip not in self._failed_attempts:
            return False
        attempts, last_attempt = self._failed_attempts[client_ip]
        if attempts >= MAX_FAILED_ATTEMPTS:
            if datetime.utcnow() - last_attempt < LOCKOUT_DURATION:
                return True
            else:
                del self._failed_attempts[client_ip]
        return False

    def _record_failed_attempt(self, client_ip: str):
        """Record a failed authentication attempt."""
        if client_ip not in self._failed_attempts:
            self._failed_attempts[client_ip] = [0, datetime.utcnow()]
        self._failed_attempts[client_ip][0] += 1
        self._failed_attempts[client_ip][1] = datetime.utcnow()


# Global security manager instance
security_manager = SecurityManager()


async def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> dict:
    """Dependency to verify API key."""
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")

    result = security_manager.verify_key(api_key)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return result


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = datetime.utcnow()

        # Clean old entries
        self.requests = {
            ip: [(t, c) for t, c in reqs if now - t < timedelta(minutes=1)]
            for ip, reqs in self.requests.items()
        }

        # Check rate limit
        if client_ip in self.requests:
            recent_requests = len(self.requests[client_ip])
            if recent_requests >= self.requests_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded. Try again later."},
                )

        # Record request
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append((now, 1))

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.requests_per_minute - len(self.requests.get(client_ip, [])))
        )
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response


class CORSMiddlewareSecure(BaseHTTPMiddleware):
    """Secure CORS middleware with specific origins."""

    def __init__(self, app, allowed_origins=None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or [
            "http://localhost:7860",
            "https://localhost:7860",
            "https://*.hf.space",  # HuggingFace Spaces
        ]

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")

        # Check if origin is allowed
        allowed = False
        for allowed_origin in self.allowed_origins:
            if allowed_origin.endswith("*"):
                prefix = allowed_origin.rstrip("*")
                if origin and origin.startswith(prefix):
                    allowed = True
                    break
            elif origin == allowed_origin:
                allowed = True
                break

        response = await call_next(request)

        if allowed and origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, OPTIONS"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization, X-API-Key"
            )
            response.headers["Access-Control-Max-Age"] = "600"

        return response
