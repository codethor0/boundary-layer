"""Circuit Breaker Simulation Lab."""

DEFAULT_REQUESTED_WORK_UNITS = 250
MIN_REQUESTED_WORK_UNITS = 1
MAX_REQUESTED_WORK_UNITS = 1000
SAFE_CAPACITY = 100
CRITICAL_CAPACITY = 200
SAFE_P99_LATENCY_MS = 500

RISK = "Cascading inference failure from unbounded work acceptance under load"
HARDENED_CONTROL = "circuit breaker and load shedding at safe capacity threshold"


def _validate_requested_work_units(requested_work_units: int) -> None:
    if (
        requested_work_units < MIN_REQUESTED_WORK_UNITS
        or requested_work_units > MAX_REQUESTED_WORK_UNITS
    ):
        raise ValueError(
            f"requested_work_units must be between {MIN_REQUESTED_WORK_UNITS} "
            f"and {MAX_REQUESTED_WORK_UNITS}"
        )


def _simulate_queue_depth(accepted_work_units: int) -> int:
    return accepted_work_units


def _simulate_p99_latency_ms(accepted_work_units: int) -> int:
    return 100 + (accepted_work_units * 2)


def _simulate_failures_vulnerable(requested_work_units: int) -> int:
    if requested_work_units <= CRITICAL_CAPACITY:
        return 0
    return requested_work_units - CRITICAL_CAPACITY


def run_circuit_breaker_lab(
    mode: str,
    requested_work_units: int = DEFAULT_REQUESTED_WORK_UNITS,
) -> dict:
    _validate_requested_work_units(requested_work_units)
    events: list[str] = []
    events.append(f"Requested work units: {requested_work_units}")

    if mode == "vulnerable":
        accepted = requested_work_units
        shed = 0
        circuit_breaker_state = 0
        queue_depth = _simulate_queue_depth(accepted)
        p99_latency_ms = _simulate_p99_latency_ms(accepted)
        simulated_failures = _simulate_failures_vulnerable(requested_work_units)

        events.append(f"Accepted all requested work units: {accepted}")
        events.append("No circuit breaker applied")
        events.append(f"Queue depth increased to {queue_depth}")
        events.append(
            f"Simulated p99 latency: {p99_latency_ms}ms "
            f"(safe threshold: {SAFE_P99_LATENCY_MS}ms)"
        )
        if p99_latency_ms > SAFE_P99_LATENCY_MS:
            events.append("Simulated p99 latency exceeded safe threshold")
        if simulated_failures > 0:
            events.append(
                f"Simulated failure count: {simulated_failures} "
                f"(critical capacity: {CRITICAL_CAPACITY})"
            )
        events.append("Cascading failure risk recorded")

        return {
            "lab": "circuit-breaker",
            "mode": mode,
            "blocked": False,
            "risk": RISK,
            "control": "none",
            "events": events,
            "summary": (
                f"Vulnerable mode accepted all {accepted} synthetic work units "
                "without backpressure."
            ),
            "_circuit_breaker_state": circuit_breaker_state,
            "_requested_work_units": requested_work_units,
            "_accepted_work_units": accepted,
            "_shed_work_units": shed,
            "_simulated_failures": simulated_failures,
            "_queue_depth": queue_depth,
            "_p99_latency_ms": p99_latency_ms,
        }

    if requested_work_units > SAFE_CAPACITY:
        circuit_breaker_state = 1
        accepted = SAFE_CAPACITY
        shed = requested_work_units - SAFE_CAPACITY
        blocked = True
        events.append("Circuit breaker opened: requested work exceeded safe capacity")
    else:
        circuit_breaker_state = 0
        accepted = requested_work_units
        shed = 0
        blocked = False
        events.append("Circuit breaker closed: requested work within safe capacity")

    queue_depth = _simulate_queue_depth(accepted)
    p99_latency_ms = _simulate_p99_latency_ms(accepted)
    simulated_failures = 0

    events.append(f"Accepted safe work units: {accepted}")
    events.append(f"Shed excess work units: {shed}")
    events.append(f"Set circuit breaker state metric: {circuit_breaker_state}")
    events.append("Emitted mitigation metrics")

    return {
        "lab": "circuit-breaker",
        "mode": mode,
        "blocked": blocked,
        "risk": RISK,
        "control": HARDENED_CONTROL,
        "events": events,
        "summary": (
            f"Hardened mode accepted {accepted} work units, shed {shed}, "
            f"circuit breaker state {circuit_breaker_state}."
        ),
        "_circuit_breaker_state": circuit_breaker_state,
        "_requested_work_units": requested_work_units,
        "_accepted_work_units": accepted,
        "_shed_work_units": shed,
        "_simulated_failures": simulated_failures,
        "_queue_depth": queue_depth,
        "_p99_latency_ms": p99_latency_ms,
    }
