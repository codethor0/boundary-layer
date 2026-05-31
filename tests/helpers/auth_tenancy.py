"""Shared helpers for auth and tenancy tests."""

from __future__ import annotations

import time

import jwt
from starlette.requests import Request


def make_request(
    authorization: str | None = None,
    path: str = "/labs",
) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if authorization:
        headers.append((b"authorization", authorization.encode()))
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "path": path,
        "headers": headers,
        "query_string": b"",
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "scheme": "http",
    }
    return Request(scope)


def make_oidc_test_token(
    secret_key: str,
    *,
    subject: str = "user-123",
    tenant_id: str = "tenant-a",
    roles: list[str] | None = None,
    issuer: str = "https://issuer.example.com",
    audience: str = "boundary-layer-api",
    expired: bool = False,
    include_tenant: bool = True,
    include_roles: bool = True,
) -> str:
    now = int(time.time())
    claims = {
        "sub": subject,
        "iss": issuer,
        "aud": audience,
        "exp": now - 60 if expired else now + 3600,
    }
    if include_tenant:
        claims["https://boundarylayer.dev/tenant_id"] = tenant_id
    if include_roles:
        claims["https://boundarylayer.dev/roles"] = roles or ["lab_runner"]
    return jwt.encode(claims, secret_key, algorithm="HS256")


def production_saas_settings(**overrides: str):
    from apps.api import config

    env = production_saas_env()
    env.update({key: str(value) for key, value in overrides.items()})
    return config.Settings.model_validate(
        {
            "boundary_layer_profile": env["BOUNDARY_LAYER_PROFILE"],
            "boundary_layer_env": env["BOUNDARY_LAYER_ENV"],
            "auth_enabled": True,
            "auth_provider": env["BOUNDARY_LAYER_AUTH_PROVIDER"],
            "database_url": env["DATABASE_URL"],
            "redis_url": env["REDIS_URL"],
            "secret_key": env["BOUNDARY_LAYER_SECRET_KEY"],
            "allowed_origins": env["BOUNDARY_LAYER_ALLOWED_ORIGINS"],
            "public_base_url": env["BOUNDARY_LAYER_PUBLIC_BASE_URL"],
            "secure_cookies": True,
            "trust_proxy_headers": True,
            "metrics_token": env["BOUNDARY_LAYER_METRICS_TOKEN"],
            "metrics_auth_required": True,
            "file_storage_backend": env["BOUNDARY_LAYER_FILE_STORAGE_BACKEND"],
            "audit_log_enabled": True,
            "oidc_issuer_url": env["OIDC_ISSUER_URL"],
            "oidc_audience": env["OIDC_AUDIENCE"],
            "oidc_jwks_url": env["OIDC_JWKS_URL"],
            "oidc_algorithms": env["OIDC_ALGORITHMS"],
            "api_key": env["BOUNDARY_LAYER_API_KEY"],
            "postgres_password": env["POSTGRES_PASSWORD"],
            "redis_password": env["REDIS_PASSWORD"],
            "session_hmac_secret": env["SESSION_HMAC_SECRET"],
        }
    )


def production_saas_env() -> dict[str, str]:
    secret = "production-saas-phase1-secret-key-minimum-32"
    return {
        "BOUNDARY_LAYER_PROFILE": "production-saas",
        "BOUNDARY_LAYER_ENV": "production",
        "BOUNDARY_LAYER_AUTH_ENABLED": "true",
        "BOUNDARY_LAYER_AUTH_PROVIDER": "oidc-test",
        "OIDC_ISSUER_URL": "https://issuer.example.com",
        "OIDC_AUDIENCE": "boundary-layer-api",
        "OIDC_JWKS_URL": "https://issuer.example.com/.well-known/jwks.json",
        "OIDC_ALGORITHMS": "HS256",
        "DATABASE_URL": "postgresql://boundary_layer:test@postgres.example:5432/boundary_layer",
        "REDIS_URL": "rediss://:test@redis.example:6379/0",
        "BOUNDARY_LAYER_SECRET_KEY": secret,
        "BOUNDARY_LAYER_ALLOWED_ORIGINS": "https://app.example.com",
        "BOUNDARY_LAYER_PUBLIC_BASE_URL": "https://app.example.com",
        "BOUNDARY_LAYER_SECURE_COOKIES": "true",
        "BOUNDARY_LAYER_TRUST_PROXY_HEADERS": "true",
        "BOUNDARY_LAYER_METRICS_TOKEN": "production-metrics-token-minimum-24",
        "BOUNDARY_LAYER_FILE_STORAGE_BACKEND": "s3",
        "BOUNDARY_LAYER_AUDIT_LOG_ENABLED": "true",
        "BOUNDARY_LAYER_API_KEY": "production-api-key-minimum-24-chars",
        "POSTGRES_PASSWORD": "production-postgres-password",
        "REDIS_PASSWORD": "production-redis-password-16",
        "SESSION_HMAC_SECRET": "production-session-hmac-secret",
    }
