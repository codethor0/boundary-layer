"""Production SaaS evidence gate tests."""

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


def test_evidence_docs_exist():
    paths = [
        "docs/PRODUCTION_10_10_EVIDENCE_MATRIX.md",
        "docs/PRODUCTION_READINESS_REVIEW.md",
        "docs/LEGAL_COMPLIANCE_READINESS.md",
    ]
    for path in paths:
        assert (ROOT / path).is_file()


def test_check_live_staging_prereqs_missing():
    result = _run("check-live-staging-prereqs.sh")
    assert result.returncode != 0
    assert "LIVE STAGING PREREQS MISSING" in result.stdout + result.stderr
    assert "RUN_LIVE_STAGING_CHECKS" in result.stdout + result.stderr


def test_check_live_staging_prereqs_no_secret_values():
    result = _run("check-live-staging-prereqs.sh", {"RUN_LIVE_STAGING_CHECKS": "true"})
    combined = result.stdout + result.stderr
    assert "eyJ" not in combined
    assert "postgresql://" not in combined


def test_evidence_runner_missing_prereqs():
    result = _run("production-saas-evidence-runner.sh")
    assert result.returncode != 0
    assert "LIVE STAGING EVIDENCE CANNOT RUN" in result.stdout + result.stderr
    assert "6/10" in result.stdout + result.stderr


def test_waf_live_check_skipped_without_config():
    result = _run("waf-live-check.sh")
    assert result.returncode == 0
    assert "SKIPPED" in result.stdout


def test_audit_sink_live_check_skipped():
    result = _run("audit-sink-live-check.sh")
    assert result.returncode == 0
    assert "SKIPPED" in result.stdout


def test_dr_restore_live_check_requires_confirmation():
    result = _run("dr-restore-live-check.sh")
    assert result.returncode == 0
    assert "DR LIVE CHECK SKIPPED" in result.stdout


def test_score_cap_language_in_readiness_doc():
    content = (ROOT / "docs/PRODUCTION_SAAS_READINESS.md").read_text(encoding="utf-8")
    assert "capped at 6/10" in content
    assert "Dry-runs" in content or "dry-runs" in content


def test_dependency_report_lists_advisory_ids():
    content = (ROOT / "DEPENDENCY_REPORT.md").read_text(encoding="utf-8")
    assert "PYSEC-2026-120" in content
    assert "2.12.0" in content


def test_production_saas_live_validation_workflow_exists():
    path = ROOT / ".github/workflows/production-saas-live-validation.yml"
    content = path.read_text(encoding="utf-8")
    assert "workflow_dispatch" in content
    assert "production-saas-evidence-runner" in content
