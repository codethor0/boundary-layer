"""Object storage backend abstraction for Production SaaS."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Protocol

from apps.api.config import Settings

logger = logging.getLogger("boundary_layer.api.storage")

SUPPORTED_OBJECT_STORAGE_BACKENDS = frozenset({"s3", "gcs", "r2"})
TENANT_KEY_SEGMENT = "tenants"
_TENANT_KEY_PATTERN = re.compile(r"^tenants/([^/]+)/")


class StorageError(Exception):
    """Object storage operation failure."""

    def __init__(self, message: str, code: str = "storage_error"):
        super().__init__(message)
        self.message = message
        self.code = code


SDK_NOT_INSTALLED_MESSAGE = (
    "Provider SDK not installed. Install optional dependency "
    "or use the local test backend."
)


@dataclass(frozen=True)
class ObjectMetadata:
    key: str
    size_bytes: int
    content_type: str


class StorageBackend(Protocol):
    def put_object(
        self,
        key: str,
        data: bytes,
        content_type: str,
        *,
        tenant_id: str = "",
    ) -> ObjectMetadata:
        """Store an object."""

    def get_object_metadata(
        self,
        key: str,
        *,
        tenant_id: str = "",
    ) -> ObjectMetadata:
        """Return metadata for an existing object."""

    def delete_object(self, key: str, *, tenant_id: str = "") -> None:
        """Delete an object."""

    def create_presigned_upload_url(
        self,
        key: str,
        content_type: str,
        ttl_seconds: int,
        *,
        tenant_id: str = "",
    ) -> str:
        """Return a presigned upload URL."""


def build_tenant_object_key(
    tenant_id: str,
    relative_key: str,
    *,
    prefix: str = "",
    require_tenant: bool = True,
) -> str:
    if require_tenant and not tenant_id.strip():
        raise StorageError(
            "tenant_id is required for object keys in production-saas",
            "tenant_required",
        )
    relative = relative_key.lstrip("/")
    normalized_prefix = prefix.strip().rstrip("/")
    if normalized_prefix.endswith(TENANT_KEY_SEGMENT):
        return f"{normalized_prefix}/{tenant_id.strip()}/{relative}"
    tenant_part = f"{TENANT_KEY_SEGMENT}/{tenant_id.strip()}/{relative}"
    if normalized_prefix:
        return f"{normalized_prefix}/{tenant_part}"
    return tenant_part


def extract_tenant_from_object_key(key: str) -> str | None:
    normalized = key.lstrip("/")
    match = _TENANT_KEY_PATTERN.match(normalized)
    if not match:
        return None
    return match.group(1)


def assert_tenant_object_access(tenant_id: str, object_key: str) -> None:
    key_tenant = extract_tenant_from_object_key(object_key)
    if key_tenant is None:
        raise StorageError(
            "Object key must be tenant-scoped as tenants/{tenant_id}/...",
            "tenant_scope_required",
        )
    if key_tenant != tenant_id.strip():
        raise StorageError(
            "Cross-tenant object access denied",
            "cross_tenant_denied",
        )


def cap_presigned_ttl(requested_ttl: int, max_ttl: int) -> int:
    if requested_ttl <= 0:
        raise StorageError("Presigned URL TTL must be positive", "invalid_ttl")
    return min(requested_ttl, max_ttl)


def _resolve_object_key(
    key: str,
    tenant_id: str,
    settings: Settings,
    *,
    require_tenant: bool,
) -> str:
    if tenant_id.strip():
        if key.startswith(f"{TENANT_KEY_SEGMENT}/"):
            object_key = key
        else:
            object_key = build_tenant_object_key(
                tenant_id,
                key,
                prefix=settings.object_storage_prefix,
                require_tenant=require_tenant,
            )
        assert_tenant_object_access(tenant_id, object_key)
        return object_key
    if require_tenant:
        raise StorageError(
            "tenant_id is required for object keys in production-saas",
            "tenant_required",
        )
    prefix = settings.object_storage_prefix.strip()
    if prefix and not key.startswith(prefix):
        return f"{prefix.rstrip('/')}/{key.lstrip('/')}"
    return key


@dataclass
class LocalMemoryStorageBackend:
    """In-memory storage for unit tests only."""

    prefix: str = "test/"
    require_tenant: bool = False
    _objects: dict[str, tuple[bytes, str]] = field(default_factory=dict)

    def _full_key(self, key: str, tenant_id: str = "") -> str:
        if tenant_id.strip() or self.require_tenant:
            return build_tenant_object_key(
                tenant_id,
                key,
                prefix=self.prefix,
                require_tenant=self.require_tenant,
            )
        return f"{self.prefix.rstrip('/')}/{key.lstrip('/')}"

    def put_object(
        self,
        key: str,
        data: bytes,
        content_type: str,
        *,
        tenant_id: str = "",
    ) -> ObjectMetadata:
        full_key = self._full_key(key, tenant_id)
        self._objects[full_key] = (data, content_type)
        return ObjectMetadata(
            key=full_key,
            size_bytes=len(data),
            content_type=content_type,
        )

    def get_object_metadata(
        self,
        key: str,
        *,
        tenant_id: str = "",
    ) -> ObjectMetadata:
        full_key = self._full_key(key, tenant_id)
        if full_key not in self._objects:
            raise StorageError(f"Object not found: {key}", "storage_not_found")
        data, content_type = self._objects[full_key]
        return ObjectMetadata(
            key=full_key,
            size_bytes=len(data),
            content_type=content_type,
        )

    def delete_object(self, key: str, *, tenant_id: str = "") -> None:
        full_key = self._full_key(key, tenant_id)
        if full_key not in self._objects:
            raise StorageError(f"Object not found: {key}", "storage_not_found")
        del self._objects[full_key]

    def create_presigned_upload_url(
        self,
        key: str,
        content_type: str,
        ttl_seconds: int,
        *,
        tenant_id: str = "",
    ) -> str:
        full_key = self._full_key(key, tenant_id)
        capped = cap_presigned_ttl(ttl_seconds, ttl_seconds)
        return f"memory://upload/{full_key}?content_type={content_type}&ttl={capped}"


class DisabledProductionStorageBackend:
    """Fail-closed storage when production-saas lacks a real provider adapter."""

    def __init__(self, reason: str) -> None:
        self._reason = reason

    def _fail(self) -> None:
        raise StorageError(self._reason, "storage_not_configured")

    def put_object(
        self,
        key: str,
        data: bytes,
        content_type: str,
        *,
        tenant_id: str = "",
    ) -> ObjectMetadata:
        self._fail()
        raise AssertionError("unreachable")

    def get_object_metadata(
        self,
        key: str,
        *,
        tenant_id: str = "",
    ) -> ObjectMetadata:
        self._fail()
        raise AssertionError("unreachable")

    def delete_object(self, key: str, *, tenant_id: str = "") -> None:
        self._fail()

    def create_presigned_upload_url(
        self,
        key: str,
        content_type: str,
        ttl_seconds: int,
        *,
        tenant_id: str = "",
    ) -> str:
        self._fail()
        raise AssertionError("unreachable")


class _CloudStorageBackendBase:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._require_tenant = settings.is_production_saas

    def _object_key(
        self,
        key: str,
        tenant_id: str,
    ) -> str:
        return _resolve_object_key(
            key,
            tenant_id,
            self._settings,
            require_tenant=self._require_tenant,
        )

    def _capped_ttl(self, ttl_seconds: int) -> int:
        return cap_presigned_ttl(
            ttl_seconds,
            self._settings.object_storage_presigned_url_ttl_seconds,
        )


class S3StorageBackend(_CloudStorageBackendBase):
    """AWS S3 object storage adapter (lazy boto3 import)."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        self._client = None

    def _require_boto3(self):
        try:
            import boto3
        except ImportError as exc:
            raise StorageError(SDK_NOT_INSTALLED_MESSAGE, "sdk_not_installed") from exc
        return boto3

    def _s3_client(self):
        if self._client is None:
            boto3 = self._require_boto3()
            self._client = boto3.client(
                "s3",
                region_name=self._settings.object_storage_region.strip(),
            )
        return self._client

    def put_object(
        self,
        key: str,
        data: bytes,
        content_type: str,
        *,
        tenant_id: str = "",
    ) -> ObjectMetadata:
        object_key = self._object_key(key, tenant_id)
        client = self._s3_client()
        client.put_object(
            Bucket=self._settings.object_storage_bucket,
            Key=object_key,
            Body=data,
            ContentType=content_type,
        )
        return ObjectMetadata(
            key=object_key,
            size_bytes=len(data),
            content_type=content_type,
        )

    def get_object_metadata(
        self,
        key: str,
        *,
        tenant_id: str = "",
    ) -> ObjectMetadata:
        object_key = self._object_key(key, tenant_id)
        client = self._s3_client()
        response = client.head_object(
            Bucket=self._settings.object_storage_bucket,
            Key=object_key,
        )
        return ObjectMetadata(
            key=object_key,
            size_bytes=int(response.get("ContentLength", 0)),
            content_type=str(response.get("ContentType", "application/octet-stream")),
        )

    def delete_object(self, key: str, *, tenant_id: str = "") -> None:
        object_key = self._object_key(key, tenant_id)
        client = self._s3_client()
        client.delete_object(
            Bucket=self._settings.object_storage_bucket,
            Key=object_key,
        )

    def create_presigned_upload_url(
        self,
        key: str,
        content_type: str,
        ttl_seconds: int,
        *,
        tenant_id: str = "",
    ) -> str:
        object_key = self._object_key(key, tenant_id)
        capped = self._capped_ttl(ttl_seconds)
        client = self._s3_client()
        return client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self._settings.object_storage_bucket,
                "Key": object_key,
                "ContentType": content_type,
            },
            ExpiresIn=capped,
        )


class R2StorageBackend(S3StorageBackend):
    """Cloudflare R2 adapter (S3-compatible API with custom endpoint)."""

    def _s3_client(self):
        if self._client is None:
            endpoint = self._settings.object_storage_endpoint.strip()
            if not endpoint:
                raise StorageError(
                    "OBJECT_STORAGE_ENDPOINT is required for r2 backend",
                    "storage_config_invalid",
                )
            boto3 = self._require_boto3()
            self._client = boto3.client(
                "s3",
                region_name=self._settings.object_storage_region.strip() or "auto",
                endpoint_url=endpoint,
            )
        return self._client


class GCSStorageBackend(_CloudStorageBackendBase):
    """Google Cloud Storage adapter (lazy google-cloud-storage import)."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        self._client = None

    def _require_gcs(self):
        try:
            from google.cloud import storage
        except ImportError as exc:
            raise StorageError(SDK_NOT_INSTALLED_MESSAGE, "sdk_not_installed") from exc
        return storage

    def _bucket(self):
        if self._client is None:
            storage = self._require_gcs()
            self._client = storage.Client().bucket(
                self._settings.object_storage_bucket.strip()
            )
        return self._client

    def put_object(
        self,
        key: str,
        data: bytes,
        content_type: str,
        *,
        tenant_id: str = "",
    ) -> ObjectMetadata:
        object_key = self._object_key(key, tenant_id)
        blob = self._bucket().blob(object_key)
        blob.upload_from_string(data, content_type=content_type)
        return ObjectMetadata(
            key=object_key,
            size_bytes=len(data),
            content_type=content_type,
        )

    def get_object_metadata(
        self,
        key: str,
        *,
        tenant_id: str = "",
    ) -> ObjectMetadata:
        object_key = self._object_key(key, tenant_id)
        blob = self._bucket().blob(object_key)
        blob.reload()
        return ObjectMetadata(
            key=object_key,
            size_bytes=int(blob.size or 0),
            content_type=str(blob.content_type or "application/octet-stream"),
        )

    def delete_object(self, key: str, *, tenant_id: str = "") -> None:
        object_key = self._object_key(key, tenant_id)
        self._bucket().blob(object_key).delete()

    def create_presigned_upload_url(
        self,
        key: str,
        content_type: str,
        ttl_seconds: int,
        *,
        tenant_id: str = "",
    ) -> str:
        object_key = self._object_key(key, tenant_id)
        capped = self._capped_ttl(ttl_seconds)
        blob = self._bucket().blob(object_key)
        return blob.generate_signed_url(
            version="v4",
            expiration=capped,
            method="PUT",
            content_type=content_type,
        )


def validate_storage_settings(settings: Settings) -> None:
    backend = settings.file_storage_backend.strip().lower()
    if settings.is_production_saas:
        if backend in {"local", "disk", "filesystem", "memory"}:
            raise ValueError(
                "BOUNDARY_LAYER_FILE_STORAGE_BACKEND must not use local disk in "
                "production-saas"
            )
        if backend not in SUPPORTED_OBJECT_STORAGE_BACKENDS:
            raise ValueError(
                "BOUNDARY_LAYER_FILE_STORAGE_BACKEND must be one of: "
                + ", ".join(sorted(SUPPORTED_OBJECT_STORAGE_BACKENDS))
            )
        if not settings.object_storage_bucket.strip():
            raise ValueError("OBJECT_STORAGE_BUCKET is required in production-saas")
        if backend == "r2" and not settings.object_storage_endpoint.strip():
            raise ValueError("OBJECT_STORAGE_ENDPOINT is required for r2 backend")


def build_storage_backend(settings: Settings) -> StorageBackend:
    validate_storage_settings(settings)
    backend = settings.file_storage_backend.strip().lower()
    if settings.is_local_lab:
        prefix = settings.object_storage_prefix or "local/"
        return LocalMemoryStorageBackend(prefix=prefix)
    if settings.is_production_saas:
        if backend == "s3":
            return S3StorageBackend(settings)
        if backend == "gcs":
            return GCSStorageBackend(settings)
        if backend == "r2":
            return R2StorageBackend(settings)
        return DisabledProductionStorageBackend(
            reason=(
                f"Object storage adapter for {backend} is not configured; "
                "set FILE_STORAGE_BACKEND to s3, gcs, or r2"
            )
        )
    return LocalMemoryStorageBackend(prefix=settings.object_storage_prefix or "test/")
