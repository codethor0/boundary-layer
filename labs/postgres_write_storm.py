"""PostgreSQL Write Storm Lab."""

import time
import uuid

from apps.api.db import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    check_postgres_connection,
    count_write_storm_events,
    init_db,
    insert_write_storm_events,
    postgres_live_enabled,
    reset_write_storm_events,
)

DEFAULT_REQUESTED_WRITES = 250
HARDENED_WRITE_BUDGET = 50
MIN_REQUESTED_WRITES = 1
MAX_REQUESTED_WRITES = 1000

RISK = "PostgreSQL primary write-path saturation from runaway prompt logging"
HARDENED_CONTROL = "tenant write budget and backpressure on synthetic write batches"


def _validate_requested_writes(requested_writes: int) -> None:
    if (
        requested_writes < MIN_REQUESTED_WRITES
        or requested_writes > MAX_REQUESTED_WRITES
    ):
        raise ValueError(
            f"requested_writes must be between {MIN_REQUESTED_WRITES} and "
            f"{MAX_REQUESTED_WRITES}"
        )


def _run_write_storm_fallback(mode: str, requested_writes: int) -> dict:
    events: list[str] = []
    events.append(
        "Using deterministic in-memory PostgreSQL fallback (live mode disabled)"
    )
    events.append(f"Requested write batch size: {requested_writes}")

    if mode == "vulnerable":
        inserted = requested_writes
        blocked = 0
        events.append(f"Created synthetic write storm batch ({inserted} events)")
        events.append("No write throttle applied")
        events.append("Write pressure risk recorded")
        duration = 0.001
        return {
            "lab": "postgres-write-storm",
            "mode": mode,
            "blocked": False,
            "risk": RISK,
            "control": "none",
            "events": events,
            "summary": (
                f"Vulnerable mode inserted {inserted} synthetic write events "
                "without throttling."
            ),
            "_inserted_count": inserted,
            "_blocked_writes_count": blocked,
            "_insert_duration_seconds": duration,
            "_insert_result": "inserted",
        }

    allowed = min(requested_writes, HARDENED_WRITE_BUDGET)
    blocked = requested_writes - allowed
    events.append(f"Applied tenant write budget: {HARDENED_WRITE_BUDGET}")
    events.append(f"Inserted allowed records: {allowed}")
    events.append(f"Blocked excess records: {blocked}")
    events.append("Emitted write storm mitigation metrics")
    duration = 0.001
    return {
        "lab": "postgres-write-storm",
        "mode": mode,
        "blocked": True,
        "risk": RISK,
        "control": HARDENED_CONTROL,
        "events": events,
        "summary": (
            f"Hardened mode capped inserts at {allowed} and blocked {blocked} "
            "excess synthetic write events."
        ),
        "_inserted_count": allowed,
        "_blocked_writes_count": blocked,
        "_insert_duration_seconds": duration,
        "_insert_result": "inserted",
    }


def _run_write_storm_live(mode: str, requested_writes: int) -> dict:
    events: list[str] = []
    try:
        check_postgres_connection()
        init_db()
    except Exception as exc:
        raise RuntimeError(
            "PostgreSQL is unavailable but BOUNDARY_LAYER_POSTGRES_LIVE=true. "
            f"Check POSTGRES_HOST and credentials. Error: {exc}"
        ) from exc

    events.append(f"Connected to live PostgreSQL at {POSTGRES_HOST}:{POSTGRES_PORT}")
    events.append(f"Requested write batch size: {requested_writes}")
    reset_write_storm_events()
    events.append("Created synthetic write storm batch")

    batch_id = uuid.uuid4().hex[:12]
    start = time.perf_counter()

    if mode == "vulnerable":
        inserted = insert_write_storm_events(requested_writes, batch_id)
        blocked = 0
        events.append(f"Inserted {inserted} write_storm_events")
        events.append("No write throttle applied")
        events.append("Write pressure risk recorded")
        duration = time.perf_counter() - start
        total = count_write_storm_events()
        events.append(f"PostgreSQL write_storm_events row count: {total}")
        return {
            "lab": "postgres-write-storm",
            "mode": mode,
            "blocked": False,
            "risk": RISK,
            "control": "none",
            "events": events,
            "summary": (
                f"Vulnerable mode inserted {inserted} synthetic PostgreSQL write "
                "events without throttling."
            ),
            "_inserted_count": inserted,
            "_blocked_writes_count": blocked,
            "_insert_duration_seconds": duration,
            "_insert_result": "inserted",
        }

    allowed = min(requested_writes, HARDENED_WRITE_BUDGET)
    blocked = requested_writes - allowed
    events.append(f"Applied tenant write budget: {HARDENED_WRITE_BUDGET}")
    inserted = insert_write_storm_events(allowed, batch_id)
    events.append(f"Inserted allowed records: {inserted}")
    events.append(f"Blocked excess records: {blocked}")
    events.append("Emitted write storm mitigation metrics")
    duration = time.perf_counter() - start
    total = count_write_storm_events()
    events.append(f"PostgreSQL write_storm_events row count: {total}")
    return {
        "lab": "postgres-write-storm",
        "mode": mode,
        "blocked": True,
        "risk": RISK,
        "control": HARDENED_CONTROL,
        "events": events,
        "summary": (
            f"Hardened mode inserted {inserted} events and blocked {blocked} "
            "excess synthetic writes."
        ),
        "_inserted_count": inserted,
        "_blocked_writes_count": blocked,
        "_insert_duration_seconds": duration,
        "_insert_result": "inserted",
    }


def run_postgres_write_storm_lab(
    mode: str,
    requested_writes: int = DEFAULT_REQUESTED_WRITES,
) -> dict:
    _validate_requested_writes(requested_writes)
    if postgres_live_enabled():
        return _run_write_storm_live(mode, requested_writes)
    return _run_write_storm_fallback(mode, requested_writes)
