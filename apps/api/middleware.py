"""HTTP middleware for BoundaryLayer API."""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from apps.api.config import Settings, get_settings

logger = logging.getLogger("boundary_layer.api")


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


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory sliding-window rate limiter keyed by client IP."""

    def __init__(self, app):
        super().__init__(app)
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def _client_key(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        settings = get_settings()
        if not settings.rate_limit_enabled:
            return await call_next(request)
        if request.url.path == "/health":
            return await call_next(request)

        now = time.monotonic()
        window = settings.rate_limit_window_seconds
        limit = settings.rate_limit_requests
        key = self._client_key(request)
        bucket = self._events[key]

        while bucket and now - bucket[0] > window:
            bucket.popleft()

        if len(bucket) >= limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(window)},
            )

        bucket.append(now)
        response = await call_next(request)
        remaining = max(limit - len(bucket), 0)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window-Seconds"] = str(window)
        return response
