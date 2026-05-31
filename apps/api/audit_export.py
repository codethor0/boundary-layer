"""Audit export sink abstraction for Production SaaS."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from apps.api.config import Settings
from apps.api.tenancy import insert_audit_event

logger = logging.getLogger("boundary_layer.api.audit_export")

SUPPORTED_EXTERNAL_AUDIT_SINKS = frozenset(
    {"splunk", "datadog", "cloudwatch", "gcp_logging", "azure_monitor", "s3"}
)


class AuditExportError(Exception):
    def __init__(self, message: str, code: str = "audit_export_error"):
        super().__init__(message)
        self.message = message
        self.code = code


@dataclass(frozen=True)
class AuditExportEvent:
    tenant_id: str | None
    actor: str | None
    action: str
    result: str
    resource_type: str | None = None
    resource_id: str | None = None
    metadata: dict[str, Any] | None = None
    timestamp: datetime | None = None

    def normalized_timestamp(self) -> datetime:
        return self.timestamp or datetime.now(UTC)


class AuditSink(Protocol):
    def export_event(self, event: AuditExportEvent) -> None:
        """Export one audit event."""

    def health_check(self) -> bool:
        """Return True when the sink is reachable."""


class LocalPostgresAuditSink:
    """Write audit events to the local Postgres audit_events table."""

    def export_event(self, event: AuditExportEvent) -> None:
        metadata = dict(event.metadata or {})
        metadata["exported_at"] = event.normalized_timestamp().isoformat()
        insert_audit_event(
            action=event.action,
            result=event.result,
            tenant_id=event.tenant_id,
            actor_subject=event.actor,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            metadata=metadata,
        )

    def health_check(self) -> bool:
        return True


class DisabledExternalAuditSink:
    """Fail closed when an external immutable sink is configured but not implemented."""

    def __init__(self, provider: str) -> None:
        self._provider = provider

    def export_event(self, event: AuditExportEvent) -> None:
        logger.warning(
            "Audit export blocked for action=%s via unconfigured sink %s",
            event.action,
            self._provider,
        )
        raise AuditExportError(
            f"External audit sink adapter for {self._provider} is not implemented",
            "audit_sink_not_configured",
        )

    def health_check(self) -> bool:
        return False


class _LazyExternalAuditSink(DisabledExternalAuditSink):
    """Placeholder shell for future HTTP/SDK-backed audit sinks."""


def build_audit_sink(settings: Settings) -> AuditSink:
    provider = settings.audit_sink_provider.strip().lower() or "postgres"
    if provider == "postgres":
        return LocalPostgresAuditSink()
    if provider in SUPPORTED_EXTERNAL_AUDIT_SINKS:
        return _LazyExternalAuditSink(provider)
    raise AuditExportError(
        f"Unsupported AUDIT_SINK_PROVIDER: {provider}",
        "audit_sink_invalid",
    )


def export_audit_event(settings: Settings, event: AuditExportEvent) -> None:
    sink = build_audit_sink(settings)
    sink.export_event(event)
