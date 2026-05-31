"""Object storage backend unit tests."""

import logging

import pytest

from apps.api import config
from apps.api.config_check import evaluate_production_saas_readiness
from apps.api.storage import (
    DisabledProductionStorageBackend,
    LocalMemoryStorageBackend,
    StorageError,
    build_storage_backend,
)
from tests.helpers.auth_tenancy import production_saas_settings


@pytest.fixture(autouse=True)
def reset_settings_cache():
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()


def test_local_memory_storage_round_trip():
    backend = LocalMemoryStorageBackend(prefix="tenant-a/")
    metadata = backend.put_object("file.txt", b"hello", "text/plain")
    assert metadata.size_bytes == 5
    fetched = backend.get_object_metadata("file.txt")
    assert fetched.content_type == "text/plain"
    url = backend.create_presigned_upload_url("file.txt", "text/plain", 60)
    assert url.startswith("memory://upload/")
    backend.delete_object("file.txt")
    with pytest.raises(StorageError, match="not found"):
        backend.get_object_metadata("file.txt")


def test_production_saas_rejects_local_storage_backend():
    from tests.helpers.auth_tenancy import production_saas_env

    merged = production_saas_env()
    merged["BOUNDARY_LAYER_FILE_STORAGE_BACKEND"] = "local"
    report = evaluate_production_saas_readiness(merged)
    assert report.ready is False
    assert any("local disk" in issue for issue in report.issues)


def test_production_saas_requires_bucket():
    from tests.helpers.auth_tenancy import production_saas_env

    merged = production_saas_env()
    merged["OBJECT_STORAGE_BUCKET"] = ""
    report = evaluate_production_saas_readiness(merged)
    assert report.ready is False
    assert any("OBJECT_STORAGE_BUCKET" in issue for issue in report.issues)


def test_production_saas_storage_backend_fails_closed():
    settings = production_saas_settings()
    backend = build_storage_backend(settings)
    assert isinstance(backend, DisabledProductionStorageBackend)
    with pytest.raises(StorageError, match="not implemented"):
        backend.create_presigned_upload_url("key", "text/plain", 60)


def test_local_lab_uses_memory_backend(monkeypatch):
    monkeypatch.delenv("BOUNDARY_LAYER_PROFILE", raising=False)
    settings = config.Settings()
    backend = build_storage_backend(settings)
    assert isinstance(backend, LocalMemoryStorageBackend)


def test_disabled_backend_put_object_fails():
    backend = DisabledProductionStorageBackend("missing adapter")
    with pytest.raises(StorageError, match="missing adapter"):
        backend.put_object("k", b"x", "text/plain")


def test_environment_provider_logs_without_secret(caplog):
    caplog.set_level(logging.INFO)
    from apps.api.secrets import EnvironmentSecretProvider

    provider = EnvironmentSecretProvider()
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("TEST_SECRET_VALUE", "super-secret-value")
        value = provider.get_secret("TEST_SECRET_VALUE")
    assert value == "super-secret-value"
    assert "super-secret-value" not in caplog.text
