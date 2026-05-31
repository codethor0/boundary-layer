"""Production SaaS staging readiness checks for BoundaryLayer."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

from apps.api.config import Settings
from apps.api.config_check import PRODUCTION_SAAS_PROFILE, _isolated_env


def _settings_from_merged(merged: dict[str, str]) -> Settings:
    merged = dict(merged)
    merged["BOUNDARY_LAYER_PROFILE"] = PRODUCTION_SAAS_PROFILE
    merged["BOUNDARY_LAYER_ENV"] = merged.get("BOUNDARY_LAYER_ENV", "staging")
    with _isolated_env(merged):
        return Settings(_env_file=None)


@dataclass
class StagingReadinessReport:
    profile: str
    environment: str
    ready: bool
    mocked: bool = False
    issues: list[str] = field(default_factory=list)

    def format_text(self) -> str:
        lines = [
            "BoundaryLayer production SaaS staging readiness check",
            f"Target profile: {self.profile}",
            f"Target environment: {self.environment}",
            f"Status: {'READY' if self.ready else 'NOT READY'}",
        ]
        if self.mocked:
            lines.append("Mode: mocked example values only (not a live deployment)")
        if self.issues:
            lines.append("Issues:")
            for issue in self.issues:
                lines.append(f"  - {issue}")
        else:
            lines.append("All required staging settings are structurally valid.")
        return "\n".join(lines)


def evaluate_staging_readiness(
    env: dict[str, str] | None = None,
    *,
    mocked: bool = False,
) -> StagingReadinessReport:
    if env is None:
        merged: dict[str, str] = {"BOUNDARY_LAYER_ENV": "staging"}
    else:
        merged = dict(env)
    merged["BOUNDARY_LAYER_PROFILE"] = PRODUCTION_SAAS_PROFILE
    merged["BOUNDARY_LAYER_ENV"] = merged.get("BOUNDARY_LAYER_ENV", "staging")
    try:
        _settings_from_merged(merged)
    except ValueError as exc:
        issues = [part.strip() for part in str(exc).split(";") if part.strip()]
        return StagingReadinessReport(
            profile=PRODUCTION_SAAS_PROFILE,
            environment=merged["BOUNDARY_LAYER_ENV"],
            ready=False,
            mocked=mocked,
            issues=issues,
        )
    except Exception as exc:
        return StagingReadinessReport(
            profile=PRODUCTION_SAAS_PROFILE,
            environment=merged["BOUNDARY_LAYER_ENV"],
            ready=False,
            mocked=mocked,
            issues=[str(exc)],
        )

    return StagingReadinessReport(
        profile=PRODUCTION_SAAS_PROFILE,
        environment=merged["BOUNDARY_LAYER_ENV"],
        ready=True,
        mocked=mocked,
        issues=[],
    )


def main() -> int:
    report = evaluate_staging_readiness()
    print(report.format_text())
    return 0 if report.ready else 1


if __name__ == "__main__":
    sys.exit(main())
