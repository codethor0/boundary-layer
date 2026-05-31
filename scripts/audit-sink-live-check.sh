#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "BoundaryLayer audit sink live check"

if [[ "${RUN_LIVE_STAGING_CHECKS:-}" != "true" ]]; then
  echo "AUDIT SINK LIVE CHECK SKIPPED (RUN_LIVE_STAGING_CHECKS not true)"
  exit 0
fi

provider="${AUDIT_SINK_PROVIDER:-postgres}"
if [[ -z "$provider" ]]; then
  echo "AUDIT SINK LIVE CHECK SKIPPED (AUDIT_SINK_PROVIDER not set)"
  exit 0
fi

if [[ "$provider" != "postgres" && -z "${AUDIT_EXPORT_ENDPOINT:-}" ]]; then
  echo "AUDIT SINK LIVE CHECK SKIPPED (external sink $provider not configured)"
  exit 0
fi

.venv/bin/python - <<'PY'
import os
import sys

from apps.api.audit_export import AuditExportEvent, build_audit_sink, export_audit_event
from apps.api.config_check import _settings_kwargs
from apps.api import config

if os.environ.get("RUN_LIVE_STAGING_CHECKS") != "true":
    print("AUDIT SINK LIVE CHECK SKIPPED")
    sys.exit(0)

kwargs = _settings_kwargs(dict(os.environ))
settings = config.Settings(_env_file=None, **kwargs)
sink = build_audit_sink(settings)
if not sink.health_check():
    print("FAIL audit sink health_check")
    sys.exit(1)

event = AuditExportEvent(
    tenant_id="staging-health",
    actor="evidence-runner",
    action="audit.live_check",
    result="allow",
    metadata={"check": "live"},
)
try:
    export_audit_event(settings, event)
except Exception as exc:
    print(f"FAIL audit export: {type(exc).__name__}")
    sys.exit(1)

print("PASS audit event exported (values redacted)")
print("AUDIT SINK LIVE CHECK PASS")
PY
