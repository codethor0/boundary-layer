"""Phase 6 staging deploy and validation script tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_DOCS = [
    "docs/STAGING_DEPLOYMENT_RUNBOOK.md",
    "docs/STAGING_SECRETS_INVENTORY.md",
    "docs/GITHUB_ENVIRONMENT_SETUP.md",
    "docs/LIVE_STAGING_EVIDENCE_TEMPLATE.md",
    "docs/DR_ONCALL_RUNBOOK.md",
    "docs/LEGAL_COMPLIANCE_READINESS.md",
]


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


def test_phase6_required_docs_exist():
    for path in REQUIRED_DOCS:
        assert (ROOT / path).is_file(), f"missing {path}"


def test_deploy_staging_aws_dry_run_default():
    result = _run("deploy-staging-aws.sh")
    assert result.returncode == 0
    assert "DRY RUN ONLY" in result.stdout
    combined = result.stdout + result.stderr
    assert "super-secret-token" not in combined


def test_deploy_staging_aws_live_requires_aws_cli():
    result = _run(
        "deploy-staging-aws.sh",
        {
            "DEPLOY_STAGING": "true",
            "CONFIRM_STAGING_DEPLOY": "true",
            "AWS_REGION": "us-east-1",
            "AWS_ACCOUNT_ID": "123456789012",
            "ECS_CLUSTER_NAME": "boundary-layer-staging",
            "ECS_SERVICE_NAME": "boundary-layer-api",
            "STAGING_RELEASE_IMAGE": (
                "123456789012.dkr.ecr.us-east-1.amazonaws.com/boundary-layer-api:abc"
            ),
            "BOUNDARY_LAYER_PUBLIC_BASE_URL": "https://staging.example.com",
        },
    )
    combined = result.stdout + result.stderr
    assert "AWS CLI not installed" in combined or "Deploy placeholder" in combined


def test_live_staging_validation_package_missing_flag():
    result = _run("live-staging-validation-package.sh")
    assert result.returncode != 0
    assert "RUN_LIVE_STAGING_CHECKS" in result.stdout + result.stderr


def test_live_staging_validation_package_lists_missing_env():
    result = _run(
        "live-staging-validation-package.sh",
        {
            "RUN_LIVE_STAGING_CHECKS": "true",
            "STAGING_BASE_URL": "https://staging.example.com",
        },
    )
    assert result.returncode != 0
    assert "Missing required environment variables" in result.stdout
    assert "STAGING_TEST_ACCESS_TOKEN_TENANT_A" in result.stdout
    combined = result.stdout + result.stderr
    assert "eyJ" not in combined


def test_waf_readiness_structural_pass():
    result = _run("waf-readiness-check.sh")
    assert result.returncode == 0
    assert "STRUCTURAL WAF READINESS PASS" in result.stdout


def test_container_build_does_not_print_push_secrets():
    result = _run("container-build.sh")
    combined = result.stdout + result.stderr
    assert "super-secret" not in combined
    assert result.returncode == 0 or "SKIP docker build" in result.stdout


def test_staging_deploy_workflow_exists():
    workflow = ROOT / ".github/workflows/staging-deploy.yml"
    content = workflow.read_text(encoding="utf-8")
    assert "workflow_dispatch" in content
    assert "environment: staging" in content
    assert "DRY RUN ONLY" in content
