"""Staging deployment script behavior tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _run(
    script: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged = {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin"}
    if env:
        merged.update(env)
    return subprocess.run(
        ["bash", str(ROOT / "scripts" / script)],
        cwd=ROOT,
        env=merged,
        capture_output=True,
        text=True,
        check=False,
    )


def test_staging_smoke_structural_passes_with_defaults():
    result = _run("staging-smoke-structural.sh")
    assert result.returncode == 0
    assert "STRUCTURAL STAGING SMOKE PASS" in result.stdout


def test_staging_smoke_live_missing_flag():
    result = _run(
        "staging-smoke-live.sh",
        {
            "STAGING_BASE_URL": "https://staging.example.com",
            "STAGING_TEST_ACCESS_TOKEN_TENANT_A": "token-a-minimum-24-characters",
            "STAGING_METRICS_AUTH_TOKEN": "metrics-token-minimum-24-chars",
        },
    )
    assert result.returncode != 0
    assert "RUN_LIVE_STAGING_CHECKS" in result.stdout + result.stderr


def test_staging_deploy_dry_run_missing_env():
    result = _run("staging-deploy-dry-run.sh")
    assert result.returncode != 0
    assert "Missing required environment variables" in result.stdout


def test_staging_deploy_dry_run_with_mock_env():
    result = _run(
        "staging-deploy-dry-run.sh",
        {
            "BOUNDARY_LAYER_PROFILE": "production-saas",
            "BOUNDARY_LAYER_ENV": "staging",
            "DATABASE_URL": "postgresql://u:p@db.staging.example:5432/db?sslmode=require",
            "REDIS_URL": "rediss://:p@redis.staging.example:6379/0",
            "SECRET_MANAGER_PROVIDER": "aws",
            "OBJECT_STORAGE_BUCKET": "example-bucket",
            "BOUNDARY_LAYER_PUBLIC_BASE_URL": "https://staging.example.com",
            "STAGING_RELEASE_IMAGE": "ghcr.io/example/boundary-layer:staging",
        },
    )
    assert result.returncode == 0
    assert "DRY RUN ONLY" in result.stdout


def test_managed_services_live_check_requires_flag():
    result = _run("production-saas-managed-services-live-check.sh")
    assert result.returncode != 0
    assert "RUN_LIVE_STAGING_CHECKS" in result.stdout + result.stderr


def test_staging_release_gate_reports_skipped_live():
    content = (ROOT / "scripts" / "staging-release-gate.sh").read_text(encoding="utf-8")
    assert "LIVE STAGING CHECKS SKIPPED" in content
    assert "LIVE STAGING CHECKS PASS" in content
    assert "STRUCTURAL STAGING CHECKS PASS" in content


def test_infra_plan_requires_confirmation():
    result = _run("infra-plan-staging.sh")
    assert result.returncode != 0
    assert "CONFIRM_STAGING_PLAN" in result.stdout + result.stderr


def test_terraform_module_placeholders_exist():
    modules = [
        "network",
        "container_service",
        "postgres",
        "redis",
        "object_storage",
        "secret_manager",
        "waf",
        "observability",
    ]
    for module in modules:
        readme = ROOT / "infra" / "terraform" / "modules" / module / "README.md"
        assert readme.is_file()
