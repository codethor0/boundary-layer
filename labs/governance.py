"""Prompt Governance Tracker Lab."""

from dataclasses import dataclass, field

from apps.api.db import (
    check_postgres_connection,
    count_orphan_records,
    create_prompt_lifecycle_records,
    delete_all_prompt_lifecycle_records,
    delete_primary_only,
    init_db,
    insert_deletion_audit,
    postgres_live_enabled,
    reset_governance_lab_records,
)

GOVERNANCE_RISK = "Incomplete prompt deletion leaves retrievable downstream artifacts"
HARDENED_CONTROL = "downstream dependency audit and cascade deletion evidence"


@dataclass
class PromptRecord:
    prompt_id: str
    content: str
    request_records: list[str] = field(default_factory=list)
    log_records: list[str] = field(default_factory=list)
    tool_records: list[str] = field(default_factory=list)
    eval_queue: list[str] = field(default_factory=list)
    training_queue: list[str] = field(default_factory=list)


def _build_sample_prompt() -> PromptRecord:
    return PromptRecord(
        prompt_id="prompt-001",
        content="Summarize customer feedback for product team.",
        request_records=["req-100", "req-101"],
        log_records=["log-200", "log-201"],
        tool_records=["tool-300"],
        eval_queue=["eval-400"],
        training_queue=["train-500"],
    )


def _delete_vulnerable(record: PromptRecord) -> dict:
    deleted_primary = record.prompt_id
    remaining = {
        "request_records": len(record.request_records),
        "log_records": len(record.log_records),
        "tool_records": len(record.tool_records),
        "eval_queue": len(record.eval_queue),
        "training_queue": len(record.training_queue),
    }
    return {
        "deleted": [deleted_primary],
        "orphaned": remaining,
        "audit_evidence": [],
    }


def _delete_hardened(record: PromptRecord) -> dict:
    checks = {
        "request_records": record.request_records,
        "log_records": record.log_records,
        "tool_records": record.tool_records,
        "eval_queue": record.eval_queue,
        "training_queue": record.training_queue,
    }
    audit = []
    deleted = []
    orphaned = {}

    for category, items in checks.items():
        if items:
            audit.append(f"Checked {category}: {len(items)} dependent records")
            for item in items:
                deleted.append(f"{category}:{item}")
        else:
            audit.append(f"Checked {category}: 0 records")

    deleted.append(f"primary:{record.prompt_id}")
    audit.append("Cascade deletion plan recorded in audit log entry audit-9001")

    for category, items in checks.items():
        orphaned[category] = 0

    return {
        "deleted": deleted,
        "orphaned": orphaned,
        "audit_evidence": audit,
    }


def _run_governance_fallback(mode: str) -> dict:
    events: list[str] = []
    events.append(
        "Using deterministic in-memory PostgreSQL fallback (live mode disabled)"
    )
    record = _build_sample_prompt()
    events.append(f"Prompt record loaded: {record.prompt_id}")
    events.append(
        f"Downstream records: requests={len(record.request_records)}, "
        f"logs={len(record.log_records)}, tools={len(record.tool_records)}, "
        f"eval={len(record.eval_queue)}, training={len(record.training_queue)}"
    )

    if mode == "vulnerable":
        result = _delete_vulnerable(record)
        events.append(f"Deleted primary prompt: {record.prompt_id}")
        for cat, count in result["orphaned"].items():
            if count > 0:
                events.append(f"Orphaned {cat}: {count} records remain")
        orphan_count = sum(result["orphaned"].values())
        return {
            "lab": "governance",
            "mode": mode,
            "blocked": False,
            "risk": GOVERNANCE_RISK,
            "control": "none",
            "events": events,
            "summary": (
                "Vulnerable deletion removed only the primary prompt; "
                f"{orphan_count} downstream records orphaned."
            ),
            "_orphan_count": orphan_count,
        }

    result = _delete_hardened(record)
    for line in result["audit_evidence"]:
        events.append(line)
    events.append(f"Cascade deleted {len(result['deleted'])} total artifacts")
    return {
        "lab": "governance",
        "mode": mode,
        "blocked": True,
        "risk": GOVERNANCE_RISK,
        "control": HARDENED_CONTROL,
        "events": events,
        "summary": (
            "Hardened deletion audited all downstream queues and produced "
            f"cascade evidence for {len(result['deleted'])} artifacts."
        ),
        "_orphan_count": 0,
        "_audit_complete": True,
    }


def _run_governance_live(mode: str) -> dict:
    events: list[str] = []
    try:
        check_postgres_connection()
        init_db()
    except Exception as exc:
        raise RuntimeError(
            "PostgreSQL is unavailable but BOUNDARY_LAYER_POSTGRES_LIVE=true. "
            f"Check POSTGRES_HOST and credentials. Error: {exc}"
        ) from exc

    from apps.api.db import POSTGRES_HOST, POSTGRES_PORT

    events.append(f"Connected to live PostgreSQL at {POSTGRES_HOST}:{POSTGRES_PORT}")
    reset_governance_lab_records()
    events.append("Created prompt lifecycle records")
    prompt_id = create_prompt_lifecycle_records()
    events.append(f"Primary prompt request stored: {prompt_id}")

    if mode == "vulnerable":
        delete_primary_only(prompt_id)
        events.append("Deleted primary prompt record only")
        orphan_count = count_orphan_records(prompt_id)
        events.append(f"Detected {orphan_count} orphaned downstream records")
        return {
            "lab": "governance",
            "mode": mode,
            "blocked": False,
            "risk": GOVERNANCE_RISK,
            "control": "none",
            "events": events,
            "summary": (
                "Vulnerable deletion removed only the primary prompt request; "
                f"{orphan_count} downstream PostgreSQL records orphaned."
            ),
            "_orphan_count": orphan_count,
        }

    delete_all_prompt_lifecycle_records(prompt_id)
    events.append("Deleted all prompt lifecycle downstream records")
    orphan_count = count_orphan_records(prompt_id)
    events.append(f"Detected {orphan_count} orphaned downstream records")
    audit_id = insert_deletion_audit(
        prompt_id, mode, orphan_count, complete=orphan_count == 0
    )
    events.append(f"Inserted deletion audit record: {audit_id}")
    events.append("Deletion propagation completed across downstream tables")
    return {
        "lab": "governance",
        "mode": mode,
        "blocked": True,
        "risk": GOVERNANCE_RISK,
        "control": HARDENED_CONTROL,
        "events": events,
        "summary": (
            "Hardened deletion cascade completed in PostgreSQL with "
            f"{orphan_count} orphaned records remaining."
        ),
        "_orphan_count": orphan_count,
        "_audit_complete": orphan_count == 0,
    }


def run_governance_lab(mode: str) -> dict:
    if postgres_live_enabled():
        return _run_governance_live(mode)
    return _run_governance_fallback(mode)
