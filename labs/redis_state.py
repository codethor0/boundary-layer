"""Redis State Tampering Lab."""

import base64
import hashlib
import hmac
import json
import os
import uuid

SESSION_HMAC_SECRET = os.environ.get(
    "SESSION_HMAC_SECRET", "local-dev-hmac-secret-change-me"
)
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_DB = int(os.environ.get("REDIS_DB", "0"))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "")
REDIS_KEY_PREFIX = "boundary_layer:lab:redis:"
REDIS_TTL_SECONDS = 300

ORIGINAL_SESSION = {
    "user_id": "user-42",
    "role": "viewer",
    "tenant_id": "tenant-a",
}

RISK = "Session privilege escalation via unsigned Redis state tampering"
HMAC_CONTROL = "HMAC session integrity verification"


def _encode_session_vulnerable(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True)
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_session_vulnerable(token: str) -> dict:
    raw = base64.urlsafe_b64decode(token.encode())
    return json.loads(raw.decode())


def _sign_session_hardened(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True)
    sig = hmac.new(
        SESSION_HMAC_SECRET.encode(), raw.encode(), hashlib.sha256
    ).hexdigest()
    envelope = {"payload": payload, "sig": sig}
    return base64.urlsafe_b64encode(json.dumps(envelope).encode()).decode()


def _verify_session_hardened(token: str) -> tuple[dict | None, bool]:
    try:
        envelope = json.loads(base64.urlsafe_b64decode(token.encode()).decode())
        payload = envelope["payload"]
        sig = envelope["sig"]
        raw = json.dumps(payload, sort_keys=True)
        expected = hmac.new(
            SESSION_HMAC_SECRET.encode(), raw.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None, False
        return payload, True
    except (KeyError, json.JSONDecodeError, ValueError):
        return None, False


def _use_live_redis() -> bool:
    return os.environ.get("BOUNDARY_LAYER_REDIS_LIVE", "false").lower() == "true"


def _redis_key() -> str:
    return f"{REDIS_KEY_PREFIX}session:{uuid.uuid4().hex[:12]}"


def _get_redis_client():
    import redis

    client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD or None,
        decode_responses=True,
        socket_connect_timeout=2,
    )
    client.ping()
    return client


def _run_redis_lab_fallback(mode: str) -> dict:
    events: list[str] = []
    events.append("Using deterministic in-memory Redis fallback (live mode disabled)")
    tampered = {**ORIGINAL_SESSION, "role": "admin"}

    if mode == "vulnerable":
        token = _encode_session_vulnerable(ORIGINAL_SESSION)
        events.append(f"Stored unsigned session token: {token[:24]}...")
        tampered_token = _encode_session_vulnerable(tampered)
        events.append("Attacker rewrote session blob in Redis with elevated role")
        decoded = _decode_session_vulnerable(tampered_token)
        events.append(f"Server accepted tampered session role={decoded['role']}")
        return {
            "lab": "redis",
            "mode": mode,
            "blocked": False,
            "risk": RISK,
            "control": "none",
            "events": events,
            "summary": (
                "Vulnerable mode accepted a tampered session blob; "
                f"role escalated from viewer to {decoded['role']}."
            ),
        }

    token = _sign_session_hardened(ORIGINAL_SESSION)
    events.append(f"Stored HMAC-signed session token: {token[:24]}...")
    tampered_token = _encode_session_vulnerable(tampered)
    events.append("Attacker attempted to replace session with unsigned blob")
    payload, valid = _verify_session_hardened(tampered_token)
    if not valid:
        events.append("HMAC verification rejected tampered session payload")
        return {
            "lab": "redis",
            "mode": mode,
            "blocked": True,
            "risk": RISK,
            "control": HMAC_CONTROL,
            "events": events,
            "summary": (
                "Hardened mode rejected tampered session; privilege escalation blocked."
            ),
        }

    events.append("Unexpected: tampered session accepted")
    return {
        "lab": "redis",
        "mode": mode,
        "blocked": False,
        "risk": RISK,
        "control": HMAC_CONTROL,
        "events": events,
        "summary": "Tampered session was incorrectly accepted.",
    }


def _run_redis_lab_live(mode: str) -> dict:
    events: list[str] = []
    tampered = {**ORIGINAL_SESSION, "role": "admin"}
    key = _redis_key()

    try:
        client = _get_redis_client()
    except Exception as exc:
        raise RuntimeError(
            "Redis is unavailable but BOUNDARY_LAYER_REDIS_LIVE=true. "
            f"Check REDIS_HOST={REDIS_HOST} REDIS_PORT={REDIS_PORT}. "
            f"Error: {exc}"
        ) from exc

    events.append(f"Connected to live Redis at {REDIS_HOST}:{REDIS_PORT}")
    events.append(f"Using namespaced key: {key}")

    if mode == "vulnerable":
        token = _encode_session_vulnerable(ORIGINAL_SESSION)
        client.setex(key, REDIS_TTL_SECONDS, token)
        events.append("Stored unsigned session payload in Redis with TTL")
        tampered_token = _encode_session_vulnerable(tampered)
        client.set(key, tampered_token)
        events.append("Attacker overwrote Redis value with tampered unsigned blob")
        stored = client.get(key)
        if stored is None:
            raise RuntimeError(
                f"Expected Redis key missing after tamper simulation: {key}"
            )
        decoded = _decode_session_vulnerable(stored)
        events.append(f"Server accepted tampered session role={decoded['role']}")
        return {
            "lab": "redis",
            "mode": mode,
            "blocked": False,
            "risk": RISK,
            "control": "none",
            "events": events,
            "summary": (
                "Vulnerable mode accepted a tampered Redis session blob; "
                f"role escalated from viewer to {decoded['role']}."
            ),
        }

    token = _sign_session_hardened(ORIGINAL_SESSION)
    client.setex(key, REDIS_TTL_SECONDS, token)
    events.append("Stored HMAC-signed session payload in Redis with TTL")
    tampered_token = _encode_session_vulnerable(tampered)
    client.set(key, tampered_token)
    events.append("Attacker overwrote Redis value with unsigned tampered blob")
    stored = client.get(key)
    if stored is None:
        raise RuntimeError(f"Expected Redis key missing after tamper simulation: {key}")
    payload, valid = _verify_session_hardened(stored)
    if not valid:
        events.append("HMAC verification rejected tampered Redis session payload")
        return {
            "lab": "redis",
            "mode": mode,
            "blocked": True,
            "risk": RISK,
            "control": HMAC_CONTROL,
            "events": events,
            "summary": (
                "Hardened mode rejected tampered Redis session; "
                "privilege escalation blocked."
            ),
        }

    events.append(f"Unexpected: tampered session accepted role={payload['role']}")
    return {
        "lab": "redis",
        "mode": mode,
        "blocked": False,
        "risk": RISK,
        "control": HMAC_CONTROL,
        "events": events,
        "summary": "Tampered Redis session was incorrectly accepted.",
    }


def run_redis_lab(mode: str) -> dict:
    if _use_live_redis():
        return _run_redis_lab_live(mode)
    return _run_redis_lab_fallback(mode)
