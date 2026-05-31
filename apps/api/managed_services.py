"""Managed service policy and live connectivity checks for Production SaaS staging."""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass, field
from typing import Literal
from urllib.parse import urlparse

import httpx

from apps.api.config import LOCAL_MANAGED_HOSTS, Settings, is_valid_https_url
from apps.api.config_check import (
    PRODUCTION_SAAS_PROFILE,
    _isolated_env,
    _settings_kwargs,
)
from apps.api.secrets import (
    SUPPORTED_SECRET_MANAGER_PROVIDERS,
    build_secret_provider,
    redact,
)
from apps.api.storage import SUPPORTED_OBJECT_STORAGE_BACKENDS, build_storage_backend

logger = logging.getLogger("boundary_layer.api.managed_services")

LIVE_CHECKS_ENV = "RUN_LIVE_STAGING_CHECKS"
DEFAULT_HEALTHCHECK_SECRET_NAME = "BOUNDARY_LAYER_HEALTHCHECK_SECRET"
STAGING_HEALTH_TENANT = "staging-health"
REDIS_HEALTH_KEY = "boundary_layer:tenant:staging-health:managed-service-check"
REDIS_HEALTH_TTL_SECONDS = 60
OBJECT_HEALTH_RELATIVE_KEY = "healthchecks/managed-service-check.txt"
CheckMode = Literal["structural", "live"]


@dataclass(frozen=True)
class LiveCheckResult:
    name: str
    passed: bool
    detail: str

    def format_line(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"{status} {self.name}: {self.detail}"


@dataclass
class ManagedServicesReport:
    profile: str
    ready: bool
    mode: CheckMode = "structural"
    structural: bool = False
    live: bool = False
    mocked: bool = False
    issues: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    live_results: list[LiveCheckResult] = field(default_factory=list)

    def format_text(self) -> str:
        if self.mode == "live" and self.ready:
            status = "LIVE CHECKS PASSED"
        elif self.structural and self.ready and not self.live:
            status = "STRUCTURALLY READY"
        elif self.ready:
            status = "READY"
        else:
            status = "NOT READY"
        lines = [
            "BoundaryLayer production SaaS managed services check",
            f"Target profile: {self.profile}",
            f"Mode: {self.mode}",
            f"Status: {status}",
        ]
        if self.mocked:
            lines.append(
                "Mode detail: mocked example values only (not live connectivity)"
            )
        if self.notes:
            lines.append("Notes:")
            for note in self.notes:
                lines.append(f"  - {note}")
        if self.live_results:
            lines.append("Live check results:")
            for result in self.live_results:
                lines.append(f"  - {result.format_line()}")
        if self.issues:
            lines.append("Issues:")
            for issue in self.issues:
                lines.append(f"  - {issue}")
        elif self.structural and self.mode == "structural":
            lines.append("Managed service settings are structurally valid.")
        elif self.mode == "live" and self.ready:
            lines.append("Managed services live connectivity checks passed.")
        return "\n".join(lines)


def is_live_checks_enabled(env: dict[str, str] | None = None) -> bool:
    source = os.environ if env is None else env
    return source.get(LIVE_CHECKS_ENV, "").strip().lower() in {"1", "true", "yes", "on"}


def healthcheck_secret_name(settings: Settings) -> str:
    configured = os.environ.get("BOUNDARY_LAYER_HEALTHCHECK_SECRET_NAME", "").strip()
    if configured:
        return configured
    return DEFAULT_HEALTHCHECK_SECRET_NAME


def redact_error_message(message: str) -> str:
    cleaned = message
    for marker in ("password=", "://", "Bearer ", "token="):
        if marker in cleaned and "@" in cleaned:
            cleaned = cleaned.split("@", 1)[-1]
            break
    if len(cleaned) > 160:
        cleaned = cleaned[:160] + "..."
    return cleaned


def check_database_url_policy(settings: Settings) -> list[str]:
    issues: list[str] = []
    url = settings.database_url.strip()
    if not url:
        issues.append("DATABASE_URL is required")
        return issues
    parsed = urlparse(url)
    host = (parsed.hostname or "").strip().lower()
    if (
        host
        and host in LOCAL_MANAGED_HOSTS
        and not settings.allow_local_managed_endpoints
    ):
        issues.append(
            "DATABASE_URL must not use localhost or container hostnames "
            "in production-saas"
        )
    sslmode = settings._database_ssl_mode()
    if sslmode != "require":
        issues.append("DATABASE_URL or DB_SSL_MODE must require SSL (sslmode=require)")
    if settings.db_pool_min_size < 1:
        issues.append("DB_POOL_MIN_SIZE must be at least 1")
    if settings.db_pool_max_size < settings.db_pool_min_size:
        issues.append(
            "DB_POOL_MAX_SIZE must be greater than or equal to DB_POOL_MIN_SIZE"
        )
    return issues


def check_redis_url_policy(settings: Settings) -> list[str]:
    issues: list[str] = []
    url = settings.redis_url.strip()
    if not url:
        issues.append("REDIS_URL is required")
        return issues
    parsed = urlparse(url)
    if parsed.scheme != "rediss":
        issues.append("REDIS_URL must use rediss:// in production-saas")
    host = (parsed.hostname or "").strip().lower()
    if (
        host
        and host in LOCAL_MANAGED_HOSTS
        and not settings.allow_local_managed_endpoints
    ):
        issues.append(
            "REDIS_URL must not use localhost or container hostnames "
            "in production-saas"
        )
    if not settings.redis_key_prefix.strip():
        issues.append("REDIS_KEY_PREFIX is required")
    return issues


def check_object_storage_policy(settings: Settings) -> list[str]:
    issues: list[str] = []
    backend = settings.file_storage_backend.strip().lower()
    if not backend:
        issues.append("BOUNDARY_LAYER_FILE_STORAGE_BACKEND is required")
        return issues
    if backend in {"local", "disk", "filesystem", "memory"}:
        issues.append("BOUNDARY_LAYER_FILE_STORAGE_BACKEND must not use local disk")
    elif backend not in SUPPORTED_OBJECT_STORAGE_BACKENDS:
        issues.append(
            "BOUNDARY_LAYER_FILE_STORAGE_BACKEND must be one of: "
            + ", ".join(sorted(SUPPORTED_OBJECT_STORAGE_BACKENDS))
        )
    else:
        if not settings.object_storage_bucket.strip():
            issues.append("OBJECT_STORAGE_BUCKET is required")
        if not settings.object_storage_region.strip() and backend != "r2":
            issues.append("OBJECT_STORAGE_REGION is required")
        if backend == "r2" and not settings.object_storage_endpoint.strip():
            issues.append("OBJECT_STORAGE_ENDPOINT is required for r2 backend")
        if settings.object_storage_presigned_url_ttl_seconds <= 0:
            issues.append("OBJECT_STORAGE_PRESIGNED_URL_TTL_SECONDS must be positive")
    return issues


def check_secret_manager_policy(settings: Settings) -> list[str]:
    issues: list[str] = []
    provider = settings.secret_manager_provider.strip().lower()
    if not provider:
        issues.append("SECRET_MANAGER_PROVIDER is required")
    elif provider not in SUPPORTED_SECRET_MANAGER_PROVIDERS:
        issues.append(
            "SECRET_MANAGER_PROVIDER must be one of: "
            + ", ".join(sorted(SUPPORTED_SECRET_MANAGER_PROVIDERS))
        )
    if not settings.secret_manager_project_or_path.strip():
        issues.append("SECRET_MANAGER_PROJECT_OR_PATH is required")
    if not settings.secret_rotation_required:
        issues.append("SECRET_ROTATION_REQUIRED must be true")
    if settings.secret_cache_ttl_seconds <= 0:
        issues.append("SECRET_CACHE_TTL_SECONDS is required")
    elif settings.secret_cache_ttl_seconds > 3600:
        issues.append("SECRET_CACHE_TTL_SECONDS must be at most 3600")
    if settings.is_production_saas and settings.allow_env_secret_provider:
        issues.append(
            "BOUNDARY_LAYER_ALLOW_ENV_SECRET_PROVIDER must not be enabled "
            "in production-saas"
        )
    audit_sink = settings.audit_sink_provider.strip()
    if settings.audit_immutable_required and audit_sink == "postgres":
        issues.append(
            "AUDIT_IMMUTABLE_REQUIRED requires a non-postgres immutable audit sink"
        )
    return issues


def run_structural_policy_checks(settings: Settings) -> list[str]:
    issues: list[str] = []
    issues.extend(check_database_url_policy(settings))
    issues.extend(check_redis_url_policy(settings))
    issues.extend(check_object_storage_policy(settings))
    issues.extend(check_secret_manager_policy(settings))
    public_base_url = settings.public_base_url.strip()
    if public_base_url and not is_valid_https_url(public_base_url):
        issues.append("BOUNDARY_LAYER_PUBLIC_BASE_URL must be a valid https URL")
    issuer = settings.oidc_issuer_url.strip()
    if issuer and not is_valid_https_url(settings.oidc_issuer_url):
        issues.append("OIDC_ISSUER_URL must be a valid https URL")
    jwks = settings.oidc_jwks_url.strip()
    if jwks and not is_valid_https_url(settings.oidc_jwks_url):
        issues.append("OIDC_JWKS_URL must be a valid https URL")
    return issues


def _settings_from_env(env: dict[str, str] | None) -> Settings:
    merged = dict(os.environ if env is None else env)
    merged["BOUNDARY_LAYER_PROFILE"] = PRODUCTION_SAAS_PROFILE
    with _isolated_env(merged):
        return Settings(_env_file=None, **_settings_kwargs(merged))


def check_database_live(settings: Settings) -> LiveCheckResult:
    sslmode = settings._database_ssl_mode()
    if sslmode not in {"require", "verify-ca", "verify-full"}:
        return LiveCheckResult(
            "postgresql",
            False,
            f"DATABASE_URL must require SSL (sslmode={sslmode or 'unset'})",
        )
    try:
        import psycopg2

        conn = psycopg2.connect(
            settings.database_url,
            connect_timeout=settings.db_connect_timeout_seconds,
        )
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
                cur.execute("SELECT current_database()")
                db_name = str(cur.fetchone()[0])
            sslmode = settings._database_ssl_mode()
            detail = f"SELECT 1 ok; database={db_name}; sslmode={sslmode}"
            return LiveCheckResult("postgresql", True, detail)
        finally:
            conn.close()
    except Exception as exc:
        return LiveCheckResult(
            "postgresql",
            False,
            redact_error_message(str(exc)),
        )


def check_redis_live(settings: Settings) -> LiveCheckResult:
    if not settings.redis_url.strip().startswith("rediss://"):
        return LiveCheckResult(
            "redis",
            False,
            "REDIS_URL must use rediss:// for live production-saas check",
        )
    try:
        import redis

        client = redis.from_url(
            settings.redis_url,
            socket_connect_timeout=settings.redis_connect_timeout_seconds,
        )
        try:
            client.ping()
            client.set(REDIS_HEALTH_KEY, "ok", ex=REDIS_HEALTH_TTL_SECONDS)
            value = client.get(REDIS_HEALTH_KEY)
            if value is None:
                raise RuntimeError("health-check key missing after SET")
            ttl = client.ttl(REDIS_HEALTH_KEY)
            client.delete(REDIS_HEALTH_KEY)
            detail = f"PING ok; key={REDIS_HEALTH_KEY}; ttl={ttl}"
            return LiveCheckResult("redis", True, detail)
        finally:
            client.close()
    except Exception as exc:
        return LiveCheckResult("redis", False, redact_error_message(str(exc)))


def check_object_storage_live(settings: Settings) -> LiveCheckResult:
    payload = b"boundary-layer-managed-service-healthcheck"
    try:
        backend = build_storage_backend(settings)
        backend.put_object(
            OBJECT_HEALTH_RELATIVE_KEY,
            payload,
            "text/plain",
            tenant_id=STAGING_HEALTH_TENANT,
        )
        metadata = backend.get_object_metadata(
            OBJECT_HEALTH_RELATIVE_KEY,
            tenant_id=STAGING_HEALTH_TENANT,
        )
        backend.delete_object(
            OBJECT_HEALTH_RELATIVE_KEY,
            tenant_id=STAGING_HEALTH_TENANT,
        )
        if not metadata.key.startswith("tenants/staging-health/"):
            return LiveCheckResult(
                "object_storage",
                False,
                "object key is not tenant-scoped under tenants/staging-health/",
            )
        return LiveCheckResult(
            "object_storage",
            True,
            f"write/read/delete ok; key={metadata.key}",
        )
    except Exception as exc:
        message = str(exc)
        if "sdk_not_installed" in message.lower():
            return LiveCheckResult(
                "object_storage",
                False,
                "Provider SDK not installed for live object storage check",
            )
        return LiveCheckResult(
            "object_storage",
            False,
            redact_error_message(message),
        )


def check_secret_manager_live(settings: Settings) -> LiveCheckResult:
    secret_name = healthcheck_secret_name(settings)
    try:
        provider = build_secret_provider(settings)
        value = provider.get_secret(secret_name)
        logger.info(
            "Health-check secret present via %s (value=%s)",
            settings.secret_manager_provider,
            redact(value),
        )
        return LiveCheckResult(
            "secret_manager",
            True,
            f"secret present for {secret_name} (value redacted)",
        )
    except Exception as exc:
        message = str(exc)
        code = getattr(exc, "code", "")
        if code == "secret_not_found" or "Missing secret" in message:
            return LiveCheckResult(
                "secret_manager",
                False,
                f"health-check secret missing: {secret_name}",
            )
        if "sdk_not_installed" in message.lower():
            return LiveCheckResult(
                "secret_manager",
                False,
                "Provider SDK not installed for live secret manager check",
            )
        return LiveCheckResult(
            "secret_manager",
            False,
            redact_error_message(message),
        )


def check_jwks_live(settings: Settings) -> LiveCheckResult:
    issuer = settings.oidc_issuer_url.strip()
    jwks_url = settings.oidc_jwks_url.strip()
    if not is_valid_https_url(issuer):
        return LiveCheckResult("jwks", False, "OIDC_ISSUER_URL must be https")
    if not is_valid_https_url(jwks_url):
        return LiveCheckResult("jwks", False, "OIDC_JWKS_URL must be https")
    timeout = min(settings.redis_connect_timeout_seconds, 10)
    try:
        response = httpx.get(jwks_url, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
        keys = payload.get("keys") or []
        if not keys:
            return LiveCheckResult("jwks", False, "JWKS response contains no keys")
        allowed = {
            alg.strip()
            for alg in settings.oidc_algorithms.split(",")
            if alg.strip() and alg.strip().lower() != "none"
        }
        key_algs = {str(key.get("alg", "")).strip() for key in keys if key.get("alg")}
        if allowed and key_algs and not (key_algs & allowed):
            return LiveCheckResult(
                "jwks",
                False,
                "JWKS signing algorithms do not match OIDC_ALGORITHMS",
            )
        return LiveCheckResult(
            "jwks",
            True,
            f"issuer=https ok; signing_keys={len(keys)}; algorithms_ok=true",
        )
    except Exception as exc:
        return LiveCheckResult("jwks", False, redact_error_message(str(exc)))


def run_live_connectivity_checks(settings: Settings) -> list[LiveCheckResult]:
    return [
        check_database_live(settings),
        check_redis_live(settings),
        check_object_storage_live(settings),
        check_secret_manager_live(settings),
        check_jwks_live(settings),
    ]


def evaluate_managed_services_readiness(
    env: dict[str, str] | None = None,
    *,
    mocked: bool = False,
    live: bool | None = None,
    mode: CheckMode | None = None,
) -> ManagedServicesReport:
    if env is None:
        merged: dict[str, str] = {"BOUNDARY_LAYER_ENV": "staging"}
    else:
        merged = dict(env)
    merged["BOUNDARY_LAYER_PROFILE"] = PRODUCTION_SAAS_PROFILE
    live_enabled = live if live is not None else is_live_checks_enabled(merged)
    selected_mode: CheckMode = mode or ("live" if live_enabled else "structural")

    if selected_mode == "live" and not live_enabled:
        return ManagedServicesReport(
            profile=PRODUCTION_SAAS_PROFILE,
            ready=False,
            mode="live",
            live=True,
            mocked=mocked,
            issues=["Live mode refused: set RUN_LIVE_STAGING_CHECKS=true explicitly"],
        )

    try:
        settings = _settings_from_env(merged)
    except ValueError as exc:
        issues = [part.strip() for part in str(exc).split(";") if part.strip()]
        return ManagedServicesReport(
            profile=PRODUCTION_SAAS_PROFILE,
            ready=False,
            mode=selected_mode,
            mocked=mocked,
            live=live_enabled,
            issues=issues,
        )
    except Exception as exc:
        return ManagedServicesReport(
            profile=PRODUCTION_SAAS_PROFILE,
            ready=False,
            mode=selected_mode,
            mocked=mocked,
            live=live_enabled,
            issues=[str(exc)],
        )

    structural_issues = run_structural_policy_checks(settings)
    if structural_issues:
        return ManagedServicesReport(
            profile=PRODUCTION_SAAS_PROFILE,
            ready=False,
            mode="structural",
            mocked=mocked,
            live=live_enabled,
            issues=structural_issues,
        )

    try:
        build_storage_backend(settings)
        build_secret_provider(settings)
    except Exception as exc:
        return ManagedServicesReport(
            profile=PRODUCTION_SAAS_PROFILE,
            ready=False,
            mode=selected_mode,
            mocked=mocked,
            live=live_enabled,
            issues=[str(exc)],
        )

    if selected_mode == "structural":
        return ManagedServicesReport(
            profile=PRODUCTION_SAAS_PROFILE,
            ready=True,
            mode="structural",
            structural=True,
            mocked=mocked,
            live=False,
            notes=[
                "Live connectivity checks skipped " "(set RUN_LIVE_STAGING_CHECKS=true)"
            ],
        )

    live_results = run_live_connectivity_checks(settings)
    failed = [result for result in live_results if not result.passed]
    if failed:
        return ManagedServicesReport(
            profile=PRODUCTION_SAAS_PROFILE,
            ready=False,
            mode="live",
            structural=True,
            live=True,
            mocked=mocked,
            live_results=live_results,
            issues=[result.format_line() for result in failed],
            notes=["Structural settings passed; one or more live checks failed"],
        )

    return ManagedServicesReport(
        profile=PRODUCTION_SAAS_PROFILE,
        ready=True,
        mode="live",
        structural=True,
        live=True,
        mocked=mocked,
        live_results=live_results,
        notes=["Structural settings and live connectivity checks passed"],
    )


def main() -> int:
    mode: CheckMode = "live" if is_live_checks_enabled() else "structural"
    report = evaluate_managed_services_readiness(mode=mode)
    print(report.format_text())
    return 0 if report.ready else 1


if __name__ == "__main__":
    sys.exit(main())
