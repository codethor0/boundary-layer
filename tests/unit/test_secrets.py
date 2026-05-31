"""Secret manager provider unit tests."""

import logging

import pytest

from apps.api import config
from apps.api.secrets import (
    DisabledProductionSecretProvider,
    EnvironmentSecretProvider,
    SecretError,
    build_secret_provider,
)
from tests.helpers.auth_tenancy import production_saas_settings


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


def test_production_saas_secret_provider_fails_closed():
    settings = production_saas_settings()
    provider = build_secret_provider(settings)
    assert isinstance(provider, DisabledProductionSecretProvider)
    with pytest.raises(SecretError, match="not implemented"):
        provider.get_secret("DATABASE_PASSWORD")


def test_production_saas_requires_secret_manager_in_config():
    from apps.api.config_check import _settings_kwargs
    from tests.helpers.auth_tenancy import production_saas_env

    env = production_saas_env()
    env["SECRET_MANAGER_PROVIDER"] = ""
    with pytest.raises(ValueError, match="SECRET_MANAGER_PROVIDER"):
        config.Settings(_env_file=None, **_settings_kwargs(env))


def test_secret_logs_do_not_include_value(caplog, monkeypatch):
    caplog.set_level(logging.INFO)
    monkeypatch.setenv("MY_SECRET", "do-not-log-me")
    provider = EnvironmentSecretProvider()
    provider.get_secret("MY_SECRET")
    assert "do-not-log-me" not in caplog.text
