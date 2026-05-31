"""Audit export sink unit tests."""

import pytest

from apps.api.audit_export import (
    AuditExportError,
    AuditExportEvent,
    DisabledExternalAuditSink,
    LocalPostgresAuditSink,
    build_audit_sink,
)
from tests.helpers.auth_tenancy import production_saas_settings


def test_local_postgres_audit_sink_health_check():
    sink = LocalPostgresAuditSink()
    assert sink.health_check() is True


def test_external_audit_sink_fails_closed():
    sink = DisabledExternalAuditSink("splunk")
    event = AuditExportEvent(
        tenant_id="tenant-a",
        actor="user-1",
        action="auth.decision",
        result="deny",
    )
    with pytest.raises(AuditExportError, match="not implemented"):
        sink.export_event(event)


def test_build_audit_sink_uses_postgres_by_default():
    settings = production_saas_settings()
    sink = build_audit_sink(settings)
    assert isinstance(sink, LocalPostgresAuditSink)


def test_build_audit_sink_external_shell():
    settings = production_saas_settings(AUDIT_SINK_PROVIDER="datadog")
    sink = build_audit_sink(settings)
    assert isinstance(sink, DisabledExternalAuditSink)


def test_audit_event_fields():
    event = AuditExportEvent(
        tenant_id="tenant-a",
        actor="user-1",
        action="cross_tenant.denied",
        result="deny",
        resource_type="lab",
        resource_id="redis",
        metadata={"reason": "tenant_mismatch"},
    )
    assert event.tenant_id == "tenant-a"
    assert event.normalized_timestamp() is not None
