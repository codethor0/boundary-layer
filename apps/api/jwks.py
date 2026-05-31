"""JWKS client abstraction for production SaaS OIDC validation."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Protocol
from urllib.error import URLError
from urllib.request import Request, urlopen

import jwt

logger = logging.getLogger("boundary_layer.api.jwks")

SUPPORTED_JWT_ALGORITHMS = frozenset(
    {"RS256", "RS384", "RS512", "ES256", "ES384", "ES512", "PS256", "PS384", "PS512"}
)


class JwksError(Exception):
    """JWKS lookup or validation failure."""

    def __init__(self, message: str, code: str = "jwks_error"):
        super().__init__(message)
        self.message = message
        self.code = code


@dataclass
class _CachedKey:
    key: Any
    expires_at: float


class JwksClient(Protocol):
    cache_ttl_seconds: int

    def get_signing_key(self, kid: str | None) -> Any:
        """Return a signing key for the given key ID."""

    def refresh(self) -> None:
        """Refresh the JWKS key set."""


@dataclass
class InMemoryJwksClient:
    """Deterministic JWKS client for unit tests."""

    keys_by_kid: dict[str, Any]
    cache_ttl_seconds: int = 300
    _cache: dict[str, _CachedKey] = field(default_factory=dict)

    def get_signing_key(self, kid: str | None) -> Any:
        if not kid:
            raise JwksError("JWT header missing kid", "jwks_missing_kid")
        cached = self._cache.get(kid)
        now = time.monotonic()
        if cached and cached.expires_at > now:
            return cached.key
        if kid not in self.keys_by_kid:
            raise JwksError(f"Unknown key id: {kid}", "jwks_unknown_kid")
        key = self.keys_by_kid[kid]
        self._cache[kid] = _CachedKey(key=key, expires_at=now + self.cache_ttl_seconds)
        return key

    def refresh(self) -> None:
        self._cache.clear()


@dataclass
class HttpJwksClient:
    """HTTP JWKS client with bounded timeout and in-memory cache."""

    jwks_url: str
    timeout_seconds: float = 5.0
    cache_ttl_seconds: int = 300
    _keys_by_kid: dict[str, Any] = field(default_factory=dict)
    _cache: dict[str, _CachedKey] = field(default_factory=dict)
    _fetched_at: float = 0.0

    def get_signing_key(self, kid: str | None) -> Any:
        if not kid:
            raise JwksError("JWT header missing kid", "jwks_missing_kid")
        now = time.monotonic()
        cached = self._cache.get(kid)
        if cached and cached.expires_at > now:
            return cached.key
        if not self._keys_by_kid or (now - self._fetched_at) > self.cache_ttl_seconds:
            self.refresh()
        if kid not in self._keys_by_kid:
            raise JwksError(f"Unknown key id: {kid}", "jwks_unknown_kid")
        key = self._keys_by_kid[kid]
        self._cache[kid] = _CachedKey(key=key, expires_at=now + self.cache_ttl_seconds)
        return key

    def refresh(self) -> None:
        try:
            request = Request(
                self.jwks_url,
                headers={"Accept": "application/json"},
            )
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = response.read()
        except (URLError, OSError) as exc:
            logger.warning("JWKS fetch failed for configured URL")
            raise JwksError("JWKS fetch failed", "jwks_fetch_failed") from exc
        except TimeoutError as exc:
            logger.warning("JWKS fetch timed out")
            raise JwksError("JWKS fetch timed out", "jwks_fetch_timeout") from exc

        try:
            jwk_set = jwt.PyJWKSet.from_json(payload)
        except jwt.PyJWTError as exc:
            raise JwksError("Invalid JWKS payload", "jwks_invalid_payload") from exc

        self._keys_by_kid = {entry.key_id: entry.key for entry in jwk_set.keys}
        self._cache.clear()
        self._fetched_at = time.monotonic()


def validate_jwt_algorithm(algorithm: str | None, allowed: list[str]) -> None:
    if not algorithm:
        raise JwksError("JWT header missing alg", "jwt_missing_alg")
    normalized = algorithm.strip()
    if normalized.lower() == "none":
        raise JwksError("Algorithm none is not allowed", "jwt_alg_none")
    allowed_set = {item.upper() for item in allowed}
    if allowed_set and normalized.upper() not in allowed_set:
        raise JwksError(
            f"Unsupported JWT algorithm: {normalized}",
            "jwt_unsupported_alg",
        )
    hs_algorithms = {"HS256", "HS384", "HS512"}
    if (
        normalized.upper() not in SUPPORTED_JWT_ALGORITHMS
        and normalized.upper() not in hs_algorithms
    ):
        raise JwksError(
            f"Unsupported JWT algorithm: {normalized}",
            "jwt_unsupported_alg",
        )


def extract_token_kid(token: str) -> tuple[dict[str, Any], str | None]:
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise JwksError("Invalid JWT header", "jwt_invalid_header") from exc
    kid = header.get("kid")
    if isinstance(kid, str):
        kid = kid.strip() or None
    else:
        kid = None
    return header, kid


def build_jwks_client(
    *,
    jwks_url: str = "",
    timeout_seconds: float = 5.0,
    cache_ttl_seconds: int = 300,
    test_keys_by_kid: dict[str, Any] | None = None,
) -> JwksClient:
    if test_keys_by_kid is not None:
        return InMemoryJwksClient(
            keys_by_kid=test_keys_by_kid,
            cache_ttl_seconds=cache_ttl_seconds,
        )
    if not jwks_url.strip():
        raise JwksError("JWKS URL not configured", "jwks_misconfigured")
    return HttpJwksClient(
        jwks_url=jwks_url.strip(),
        timeout_seconds=timeout_seconds,
        cache_ttl_seconds=cache_ttl_seconds,
    )
