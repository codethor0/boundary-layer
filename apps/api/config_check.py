"""Production SaaS readiness checks for BoundaryLayer."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

from apps.api.config import Settings

PRODUCTION_SAAS_PROFILE = "production-saas"


@dataclass
class ReadinessReport:
    profile: str
    ready: bool
    issues: list[str] = field(default_factory=list)

    def format_text(self) -> str:
        lines = [
            "BoundaryLayer production SaaS readiness check",
            f"Target profile: {self.profile}",
            f"Status: {'READY' if self.ready else 'NOT READY'}",
        ]
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


def _settings_from_merged(merged: dict[str, str]) -> Settings:
    return Settings.model_validate(
        {
            "boundary_layer_profile": PRODUCTION_SAAS_PROFILE,
            "boundary_layer_env": merged.get("BOUNDARY_LAYER_ENV", "production"),
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
            "file_storage_backend": merged.get(
                "BOUNDARY_LAYER_FILE_STORAGE_BACKEND", ""
            ),
            "audit_log_enabled": _env_bool(
                merged.get("BOUNDARY_LAYER_AUDIT_LOG_ENABLED")
            ),
            "api_key": merged.get("BOUNDARY_LAYER_API_KEY", ""),
            "postgres_password": merged.get("POSTGRES_PASSWORD", ""),
            "redis_password": merged.get("REDIS_PASSWORD", ""),
            "session_hmac_secret": merged.get("SESSION_HMAC_SECRET", ""),
        }
    )


def evaluate_production_saas_readiness(
    env: dict[str, str] | None = None,
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
            issues=issues,
        )
    except Exception as exc:
        return ReadinessReport(
            profile=PRODUCTION_SAAS_PROFILE,
            ready=False,
            issues=[str(exc)],
        )

    return ReadinessReport(
        profile=PRODUCTION_SAAS_PROFILE,
        ready=True,
        issues=[],
    )


def main() -> int:
    report = evaluate_production_saas_readiness()
    print(report.format_text())
    return 0 if report.ready else 1


if __name__ == "__main__":
    sys.exit(main())
