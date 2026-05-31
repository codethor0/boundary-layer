"""Managed service policy and connectivity checks for Production SaaS staging."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from urllib.parse import urlparse

from apps.api.config import LOCAL_MANAGED_HOSTS, Settings, is_valid_https_url
from apps.api.config_check import (
    PRODUCTION_SAAS_PROFILE,
    _isolated_env,
    _settings_kwargs,
)
from apps.api.secrets import SUPPORTED_SECRET_MANAGER_PROVIDERS, build_secret_provider
from apps.api.storage import SUPPORTED_OBJECT_STORAGE_BACKENDS, build_storage_backend

LIVE_CHECKS_ENV = "RUN_LIVE_STAGING_CHECKS"
HEALTHCHECK_SECRET_NAME = "BOUNDARY_LAYER_HEALTHCHECK_SECRET"


@dataclass
class ManagedServicesReport:
    profile: str
    ready: bool
    structural: bool = False
    live: bool = False
    mocked: bool = False
    issues: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def format_text(self) -> str:
        if self.structural and self.ready:
            status = "STRUCTURALLY READY"
        elif self.ready:
            status = "READY"
        else:
            status = "NOT READY"
        lines = [
            "BoundaryLayer production SaaS managed services check",
            f"Target profile: {self.profile}",
            f"Status: {status}",
        ]
        if self.mocked:
            lines.append("Mode: mocked example values only (not live connectivity)")
        if self.live:
            lines.append("Mode: live connectivity checks enabled")
        if self.notes:
            lines.append("Notes:")
            for note in self.notes:
                lines.append(f"  - {note}")
        if self.issues:
            lines.append("Issues:")
            for issue in self.issues:
                lines.append(f"  - {issue}")
        elif self.structural:
            lines.append("Managed service settings are structurally valid.")
        elif self.ready:
            lines.append("Managed services connectivity checks passed.")
        return "\n".join(lines)


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


def _settings_from_env(env: dict[str, str] | None) -> Settings:
    merged = dict(os.environ if env is None else env)
    merged["BOUNDARY_LAYER_PROFILE"] = PRODUCTION_SAAS_PROFILE
    with _isolated_env(merged):
        return Settings(_env_file=None, **_settings_kwargs(merged))


def evaluate_managed_services_readiness(
    env: dict[str, str] | None = None,
    *,
    mocked: bool = False,
    live: bool | None = None,
) -> ManagedServicesReport:
    if env is None:
        merged: dict[str, str] = {"BOUNDARY_LAYER_ENV": "staging"}
    else:
        merged = dict(env)
    merged["BOUNDARY_LAYER_PROFILE"] = PRODUCTION_SAAS_PROFILE
    live_enabled = (
        live
        if live is not None
        else os.environ.get(LIVE_CHECKS_ENV, "").strip().lower()
        in {"1", "true", "yes", "on"}
    )

    try:
        settings = _settings_from_env(merged)
    except ValueError as exc:
        issues = [part.strip() for part in str(exc).split(";") if part.strip()]
        return ManagedServicesReport(
            profile=PRODUCTION_SAAS_PROFILE,
            ready=False,
            mocked=mocked,
            live=live_enabled,
            issues=issues,
        )
    except Exception as exc:
        return ManagedServicesReport(
            profile=PRODUCTION_SAAS_PROFILE,
            ready=False,
            mocked=mocked,
            live=live_enabled,
            issues=[str(exc)],
        )

    issues: list[str] = []
    issues.extend(check_database_url_policy(settings))
    issues.extend(check_redis_url_policy(settings))
    issues.extend(check_object_storage_policy(settings))
    issues.extend(check_secret_manager_policy(settings))

    public_base_url = settings.public_base_url.strip()
    if public_base_url and not is_valid_https_url(public_base_url):
        issues.append("BOUNDARY_LAYER_PUBLIC_BASE_URL must be a valid https URL")

    notes: list[str] = []
    if issues:
        return ManagedServicesReport(
            profile=PRODUCTION_SAAS_PROFILE,
            ready=False,
            mocked=mocked,
            live=live_enabled,
            issues=issues,
            notes=notes,
        )

    try:
        build_storage_backend(settings)
        build_secret_provider(settings)
    except Exception as exc:
        return ManagedServicesReport(
            profile=PRODUCTION_SAAS_PROFILE,
            ready=False,
            mocked=mocked,
            live=live_enabled,
            issues=[str(exc)],
        )

    if not live_enabled:
        notes.append(
            "Live connectivity checks skipped (set RUN_LIVE_STAGING_CHECKS=true)"
        )
        return ManagedServicesReport(
            profile=PRODUCTION_SAAS_PROFILE,
            ready=True,
            structural=True,
            mocked=mocked,
            live=False,
            notes=notes,
        )

    live_issues = _run_live_checks(settings)
    if live_issues:
        return ManagedServicesReport(
            profile=PRODUCTION_SAAS_PROFILE,
            ready=False,
            structural=True,
            mocked=mocked,
            live=True,
            issues=live_issues,
            notes=["Structural settings passed; live connectivity failed"],
        )

    return ManagedServicesReport(
        profile=PRODUCTION_SAAS_PROFILE,
        ready=True,
        structural=True,
        live=True,
        mocked=mocked,
        notes=["Structural settings and live connectivity checks passed"],
    )


def _run_live_checks(settings: Settings) -> list[str]:
    issues: list[str] = []

    try:
        import psycopg2

        conn = psycopg2.connect(
            settings.database_url,
            connect_timeout=settings.db_connect_timeout_seconds,
        )
        conn.close()
    except Exception as exc:
        issues.append(f"DATABASE_URL live connection failed: {exc}")

    try:
        import redis

        client = redis.from_url(
            settings.redis_url,
            socket_connect_timeout=settings.redis_connect_timeout_seconds,
        )
        client.ping()
        client.close()
    except Exception as exc:
        issues.append(f"REDIS_URL live ping failed: {exc}")

    try:
        backend = build_storage_backend(settings)
        backend.get_object_metadata(
            "healthcheck.txt",
            tenant_id="healthcheck",
        )
    except Exception as exc:
        message = str(exc)
        if "not found" in message.lower() or "404" in message:
            pass
        elif "sdk_not_installed" in message.lower():
            issues.append("Object storage adapter SDK not installed for live check")
        else:
            issues.append(f"Object storage live metadata check failed: {exc}")

    if not settings.allow_env_secret_provider:
        try:
            provider = build_secret_provider(settings)
            provider.get_secret(HEALTHCHECK_SECRET_NAME)
        except Exception as exc:
            message = str(exc)
            if "sdk_not_installed" in message.lower():
                issues.append("Secret manager adapter SDK not installed for live check")
            elif "secret_not_found" in message.lower() or "Missing secret" in message:
                pass
            else:
                issues.append(f"Secret manager live lookup failed: {exc}")

    return issues


def main() -> int:
    report = evaluate_managed_services_readiness()
    print(report.format_text())
    return 0 if report.ready else 1


if __name__ == "__main__":
    sys.exit(main())
