"""Shared pytest configuration."""

from __future__ import annotations

import os

import pytest

_ISOLATED_ENV_KEYS = tuple(
    key
    for key in list(os.environ)
    if key.startswith("BOUNDARY_LAYER_")
    or key
    in {
        "POSTGRES_PASSWORD",
        "REDIS_PASSWORD",
        "SESSION_HMAC_SECRET",
        "POSTGRES_SSLMODE",
        "POSTGRES_SSL_ROOT_CERT",
        "REDIS_TLS_ENABLED",
        "REDIS_SSL_CA_CERT",
    }
)


def pytest_configure(config):
    for key in _ISOLATED_ENV_KEYS:
        os.environ.pop(key, None)
    os.environ.setdefault("BOUNDARY_LAYER_ENV", "development")


@pytest.fixture(autouse=True)
def reset_settings_cache():
    from apps.api import config

    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()
