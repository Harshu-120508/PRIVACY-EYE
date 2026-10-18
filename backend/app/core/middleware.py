"""
Custom middleware: Rate limiting, Request ID injection, and CSRF protection.
"""
import time
import uuid
import secrets
from collections import defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request for tracing."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory sliding-window rate limiter.
    For production, replace with Redis-backed limiter (e.g. slowapi).
    """

    def __init__(self, app, calls: int = 30, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self._requests: dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health check and high-frequency live camera frames
        if request.url.path in ["/", "/api/v1/health"] or request.url.path.startswith("/api/v1/live/frame"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - self.period

        # Prune old requests
        self._requests[client_ip] = [t for t in self._requests[client_ip] if t > window_start]

        if len(self._requests[client_ip]) >= self.calls:
            logger.warning("Rate limit exceeded", client_ip=client_ip)
            return Response(
                content='{"detail":"Rate limit exceeded. Please slow down."}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(self.period)},
            )

        self._requests[client_ip].append(now)
        return await call_next(request)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Double-submit cookie CSRF protection.

    How it works:
    1. On every response, we set a `csrf_token` cookie (readable by JS).
    2. On state-changing requests (POST/PUT/PATCH/DELETE) that use cookie-based auth,
       the client must send an `X-CSRF-Token` header matching the cookie value.
    3. Requests using Bearer token auth (API clients, mobile) are EXEMPT from
       CSRF checks because they are not vulnerable to CSRF attacks.
    4. Safe methods (GET/HEAD/OPTIONS) are always exempt.
    5. Health/docs endpoints are always exempt.

    This is the OWASP-recommended "Double Submit Cookie" pattern.
    """

    EXEMPT_PATHS = frozenset([
        "/", "/health", "/ready", "/docs", "/redoc", "/openapi.json",
        "/api/v1/health", "/api/v1/ready",
    ])

    SAFE_METHODS = frozenset(["GET", "HEAD", "OPTIONS"])

    async def dispatch(self, request: Request, call_next):
        # Always allow safe methods
        if request.method in self.SAFE_METHODS:
            response = await call_next(request)
            self._set_csrf_cookie(response)
            return response

        # Always allow exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            response = await call_next(request)
            return response

        # If the request uses Bearer auth (not cookie-based), CSRF is not needed
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            response = await call_next(request)
            return response

        # For cookie-based auth on state-changing methods, validate CSRF token
        cookie_token = request.cookies.get("csrf_token")
        header_token = request.headers.get("x-csrf-token")

        if cookie_token and header_token and secrets.compare_digest(cookie_token, header_token):
            response = await call_next(request)
            self._set_csrf_cookie(response)
            return response

        # If no cookies are present at all (e.g. unauthenticated registration/login),
        # allow through — CSRF only matters for authenticated cookie sessions
        if "access_token" not in request.cookies:
            response = await call_next(request)
            self._set_csrf_cookie(response)
            return response

        # CSRF validation failed
        logger.warning("CSRF token validation failed", path=request.url.path)
        return Response(
            content='{"detail":"CSRF token missing or invalid. Include X-CSRF-Token header."}',
            status_code=403,
            media_type="application/json",
        )

    def _set_csrf_cookie(self, response: Response) -> None:
        """Set a fresh CSRF token cookie on the response (readable by JS)."""
        token = secrets.token_urlsafe(32)
        response.set_cookie(
            key="csrf_token",
            value=token,
            httponly=False,  # Must be readable by JavaScript
            samesite="lax",
            secure=False,  # Set to True in production behind HTTPS
            max_age=86400,  # 24 hours
            path="/",
        )

