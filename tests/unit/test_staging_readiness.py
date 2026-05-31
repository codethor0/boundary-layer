"""Production SaaS staging readiness tests."""

import pytest

from apps.api import config
from apps.api.config_check import evaluate_production_saas_readiness
from apps.api.staging_check import evaluate_staging_readiness
from tests.helpers.auth_tenancy import production_saas_env


@pytest.fixture(autouse=True)
def reset_settings_cache():
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()


def _staging_env(**overrides: str) -> dict[str, str]:
    env = {
        "BOUNDARY_LAYER_PROFILE": "production-saas",
        "BOUNDARY_LAYER_ENV": "staging",
        "BOUNDARY_LAYER_AUTH_ENABLED": "true",
        "BOUNDARY_LAYER_AUTH_PROVIDER": "oidc",
        "OIDC_ISSUER_URL": "https://staging-issuer.example.com",
        "OIDC_AUDIENCE": "boundary-layer-api-staging",
        "OIDC_JWKS_URL": "https://staging-issuer.example.com/.well-known/jwks.json",
        "OIDC_ALGORITHMS": "RS256",
        "OIDC_TENANT_CLAIM": "https://boundarylayer.dev/tenant_id",
        "OIDC_ROLES_CLAIM": "https://boundarylayer.dev/roles",
        "OIDC_SUBJECT_CLAIM": "sub",
        "OIDC_EMAIL_CLAIM": "email",
        "OIDC_CLOCK_SKEW_SECONDS": "60",
        "DATABASE_URL": (
            "postgresql://boundary_layer:test@db.staging.example:5432/"
            "boundary_layer?sslmode=require"
        ),
        "DB_SSL_MODE": "require",
        "REDIS_URL": "rediss://:test@redis.staging.example:6379/0",
        "REDIS_KEY_PREFIX": "boundary_layer:tenant",
        "BOUNDARY_LAYER_SECRET_KEY": "production-saas-staging-secret-key-minimum-32",
        "BOUNDARY_LAYER_ALLOWED_ORIGINS": "https://staging.example.com",
        "BOUNDARY_LAYER_PUBLIC_BASE_URL": "https://staging.example.com",
        "BOUNDARY_LAYER_SECURE_COOKIES": "true",
        "BOUNDARY_LAYER_TRUST_PROXY_HEADERS": "true",
        "BOUNDARY_LAYER_METRICS_TOKEN": "production-metrics-token-minimum-24",
        "BOUNDARY_LAYER_FILE_STORAGE_BACKEND": "s3",
        "OBJECT_STORAGE_BUCKET": "boundary-layer-staging-artifacts",
        "OBJECT_STORAGE_REGION": "us-east-1",
        "BOUNDARY_LAYER_AUDIT_LOG_ENABLED": "true",
        "SECRET_MANAGER_PROVIDER": "aws",
        "SECRET_MANAGER_PROJECT_OR_PATH": "boundary-layer/staging",
        "BOUNDARY_LAYER_API_KEY": "production-api-key-minimum-24-chars",
        "POSTGRES_PASSWORD": "production-postgres-password",
        "REDIS_PASSWORD": "production-redis-password-16",
        "SESSION_HMAC_SECRET": "production-session-hmac-secret",
    }
    env.update(overrides)
    return env


def test_staging_readiness_reports_not_ready_by_default():
    report = evaluate_staging_readiness({"BOUNDARY_LAYER_ENV": "staging"})
    assert report.ready is False
    assert report.issues


def test_staging_readiness_example_passes():
    report = evaluate_staging_readiness(_staging_env(), mocked=True)
    assert report.ready is True
    assert report.mocked is True


def test_staging_rejects_http_oidc_issuer(monkeypatch):
    env = _staging_env(OIDC_ISSUER_URL="http://insecure.example.com")
    with pytest.raises(ValueError, match="OIDC_ISSUER_URL"):
        config.Settings.model_validate(
            __import__(
                "apps.api.staging_check", fromlist=["_settings_from_merged"]
            )._settings_from_merged(env)
        )


def test_staging_rejects_oidc_test_provider():
    env = _staging_env(BOUNDARY_LAYER_AUTH_PROVIDER="oidc-test")
    report = evaluate_staging_readiness(env)
    assert report.ready is False
    assert any("oidc-test" in issue for issue in report.issues)


def test_staging_rejects_localhost_database():
    env = _staging_env(
        DATABASE_URL="postgresql://u:p@localhost:5432/db?sslmode=require"
    )
    report = evaluate_staging_readiness(env)
    assert report.ready is False
    assert any("DATABASE_URL" in issue for issue in report.issues)


def test_staging_rejects_non_tls_redis():
    env = _staging_env(REDIS_URL="redis://localhost:6379/0")
    report = evaluate_staging_readiness(env)
    assert report.ready is False
    assert any("REDIS_URL" in issue for issue in report.issues)


def test_staging_rejects_missing_tenant_claim():
    env = _staging_env(OIDC_TENANT_CLAIM="")
    report = evaluate_staging_readiness(env)
    assert report.ready is False
    assert any("OIDC_TENANT_CLAIM" in issue for issue in report.issues)


def test_staging_rejects_missing_roles_claim():
    env = _staging_env(OIDC_ROLES_CLAIM="")
    report = evaluate_staging_readiness(env)
    assert report.ready is False
    assert any("OIDC_ROLES_CLAIM" in issue for issue in report.issues)


def test_production_saas_rejects_localhost_database(monkeypatch):
    env = production_saas_env()
    env["DATABASE_URL"] = "postgresql://u:p@postgres:5432/db?sslmode=require"
    report = evaluate_production_saas_readiness(env)
    assert report.ready is False


def test_production_saas_rejects_redis_without_tls():
    env = production_saas_env()
    env["REDIS_URL"] = "redis://redis.example:6379/0"
    report = evaluate_production_saas_readiness(env)
    assert report.ready is False


def test_production_saas_rejects_missing_secret_manager():
    env = production_saas_env()
    env["SECRET_MANAGER_PROVIDER"] = ""
    report = evaluate_production_saas_readiness(env)
    assert report.ready is False


def test_production_saas_rejects_database_without_ssl():
    env = production_saas_env()
    env["DATABASE_URL"] = "postgresql://u:p@postgres.example:5432/db"
    env["DB_SSL_MODE"] = ""
    report = evaluate_production_saas_readiness(env)
    assert report.ready is False
