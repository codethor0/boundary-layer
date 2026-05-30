"""SSE Exhaustion Simulation Lab."""

DEFAULT_REQUESTED_STREAMS = 250
MIN_REQUESTED_STREAMS = 1
MAX_REQUESTED_STREAMS = 1000
DEFAULT_STREAM_DURATION_SECONDS = 120
MIN_STREAM_DURATION_SECONDS = 1
MAX_STREAM_DURATION_SECONDS = 3600
MAX_STREAMS_PER_TENANT = 50
IDLE_TIMEOUT_SECONDS = 30
WORKER_PRESSURE_THRESHOLD = 100

RISK = "Streaming resource exhaustion from unbounded SSE connections"
HARDENED_CONTROL = (
    "tenant stream cap, idle timeout, and cleanup for synthetic SSE streams"
)


def _validate_requested_streams(requested_streams: int) -> None:
    if (
        requested_streams < MIN_REQUESTED_STREAMS
        or requested_streams > MAX_REQUESTED_STREAMS
    ):
        raise ValueError(
            f"requested_streams must be between {MIN_REQUESTED_STREAMS} "
            f"and {MAX_REQUESTED_STREAMS}"
        )


def _validate_stream_duration(stream_duration_seconds: int) -> None:
    if (
        stream_duration_seconds < MIN_STREAM_DURATION_SECONDS
        or stream_duration_seconds > MAX_STREAM_DURATION_SECONDS
    ):
        raise ValueError(
            f"stream_duration_seconds must be between "
            f"{MIN_STREAM_DURATION_SECONDS} and {MAX_STREAM_DURATION_SECONDS}"
        )


def _simulate_active_streams(accepted_streams: int) -> int:
    return accepted_streams


def _simulate_orphaned_streams_vulnerable(accepted_streams: int) -> int:
    return max(0, accepted_streams - MAX_STREAMS_PER_TENANT)


def _simulate_worker_pressure(active_streams: int) -> int:
    return active_streams


def _simulate_memory_pressure_mb(
    active_streams: int,
    stream_duration_seconds: int,
) -> int:
    return (active_streams * stream_duration_seconds) // 60


def run_sse_exhaustion_lab(
    mode: str,
    requested_streams: int = DEFAULT_REQUESTED_STREAMS,
    stream_duration_seconds: int = DEFAULT_STREAM_DURATION_SECONDS,
) -> dict:
    _validate_requested_streams(requested_streams)
    _validate_stream_duration(stream_duration_seconds)

    events: list[str] = []
    events.append(f"Requested stream count: {requested_streams}")
    events.append(f"Stream duration seconds: {stream_duration_seconds}")

    if mode == "vulnerable":
        accepted = requested_streams
        rejected = 0
        active_streams = _simulate_active_streams(accepted)
        orphaned_streams = _simulate_orphaned_streams_vulnerable(accepted)
        worker_pressure = _simulate_worker_pressure(active_streams)
        memory_pressure_mb = _simulate_memory_pressure_mb(
            active_streams,
            stream_duration_seconds,
        )
        cleanup_applied = False

        events.append(f"Accepted all requested streams: {accepted}")
        events.append("No stream cap applied")
        events.append("No idle timeout applied")
        events.append("No cleanup applied")
        events.append(f"Simulated orphaned streams created: {orphaned_streams}")
        events.append(
            f"Simulated worker pressure: {worker_pressure} "
            f"(threshold: {WORKER_PRESSURE_THRESHOLD})"
        )
        events.append(f"Simulated memory pressure: {memory_pressure_mb} MB")
        events.append("Worker pressure risk recorded")
        events.append("Memory pressure risk recorded")

        return {
            "lab": "sse-exhaustion",
            "mode": mode,
            "blocked": False,
            "risk": RISK,
            "control": "none",
            "events": events,
            "summary": (
                f"Vulnerable mode accepted all {accepted} synthetic SSE streams "
                "without caps or cleanup."
            ),
            "_requested_streams": requested_streams,
            "_accepted_streams": accepted,
            "_rejected_streams": rejected,
            "_active_streams": active_streams,
            "_orphaned_streams": orphaned_streams,
            "_worker_pressure": worker_pressure,
            "_memory_pressure_mb": memory_pressure_mb,
            "_cleanup_applied": cleanup_applied,
        }

    if requested_streams > MAX_STREAMS_PER_TENANT:
        accepted = MAX_STREAMS_PER_TENANT
        rejected = requested_streams - MAX_STREAMS_PER_TENANT
        blocked = True
    else:
        accepted = requested_streams
        rejected = 0
        blocked = False

    active_streams = _simulate_active_streams(accepted)
    orphaned_streams = 0
    worker_pressure = _simulate_worker_pressure(active_streams)
    memory_pressure_mb = _simulate_memory_pressure_mb(
        active_streams,
        stream_duration_seconds,
    )
    cleanup_applied = True

    events.append(f"Applied tenant stream cap: {MAX_STREAMS_PER_TENANT}")
    events.append(f"Accepted allowed streams: {accepted}")
    events.append(f"Rejected excess streams: {rejected}")
    events.append(f"Applied idle timeout: {IDLE_TIMEOUT_SECONDS}s")
    events.append("Applied cleanup")
    events.append(f"Simulated orphaned streams after cleanup: {orphaned_streams}")
    events.append("Emitted SSE mitigation metrics")

    return {
        "lab": "sse-exhaustion",
        "mode": mode,
        "blocked": blocked,
        "risk": RISK,
        "control": HARDENED_CONTROL,
        "events": events,
        "summary": (
            f"Hardened mode accepted {accepted} streams, rejected {rejected}, "
            "and applied cleanup controls."
        ),
        "_requested_streams": requested_streams,
        "_accepted_streams": accepted,
        "_rejected_streams": rejected,
        "_active_streams": active_streams,
        "_orphaned_streams": orphaned_streams,
        "_worker_pressure": worker_pressure,
        "_memory_pressure_mb": memory_pressure_mb,
        "_cleanup_applied": cleanup_applied,
    }
