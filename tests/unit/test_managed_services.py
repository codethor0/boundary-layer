"""Managed service readiness unit tests."""

import pytest

from apps.api import config
from apps.api.managed_services import (
    LIVE_CHECKS_ENV,
    check_database_url_policy,
    check_object_storage_policy,
    check_redis_url_policy,
    check_secret_manager_policy,
    evaluate_managed_services_readiness,
)
from tests.helpers.auth_tenancy import production_saas_env


def _policy_settings(**overrides: str):
    env = production_saas_env()
    env.update(overrides)
    from apps.api.config_check import _settings_kwargs

    return config.Settings(_env_file=None, **_settings_kwargs(env))


@pytest.fixture(autouse=True)
def reset_settings_cache():
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()


def _managed_env(**overrides: str) -> dict[str, str]:
    env = production_saas_env()
    env["BOUNDARY_LAYER_ENV"] = "staging"
    env["BOUNDARY_LAYER_AUTH_PROVIDER"] = "oidc"
    env["OIDC_ALGORITHMS"] = "RS256"
    env.update(overrides)
    return env


def test_managed_services_reports_not_ready_by_default():
    report = evaluate_managed_services_readiness({"BOUNDARY_LAYER_ENV": "staging"})
    assert report.ready is False
    assert report.issues


def test_managed_services_example_passes_structurally():
    report = evaluate_managed_services_readiness(_managed_env(), mocked=True)
    assert report.ready is True
    assert report.structural is True
    assert report.live is False


def test_policy_rejects_localhost_database():
    settings = _policy_settings()
    settings.database_url = "postgresql://u:p@localhost:5432/db?sslmode=require"
    issues = check_database_url_policy(settings)
    assert any("DATABASE_URL" in issue for issue in issues)


def test_policy_rejects_container_database_host():
    settings = _policy_settings()
    settings.database_url = "postgresql://u:p@postgres:5432/db?sslmode=require"
    issues = check_database_url_policy(settings)
    assert any("DATABASE_URL" in issue for issue in issues)


def test_policy_requires_db_ssl():
    settings = _policy_settings()
    settings.database_url = "postgresql://u:p@db.example:5432/db"
    settings.db_ssl_mode = ""
    issues = check_database_url_policy(settings)
    assert any("SSL" in issue for issue in issues)


def test_policy_requires_redis_tls():
    settings = _policy_settings()
    settings.redis_url = "redis://redis.example:6379/0"
    issues = check_redis_url_policy(settings)
    assert any("rediss://" in issue for issue in issues)


def test_policy_rejects_local_storage_backend():
    settings = _policy_settings()
    settings.file_storage_backend = "local"
    issues = check_object_storage_policy(settings)
    assert any("local disk" in issue for issue in issues)


def test_policy_requires_secret_rotation():
    settings = _policy_settings()
    settings.secret_rotation_required = False
    issues = check_secret_manager_policy(settings)
    assert any("SECRET_ROTATION_REQUIRED" in issue for issue in issues)


def test_policy_requires_secret_cache_ttl():
    settings = _policy_settings()
    settings.secret_cache_ttl_seconds = 0
    issues = check_secret_manager_policy(settings)
    assert any("SECRET_CACHE_TTL_SECONDS" in issue for issue in issues)


def test_live_checks_skipped_by_default(monkeypatch):
    monkeypatch.delenv(LIVE_CHECKS_ENV, raising=False)
    report = evaluate_managed_services_readiness(_managed_env(), mocked=True)
    assert report.live is False
    assert any("skipped" in note.lower() for note in report.notes)


def test_live_checks_flag_respected(monkeypatch):
    monkeypatch.setenv(LIVE_CHECKS_ENV, "true")
    report = evaluate_managed_services_readiness(_managed_env(), mocked=True, live=True)
    assert report.live is True


def test_immutable_audit_policy_flags_postgres_sink():
    settings = _policy_settings()
    settings.audit_immutable_required = True
    settings.audit_sink_provider = "postgres"
    issues = check_secret_manager_policy(settings)
    assert any("AUDIT_IMMUTABLE_REQUIRED" in issue for issue in issues)


def test_managed_services_module_main_not_ready():
    from apps.api import managed_services as module

    exit_code = module.main()
    assert exit_code == 1
