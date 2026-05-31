"""Production SaaS profile guardrail tests."""

import pytest

from apps.api import config
from apps.api.config_check import evaluate_production_saas_readiness
from tests.helpers.auth_tenancy import production_saas_env as _base_production_saas_env


@pytest.fixture(autouse=True)
def reset_settings_cache():
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()


def _production_like_env(monkeypatch):
    monkeypatch.setenv("BOUNDARY_LAYER_PROFILE", "production-like")
    monkeypatch.setenv("BOUNDARY_LAYER_ENV", "production")
    monkeypatch.setenv("BOUNDARY_LAYER_API_KEY", "a" * 32)
    monkeypatch.setenv("BOUNDARY_LAYER_METRICS_TOKEN", "b" * 32)
    monkeypatch.setenv("POSTGRES_PASSWORD", "postgres-secret-16")
    monkeypatch.setenv("REDIS_PASSWORD", "redis-secret-16chars")
    monkeypatch.setenv("SESSION_HMAC_SECRET", "session-hmac-secret")


def _production_saas_env(monkeypatch):
    _production_like_env(monkeypatch)
    for key, value in _base_production_saas_env().items():
        monkeypatch.setenv(key, value)


def test_local_lab_profile_uses_local_defaults(monkeypatch):
    monkeypatch.delenv("BOUNDARY_LAYER_PROFILE", raising=False)
    settings = config.Settings()
    assert settings.boundary_layer_profile == "local-lab"
    assert settings.is_local_lab is True
    assert settings.auth_enabled is False
    assert settings.allow_vulnerable is True


def test_production_like_profile_remains_supported(monkeypatch):
    _production_like_env(monkeypatch)
    settings = config.Settings()
    assert settings.boundary_layer_profile == "production-like"
    assert settings.is_production is True
    assert settings.auth_enabled is True
    assert settings.allow_vulnerable is False


def test_production_saas_profile_fails_when_required_settings_missing(monkeypatch):
    monkeypatch.setenv("BOUNDARY_LAYER_PROFILE", "production-saas")
    monkeypatch.setenv("BOUNDARY_LAYER_ENV", "production")
    with pytest.raises(ValueError, match="required"):
        config.Settings(_env_file=None)


def test_production_saas_profile_passes_with_mocked_settings(monkeypatch):
    _production_saas_env(monkeypatch)
    settings = config.Settings()
    assert settings.is_production_saas is True
    assert settings.audit_log_enabled is True


def test_production_saas_rejects_insecure_secret_key(monkeypatch):
    _production_saas_env(monkeypatch)
    monkeypatch.setenv("BOUNDARY_LAYER_SECRET_KEY", "short")
    with pytest.raises(ValueError, match="BOUNDARY_LAYER_SECRET_KEY"):
        config.Settings()


def test_production_saas_requires_allowed_origins(monkeypatch):
    _production_saas_env(monkeypatch)
    monkeypatch.setenv("BOUNDARY_LAYER_ALLOWED_ORIGINS", "")
    with pytest.raises(ValueError, match="BOUNDARY_LAYER_ALLOWED_ORIGINS"):
        config.Settings()


def test_production_saas_requires_metrics_auth_token(monkeypatch):
    _production_saas_env(monkeypatch)
    monkeypatch.setenv("BOUNDARY_LAYER_METRICS_TOKEN", "")
    with pytest.raises(ValueError, match="BOUNDARY_LAYER_METRICS_TOKEN"):
        config.Settings()


def test_production_saas_requires_audit_log_enabled(monkeypatch):
    _production_saas_env(monkeypatch)
    monkeypatch.setenv("BOUNDARY_LAYER_AUDIT_LOG_ENABLED", "false")
    with pytest.raises(ValueError, match="BOUNDARY_LAYER_AUDIT_LOG_ENABLED"):
        config.Settings()


def test_production_saas_check_reports_not_ready_by_default():
    report = evaluate_production_saas_readiness(
        {
            "BOUNDARY_LAYER_PROFILE": "production-saas",
            "BOUNDARY_LAYER_ENV": "production",
        }
    )
    assert report.ready is False
    assert report.issues


def test_production_saas_check_passes_with_mocked_env():
    report = evaluate_production_saas_readiness(_base_production_saas_env())
    assert report.ready is True


def test_production_saas_requires_oidc_issuer_url(monkeypatch):
    _production_saas_env(monkeypatch)
    monkeypatch.setenv("OIDC_ISSUER_URL", "")
    with pytest.raises(ValueError, match="OIDC_ISSUER_URL"):
        config.Settings()


def test_production_saas_requires_oidc_jwks_url(monkeypatch):
    _production_saas_env(monkeypatch)
    monkeypatch.setenv("OIDC_JWKS_URL", "")
    with pytest.raises(ValueError, match="OIDC_JWKS_URL"):
        config.Settings()


def test_production_saas_requires_oidc_audience(monkeypatch):
    _production_saas_env(monkeypatch)
    monkeypatch.setenv("OIDC_AUDIENCE", "")
    with pytest.raises(ValueError, match="OIDC_AUDIENCE"):
        config.Settings()


def test_production_saas_rejects_wildcard_origins(monkeypatch):
    _production_saas_env(monkeypatch)
    monkeypatch.setenv("BOUNDARY_LAYER_ALLOWED_ORIGINS", "*")
    with pytest.raises(ValueError, match="wildcards"):
        config.Settings()


def test_production_saas_rejects_insecure_algorithms(monkeypatch):
    _production_saas_env(monkeypatch)
    monkeypatch.setenv("OIDC_ALGORITHMS", "none,HS256")
    with pytest.raises(ValueError, match="OIDC_ALGORITHMS"):
        config.Settings()


def test_local_lab_does_not_require_oidc(monkeypatch):
    monkeypatch.delenv("BOUNDARY_LAYER_PROFILE", raising=False)
    monkeypatch.delenv("OIDC_ISSUER_URL", raising=False)
    settings = config.Settings()
    assert settings.boundary_layer_profile == "local-lab"
    assert settings.oidc_issuer_url == ""
