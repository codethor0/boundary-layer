"""Object storage backend abstraction for Production SaaS."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Protocol

from apps.api.config import Settings

logger = logging.getLogger("boundary_layer.api.storage")

SUPPORTED_OBJECT_STORAGE_BACKENDS = frozenset({"s3", "gcs", "r2"})


class StorageError(Exception):
    """Object storage operation failure."""

    def __init__(self, message: str, code: str = "storage_error"):
        super().__init__(message)
        self.message = message
        self.code = code


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
    ) -> ObjectMetadata:
        """Store an object."""

    def get_object_metadata(self, key: str) -> ObjectMetadata:
        """Return metadata for an existing object."""

    def delete_object(self, key: str) -> None:
        """Delete an object."""

    def create_presigned_upload_url(
        self,
        key: str,
        content_type: str,
        ttl_seconds: int,
    ) -> str:
        """Return a presigned upload URL."""


@dataclass
class LocalMemoryStorageBackend:
    """In-memory storage for unit tests only."""

    prefix: str = "test/"
    _objects: dict[str, tuple[bytes, str]] = field(default_factory=dict)

    def _full_key(self, key: str) -> str:
        return f"{self.prefix.rstrip('/')}/{key.lstrip('/')}"

    def put_object(
        self,
        key: str,
        data: bytes,
        content_type: str,
    ) -> ObjectMetadata:
        full_key = self._full_key(key)
        self._objects[full_key] = (data, content_type)
        return ObjectMetadata(
            key=full_key,
            size_bytes=len(data),
            content_type=content_type,
        )

    def get_object_metadata(self, key: str) -> ObjectMetadata:
        full_key = self._full_key(key)
        if full_key not in self._objects:
            raise StorageError(f"Object not found: {key}", "storage_not_found")
        data, content_type = self._objects[full_key]
        return ObjectMetadata(
            key=full_key,
            size_bytes=len(data),
            content_type=content_type,
        )

    def delete_object(self, key: str) -> None:
        full_key = self._full_key(key)
        if full_key not in self._objects:
            raise StorageError(f"Object not found: {key}", "storage_not_found")
        del self._objects[full_key]

    def create_presigned_upload_url(
        self,
        key: str,
        content_type: str,
        ttl_seconds: int,
    ) -> str:
        full_key = self._full_key(key)
        return (
            f"memory://upload/{full_key}?content_type={content_type}&ttl={ttl_seconds}"
        )


class DisabledProductionStorageBackend:
    """Fail-closed storage when production-saas lacks a real provider adapter."""

    def __init__(self, reason: str) -> None:
        self._reason = reason

    def _fail(self) -> None:
        raise StorageError(self._reason, "storage_not_configured")

    def put_object(self, key: str, data: bytes, content_type: str) -> ObjectMetadata:
        self._fail()
        raise AssertionError("unreachable")

    def get_object_metadata(self, key: str) -> ObjectMetadata:
        self._fail()
        raise AssertionError("unreachable")

    def delete_object(self, key: str) -> None:
        self._fail()

    def create_presigned_upload_url(
        self,
        key: str,
        content_type: str,
        ttl_seconds: int,
    ) -> str:
        self._fail()
        raise AssertionError("unreachable")


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


def build_storage_backend(settings: Settings) -> StorageBackend:
    validate_storage_settings(settings)
    backend = settings.file_storage_backend.strip().lower()
    if settings.is_local_lab:
        prefix = settings.object_storage_prefix or "local/"
        return LocalMemoryStorageBackend(prefix=prefix)
    if settings.is_production_saas:
        return DisabledProductionStorageBackend(
            reason=(
                f"Object storage adapter for {backend} is not implemented; "
                "configure a managed provider adapter before production use"
            )
        )
    return LocalMemoryStorageBackend(prefix=settings.object_storage_prefix or "test/")
