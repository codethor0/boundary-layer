"""Secret manager provider unit tests."""

import logging

import pytest

from apps.api import config
from apps.api.secrets import (
    AwsSecretsManagerProvider,
    AzureKeyVaultProvider,
    DopplerSecretProvider,
    EnvironmentSecretProvider,
    GcpSecretManagerProvider,
    SecretError,
    VaultSecretProvider,
    build_secret_provider,
    redact,
)
from tests.helpers.auth_tenancy import production_saas_env, production_saas_settings


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


def test_environment_secret_provider_returns_value(monkeypatch):
    monkeypatch.setenv("BOUNDARY_LAYER_TEST_SECRET", "expected-value")
    provider = EnvironmentSecretProvider()
    assert provider.get_secret("BOUNDARY_LAYER_TEST_SECRET") == "expected-value"


def test_environment_secret_provider_missing_secret():
    provider = EnvironmentSecretProvider()
    with pytest.raises(SecretError, match="Missing secret"):
        provider.get_secret("BOUNDARY_LAYER_MISSING_SECRET")


def test_environment_secret_provider_json_secret(monkeypatch):
    monkeypatch.setenv("JSON_SECRET", '{"role":"lab_runner"}')
    provider = EnvironmentSecretProvider()
    payload = provider.get_json_secret("JSON_SECRET")
    assert payload["role"] == "lab_runner"


def test_production_saas_uses_cloud_secret_provider():
    settings = production_saas_settings()
    provider = build_secret_provider(settings)
    assert isinstance(provider, AwsSecretsManagerProvider)


def test_aws_secret_provider_requires_sdk():
    provider = AwsSecretsManagerProvider(production_saas_settings())
    with pytest.raises(SecretError, match="SDK not installed"):
        provider.get_secret("DATABASE_PASSWORD")


def test_gcp_secret_provider_requires_sdk():
    settings = production_saas_settings(SECRET_MANAGER_PROVIDER="gcp")
    provider = GcpSecretManagerProvider(settings)
    with pytest.raises(SecretError, match="SDK not installed"):
        provider.get_secret("DATABASE_PASSWORD")


def test_azure_secret_provider_requires_sdk():
    settings = production_saas_settings(SECRET_MANAGER_PROVIDER="azure")
    provider = AzureKeyVaultProvider(settings)
    with pytest.raises(SecretError, match="SDK not installed"):
        provider.get_secret("DATABASE_PASSWORD")


def test_vault_secret_provider_requires_sdk(monkeypatch):
    monkeypatch.setenv("VAULT_ADDR", "https://vault.example.com")
    monkeypatch.setenv("VAULT_TOKEN", "test-token")
    settings = production_saas_settings(SECRET_MANAGER_PROVIDER="vault")
    provider = VaultSecretProvider(settings)
    with pytest.raises(SecretError, match="SDK not installed"):
        provider.get_secret("DATABASE_PASSWORD")


def test_doppler_secret_provider_requires_token():
    settings = production_saas_settings(SECRET_MANAGER_PROVIDER="doppler")
    provider = DopplerSecretProvider(settings)
    with pytest.raises(SecretError, match="DOPPLER_TOKEN"):
        provider.get_secret("DATABASE_PASSWORD")


def test_production_saas_requires_secret_manager_in_config():
    from apps.api.config_check import _settings_kwargs
    from tests.helpers.auth_tenancy import production_saas_env

    env = production_saas_env()
    env["SECRET_MANAGER_PROVIDER"] = ""
    with pytest.raises(ValueError, match="SECRET_MANAGER_PROVIDER"):
        config.Settings(_env_file=None, **_settings_kwargs(env))


def test_production_saas_requires_secret_cache_ttl():
    from apps.api.config_check import _settings_kwargs
    from tests.helpers.auth_tenancy import production_saas_env

    env = production_saas_env()
    env["SECRET_CACHE_TTL_SECONDS"] = "0"
    with pytest.raises(ValueError, match="SECRET_CACHE_TTL_SECONDS"):
        config.Settings(_env_file=None, **_settings_kwargs(env))


def test_production_saas_rejects_env_secret_provider_override():
    settings = _policy_settings()
    settings.allow_env_secret_provider = True
    from apps.api.managed_services import check_secret_manager_policy

    issues = check_secret_manager_policy(settings)
    assert any("ALLOW_ENV_SECRET_PROVIDER" in issue for issue in issues)


def test_secret_logs_do_not_include_value(caplog, monkeypatch):
    caplog.set_level(logging.INFO)
    monkeypatch.setenv("MY_SECRET", "do-not-log-me")
    provider = EnvironmentSecretProvider()
    provider.get_secret("MY_SECRET")
    assert "do-not-log-me" not in caplog.text


def test_redact_masks_secret_values():
    assert redact("super-secret-value") == "supe**************"
    assert redact("abc") == "***"


def test_refresh_secret_clears_cache(monkeypatch):
    monkeypatch.setenv("ROTATE_ME", "first-value")
    provider = EnvironmentSecretProvider(cache_ttl_seconds=300)
    assert provider.get_secret("ROTATE_ME") == "first-value"
    monkeypatch.setenv("ROTATE_ME", "second-value")
    assert provider.refresh_secret("ROTATE_ME") == "second-value"


def test_local_lab_uses_environment_provider(monkeypatch):
    monkeypatch.delenv("BOUNDARY_LAYER_PROFILE", raising=False)
    settings = config.Settings()
    provider = build_secret_provider(settings)
    assert isinstance(provider, EnvironmentSecretProvider)
