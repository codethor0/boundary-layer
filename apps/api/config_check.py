"""Production SaaS readiness checks for BoundaryLayer."""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field

from apps.api.config import Settings

READINESS_ENV_KEYS = (
    "BOUNDARY_LAYER_PROFILE",
    "BOUNDARY_LAYER_ENV",
    "BOUNDARY_LAYER_AUTH_ENABLED",
    "BOUNDARY_LAYER_AUTH_PROVIDER",
    "BOUNDARY_LAYER_SECRET_KEY",
    "BOUNDARY_LAYER_ALLOWED_ORIGINS",
    "BOUNDARY_LAYER_PUBLIC_BASE_URL",
    "BOUNDARY_LAYER_SECURE_COOKIES",
    "BOUNDARY_LAYER_TRUST_PROXY_HEADERS",
    "BOUNDARY_LAYER_METRICS_TOKEN",
    "BOUNDARY_LAYER_FILE_STORAGE_BACKEND",
    "BOUNDARY_LAYER_AUDIT_LOG_ENABLED",
    "BOUNDARY_LAYER_API_KEY",
    "BOUNDARY_LAYER_ALLOW_LOCAL_MANAGED_ENDPOINTS",
    "OIDC_ISSUER_URL",
    "OIDC_AUDIENCE",
    "OIDC_JWKS_URL",
    "OIDC_ALGORITHMS",
    "OIDC_REQUIRED_CLAIMS",
    "OIDC_TENANT_CLAIM",
    "OIDC_ROLES_CLAIM",
    "OIDC_SUBJECT_CLAIM",
    "OIDC_EMAIL_CLAIM",
    "OIDC_REQUIRED_ROLES",
    "OIDC_CLOCK_SKEW_SECONDS",
    "DATABASE_URL",
    "REDIS_URL",
    "DB_POOL_MIN_SIZE",
    "DB_POOL_MAX_SIZE",
    "DB_CONNECT_TIMEOUT_SECONDS",
    "DB_SSL_MODE",
    "REDIS_CONNECT_TIMEOUT_SECONDS",
    "REDIS_KEY_PREFIX",
    "OBJECT_STORAGE_BUCKET",
    "OBJECT_STORAGE_REGION",
    "OBJECT_STORAGE_PREFIX",
    "OBJECT_STORAGE_KMS_KEY_ID",
    "OBJECT_STORAGE_PRESIGNED_URL_TTL_SECONDS",
    "SECRET_MANAGER_PROVIDER",
    "SECRET_MANAGER_PROJECT_OR_PATH",
    "SECRET_ROTATION_REQUIRED",
    "POSTGRES_PASSWORD",
    "REDIS_PASSWORD",
    "SESSION_HMAC_SECRET",
)

PRODUCTION_SAAS_PROFILE = "production-saas"


@dataclass
class ReadinessReport:
    profile: str
    ready: bool
    mocked: bool = False
    issues: list[str] = field(default_factory=list)

    def format_text(self) -> str:
        lines = [
            "BoundaryLayer production SaaS readiness check",
            f"Target profile: {self.profile}",
            f"Status: {'READY' if self.ready else 'NOT READY'}",
        ]
        if self.mocked:
            lines.append("Mode: mocked example values only (not a live deployment)")
        if self.issues:
            lines.append("Issues:")
            for issue in self.issues:
                lines.append(f"  - {issue}")
        else:
            lines.append("All required production-saas settings are present.")
        return "\n".join(lines)


def _env_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _settings_kwargs(merged: dict[str, str]) -> dict[str, object]:
    return {
        "boundary_layer_profile": PRODUCTION_SAAS_PROFILE,
        "boundary_layer_env": merged.get("BOUNDARY_LAYER_ENV", "production"),
        "auth_enabled": _env_bool(merged.get("BOUNDARY_LAYER_AUTH_ENABLED", "true")),
        "auth_provider": merged.get("BOUNDARY_LAYER_AUTH_PROVIDER", ""),
        "database_url": merged.get("DATABASE_URL", ""),
        "redis_url": merged.get("REDIS_URL", ""),
        "secret_key": merged.get("BOUNDARY_LAYER_SECRET_KEY", ""),
        "allowed_origins": merged.get("BOUNDARY_LAYER_ALLOWED_ORIGINS", ""),
        "public_base_url": merged.get("BOUNDARY_LAYER_PUBLIC_BASE_URL", ""),
        "secure_cookies": _env_bool(merged.get("BOUNDARY_LAYER_SECURE_COOKIES")),
        "trust_proxy_headers": _env_bool(
            merged.get("BOUNDARY_LAYER_TRUST_PROXY_HEADERS")
        ),
        "metrics_token": merged.get("BOUNDARY_LAYER_METRICS_TOKEN", ""),
        "metrics_auth_required": True,
        "file_storage_backend": merged.get("BOUNDARY_LAYER_FILE_STORAGE_BACKEND", ""),
        "audit_log_enabled": _env_bool(merged.get("BOUNDARY_LAYER_AUDIT_LOG_ENABLED")),
        "oidc_issuer_url": merged.get("OIDC_ISSUER_URL", ""),
        "oidc_audience": merged.get("OIDC_AUDIENCE", ""),
        "oidc_jwks_url": merged.get("OIDC_JWKS_URL", ""),
        "oidc_algorithms": merged.get("OIDC_ALGORITHMS", "RS256"),
        "oidc_required_claims": merged.get("OIDC_REQUIRED_CLAIMS", ""),
        "oidc_tenant_claim": merged.get(
            "OIDC_TENANT_CLAIM", "https://boundarylayer.dev/tenant_id"
        ),
        "oidc_roles_claim": merged.get(
            "OIDC_ROLES_CLAIM", "https://boundarylayer.dev/roles"
        ),
        "oidc_subject_claim": merged.get("OIDC_SUBJECT_CLAIM", "sub"),
        "oidc_email_claim": merged.get("OIDC_EMAIL_CLAIM", "email"),
        "oidc_required_roles": merged.get("OIDC_REQUIRED_ROLES", ""),
        "oidc_clock_skew_seconds": int(merged.get("OIDC_CLOCK_SKEW_SECONDS", "60")),
        "api_key": merged.get("BOUNDARY_LAYER_API_KEY", ""),
        "postgres_password": merged.get("POSTGRES_PASSWORD", ""),
        "redis_password": merged.get("REDIS_PASSWORD", ""),
        "session_hmac_secret": merged.get("SESSION_HMAC_SECRET", ""),
        "db_pool_min_size": int(merged.get("DB_POOL_MIN_SIZE", "1")),
        "db_pool_max_size": int(merged.get("DB_POOL_MAX_SIZE", "10")),
        "db_connect_timeout_seconds": int(
            merged.get("DB_CONNECT_TIMEOUT_SECONDS", "5")
        ),
        "db_ssl_mode": merged.get("DB_SSL_MODE", ""),
        "redis_connect_timeout_seconds": int(
            merged.get("REDIS_CONNECT_TIMEOUT_SECONDS", "3")
        ),
        "redis_key_prefix": merged.get("REDIS_KEY_PREFIX", ""),
        "object_storage_bucket": merged.get("OBJECT_STORAGE_BUCKET", ""),
        "object_storage_region": merged.get("OBJECT_STORAGE_REGION", ""),
        "object_storage_prefix": merged.get("OBJECT_STORAGE_PREFIX", ""),
        "object_storage_kms_key_id": merged.get("OBJECT_STORAGE_KMS_KEY_ID", ""),
        "object_storage_presigned_url_ttl_seconds": int(
            merged.get("OBJECT_STORAGE_PRESIGNED_URL_TTL_SECONDS", "900")
        ),
        "secret_manager_provider": merged.get("SECRET_MANAGER_PROVIDER", ""),
        "secret_manager_project_or_path": merged.get(
            "SECRET_MANAGER_PROJECT_OR_PATH", ""
        ),
        "secret_rotation_required": _env_bool(
            merged.get("SECRET_ROTATION_REQUIRED", "false")
        ),
        "allow_local_managed_endpoints": _env_bool(
            merged.get("BOUNDARY_LAYER_ALLOW_LOCAL_MANAGED_ENDPOINTS")
        ),
    }


@contextmanager
def _isolated_env(merged: dict[str, str]):
    backup = {key: os.environ.get(key) for key in READINESS_ENV_KEYS}
    try:
        for key in READINESS_ENV_KEYS:
            os.environ.pop(key, None)
        os.environ.update({key: str(value) for key, value in merged.items()})
        yield
    finally:
        for key in READINESS_ENV_KEYS:
            os.environ.pop(key, None)
        for key, value in backup.items():
            if value is not None:
                os.environ[key] = value


def _settings_from_merged(merged: dict[str, str]) -> Settings:
    merged = dict(merged)
    merged["BOUNDARY_LAYER_PROFILE"] = PRODUCTION_SAAS_PROFILE
    with _isolated_env(merged):
        return Settings(_env_file=None)


def evaluate_production_saas_readiness(
    env: dict[str, str] | None = None,
    *,
    mocked: bool = False,
) -> ReadinessReport:
    merged = dict(os.environ if env is None else env)
    merged["BOUNDARY_LAYER_PROFILE"] = PRODUCTION_SAAS_PROFILE
    try:
        _settings_from_merged(merged)
    except ValueError as exc:
        issues = [part.strip() for part in str(exc).split(";") if part.strip()]
        return ReadinessReport(
            profile=PRODUCTION_SAAS_PROFILE,
            ready=False,
            mocked=mocked,
            issues=issues,
        )
    except Exception as exc:
        return ReadinessReport(
            profile=PRODUCTION_SAAS_PROFILE,
            ready=False,
            mocked=mocked,
            issues=[str(exc)],
        )

    return ReadinessReport(
        profile=PRODUCTION_SAAS_PROFILE,
        ready=True,
        mocked=mocked,
        issues=[],
    )


def main() -> int:
    report = evaluate_production_saas_readiness()
    print(report.format_text())
    return 0 if report.ready else 1


if __name__ == "__main__":
    sys.exit(main())
