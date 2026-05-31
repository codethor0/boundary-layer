"""Live managed-service check gating tests."""

from unittest.mock import patch

from apps.api.managed_services import (
    LIVE_CHECKS_ENV,
    REDIS_HEALTH_KEY,
    REDIS_HEALTH_TTL_SECONDS,
    LiveCheckResult,
    evaluate_managed_services_readiness,
    is_live_checks_enabled,
    run_live_connectivity_checks,
)
from tests.helpers.auth_tenancy import production_saas_env, production_saas_settings


def _managed_env(**overrides: str) -> dict[str, str]:
    env = production_saas_env()
    env["BOUNDARY_LAYER_ENV"] = "staging"
    env["BOUNDARY_LAYER_AUTH_PROVIDER"] = "oidc"
    env["OIDC_ALGORITHMS"] = "RS256"
    env.update(overrides)
    return env


def test_is_live_checks_enabled_false_by_default(monkeypatch):
    monkeypatch.delenv(LIVE_CHECKS_ENV, raising=False)
    assert is_live_checks_enabled() is False


def test_live_mode_refused_without_flag():
    report = evaluate_managed_services_readiness(
        _managed_env(),
        mode="live",
        live=False,
    )
    assert report.ready is False
    assert any("RUN_LIVE_STAGING_CHECKS" in issue for issue in report.issues)


def test_structural_mode_makes_no_live_calls():
    with patch("apps.api.managed_services.run_live_connectivity_checks") as mocked:
        report = evaluate_managed_services_readiness(_managed_env(), mocked=True)
        mocked.assert_not_called()
    assert report.mode == "structural"
    assert report.ready is True


def test_live_mode_runs_checks_when_enabled(monkeypatch):
    monkeypatch.setenv(LIVE_CHECKS_ENV, "true")
    fake_results = [LiveCheckResult("postgresql", True, "ok")]
    with patch(
        "apps.api.managed_services.run_live_connectivity_checks",
        return_value=fake_results,
    ):
        report = evaluate_managed_services_readiness(
            _managed_env(),
            mode="live",
            live=True,
        )
    assert report.mode == "live"
    assert report.ready is True
    assert report.live_results[0].passed is True


def test_live_results_redact_secrets_in_output():
    results = [
        LiveCheckResult(
            "secret_manager",
            True,
            "secret present for HEALTHCHECK (value redacted)",
        )
    ]
    text = results[0].format_line()
    assert "redacted" in text
    assert "super-secret" not in text


def test_redis_health_key_and_ttl_constants():
    expected = "boundary_layer:tenant:staging-health:managed-service-check"
    assert REDIS_HEALTH_KEY == expected
    assert REDIS_HEALTH_TTL_SECONDS == 60


def test_live_check_failure_classification(monkeypatch):
    monkeypatch.setenv(LIVE_CHECKS_ENV, "true")
    fake_results = [
        LiveCheckResult("postgresql", False, "connection refused"),
        LiveCheckResult("redis", True, "PING ok"),
    ]
    with patch(
        "apps.api.managed_services.run_live_connectivity_checks",
        return_value=fake_results,
    ):
        report = evaluate_managed_services_readiness(
            _managed_env(),
            mode="live",
            live=True,
        )
    assert report.ready is False
    assert any("FAIL postgresql" in issue for issue in report.issues)


def test_run_live_connectivity_checks_invokes_all_checks():
    settings = production_saas_settings()
    ok = LiveCheckResult("postgresql", True, "ok")
    with (
        patch("apps.api.managed_services.check_database_live", return_value=ok),
        patch(
            "apps.api.managed_services.check_redis_live",
            return_value=LiveCheckResult("redis", True, "ok"),
        ),
        patch(
            "apps.api.managed_services.check_object_storage_live",
            return_value=LiveCheckResult("object_storage", True, "ok"),
        ),
        patch(
            "apps.api.managed_services.check_secret_manager_live",
            return_value=LiveCheckResult("secret_manager", True, "ok"),
        ),
        patch(
            "apps.api.managed_services.check_jwks_live",
            return_value=LiveCheckResult("jwks", True, "ok"),
        ),
    ):
        results = run_live_connectivity_checks(settings)
    assert len(results) == 5
