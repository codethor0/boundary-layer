"""Object storage backend unit tests."""

import logging

import pytest

from apps.api import config
from apps.api.config_check import evaluate_production_saas_readiness
from apps.api.storage import (
    GCSStorageBackend,
    LocalMemoryStorageBackend,
    R2StorageBackend,
    S3StorageBackend,
    StorageError,
    assert_tenant_object_access,
    build_storage_backend,
    build_tenant_object_key,
    cap_presigned_ttl,
    extract_tenant_from_object_key,
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


def test_build_tenant_object_key_scopes_by_tenant():
    key = build_tenant_object_key("tenant-a", "artifacts/file.txt", prefix="tenants/")
    assert key == "tenants/tenant-a/artifacts/file.txt"


def test_build_tenant_object_key_requires_tenant_in_production_saas():
    with pytest.raises(StorageError, match="tenant_id is required"):
        build_tenant_object_key("", "file.txt")


def test_extract_tenant_from_object_key():
    assert extract_tenant_from_object_key("tenants/tenant-a/file.txt") == "tenant-a"
    assert extract_tenant_from_object_key("other/path") is None


def test_cross_tenant_object_access_denied():
    with pytest.raises(StorageError, match="Cross-tenant"):
        assert_tenant_object_access("tenant-a", "tenants/tenant-b/file.txt")


def test_presigned_url_ttl_capped():
    assert cap_presigned_ttl(120, 60) == 60
    with pytest.raises(StorageError, match="TTL"):
        cap_presigned_ttl(0, 60)


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


def test_production_saas_uses_s3_adapter():
    settings = production_saas_settings()
    backend = build_storage_backend(settings)
    assert isinstance(backend, S3StorageBackend)


def test_s3_adapter_requires_sdk_for_operations():
    settings = production_saas_settings()
    backend = S3StorageBackend(settings)
    with pytest.raises(StorageError, match="SDK not installed"):
        backend.put_object("file.txt", b"data", "text/plain", tenant_id="tenant-a")


def test_gcs_adapter_requires_sdk_for_operations():
    settings = production_saas_settings(BOUNDARY_LAYER_FILE_STORAGE_BACKEND="gcs")
    backend = GCSStorageBackend(settings)
    with pytest.raises(StorageError, match="SDK not installed"):
        backend.get_object_metadata("file.txt", tenant_id="tenant-a")


def test_r2_adapter_requires_endpoint():
    from apps.api.config_check import _settings_kwargs
    from tests.helpers.auth_tenancy import production_saas_env

    env = production_saas_env()
    env["BOUNDARY_LAYER_FILE_STORAGE_BACKEND"] = "r2"
    env["OBJECT_STORAGE_ENDPOINT"] = ""
    with pytest.raises(ValueError, match="OBJECT_STORAGE_ENDPOINT"):
        config.Settings(_env_file=None, **_settings_kwargs(env))


def test_r2_adapter_requires_sdk_when_endpoint_configured():
    settings = production_saas_settings(
        BOUNDARY_LAYER_FILE_STORAGE_BACKEND="r2",
        OBJECT_STORAGE_ENDPOINT="https://example.r2.cloudflarestorage.com",
    )
    backend = R2StorageBackend(settings)
    with pytest.raises(StorageError, match="SDK not installed"):
        backend.create_presigned_upload_url(
            "file.txt",
            "text/plain",
            60,
            tenant_id="tenant-a",
        )


def test_cloud_storage_rejects_cross_tenant_object_key():
    settings = production_saas_settings()
    backend = S3StorageBackend(settings)
    with pytest.raises(StorageError, match="Cross-tenant"):
        backend._object_key("tenants/tenant-b/file.txt", "tenant-a")


def test_local_lab_uses_memory_backend(monkeypatch):
    monkeypatch.delenv("BOUNDARY_LAYER_PROFILE", raising=False)
    settings = config.Settings()
    backend = build_storage_backend(settings)
    assert isinstance(backend, LocalMemoryStorageBackend)


def test_storage_errors_do_not_include_secret_values(caplog):
    caplog.set_level(logging.ERROR)
    backend = S3StorageBackend(production_saas_settings())
    with pytest.raises(StorageError):
        backend.put_object("file.txt", b"secret-payload", "text/plain", tenant_id="t1")
    assert "secret-payload" not in caplog.text
