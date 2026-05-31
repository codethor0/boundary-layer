"""HTTP middleware for BoundaryLayer API."""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from apps.api.config import Settings, get_settings
from apps.api.rate_limit import RateLimitUnavailable, build_rate_limiter

logger = logging.getLogger("boundary_layer.api")

PRODUCTION_LOCKDOWN_PATHS = frozenset({"/docs", "/redoc", "/openapi.json"})


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach request IDs and emit structured access logs."""

    def __init__(self, app, settings: Settings):
        super().__init__(app)
        self.settings = settings

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        started = time.perf_counter()

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        if self.settings.log_request_id:
            elapsed_ms = (time.perf_counter() - started) * 1000
            client_ip = request.client.host if request.client else "unknown"
            logger.info(
                "request completed",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code,
                    "client_ip": client_ip,
                },
            )
            response.headers["X-Response-Time-Ms"] = f"{elapsed_ms:.2f}"
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add baseline security headers to every response."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
        )
        return response


class ProductionLockdownMiddleware(BaseHTTPMiddleware):
    """Hide documentation and schema endpoints in production."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        settings = get_settings()
        if (
            settings.is_production
            and not settings.expose_openapi
            and request.url.path in PRODUCTION_LOCKDOWN_PATHS
        ):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter with optional Redis backend."""

    def __init__(self, app):
        super().__init__(app)
        self._limiter = None
        self._backend = None

    def _client_key(self, request: Request, settings: Settings) -> str:
        if settings.trust_proxy_headers:
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                parts = [part.strip() for part in forwarded.split(",") if part.strip()]
                if parts:
                    # Nginx appends the real client IP as the rightmost hop.
                    return parts[-1]
        if request.client:
            return request.client.host
        return "unknown"

    def _get_limiter(self, settings: Settings):
        if self._limiter is None or self._backend != settings.rate_limit_backend:
            self._backend = settings.rate_limit_backend
            fail_open = not settings.is_production
            self._limiter = build_rate_limiter(
                settings.rate_limit_backend,
                fail_open=fail_open,
            )
        return self._limiter

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        settings = get_settings()
        if not settings.rate_limit_enabled:
            return await call_next(request)
        if request.url.path in {"/health", "/ready"}:
            return await call_next(request)

        window = settings.rate_limit_window_seconds
        limit = settings.rate_limit_requests
        key = self._client_key(request, settings)
        try:
            allowed, remaining = self._get_limiter(settings).allow(key, limit, window)
        except RateLimitUnavailable:
            return JSONResponse(
                status_code=503,
                content={"detail": "Rate limiting unavailable"},
            )

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(window)},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window-Seconds"] = str(window)
        return response
