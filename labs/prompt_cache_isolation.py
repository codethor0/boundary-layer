"""Prompt Cache Isolation Lab."""

import hashlib
import json
import os

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_DB = int(os.environ.get("REDIS_DB", "0"))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "")
CACHE_KEY_PREFIX = "boundary_layer:lab:prompt_cache:"
REDIS_TTL_SECONDS = 300

DEFAULT_TENANT_A = "tenant-a"
DEFAULT_TENANT_B = "tenant-b"
DEFAULT_PROMPT_PREFIX = "summarize confidential acquisition plan"
MAX_TENANT_LEN = 64
MAX_PREFIX_LEN = 256

RISK = "Cross-tenant prompt-prefix cache bleed via shared cache keys"
HARDENED_CONTROL = "per-tenant cache namespace isolation"


def _validate_tenant(tenant: str, field_name: str) -> None:
    if not tenant or not tenant.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if len(tenant) > MAX_TENANT_LEN:
        raise ValueError(f"{field_name} must be at most {MAX_TENANT_LEN} characters")


def _validate_prompt_prefix(prompt_prefix: str) -> None:
    if not prompt_prefix or not prompt_prefix.strip():
        raise ValueError("prompt_prefix must be a non-empty string")
    if len(prompt_prefix) > MAX_PREFIX_LEN:
        raise ValueError(f"prompt_prefix must be at most {MAX_PREFIX_LEN} characters")


def _hash_prompt_prefix(prompt_prefix: str) -> str:
    return hashlib.sha256(prompt_prefix.encode()).hexdigest()[:16]


def global_cache_key(prompt_prefix: str) -> str:
    prefix_hash = _hash_prompt_prefix(prompt_prefix)
    return f"{CACHE_KEY_PREFIX}global:{prefix_hash}"


def tenant_cache_key(tenant_id: str, prompt_prefix: str) -> str:
    prefix_hash = _hash_prompt_prefix(prompt_prefix)
    return f"{CACHE_KEY_PREFIX}{tenant_id}:{prefix_hash}"


def _cache_payload(tenant_id: str, prompt_prefix: str) -> str:
    return json.dumps(
        {
            "tenant_id": tenant_id,
            "prompt_prefix": prompt_prefix,
            "synthetic": True,
        }
    )


def redis_live_enabled() -> bool:
    return os.environ.get("BOUNDARY_LAYER_REDIS_LIVE", "false").lower() == "true"


def _get_redis_client():
    from apps.api.redis_client import get_redis_client

    client = get_redis_client()
    client.ping()
    return client


def _run_fallback(
    mode: str,
    tenant_a: str,
    tenant_b: str,
    prompt_prefix: str,
) -> dict:
    events: list[str] = []
    events.append("Using deterministic in-memory Redis fallback (live mode disabled)")
    store: dict[str, str] = {}
    tenant_a_key = global_cache_key(prompt_prefix)
    tenant_b_key = global_cache_key(prompt_prefix)
    cache_key_mode = "global"

    if mode == "vulnerable":
        store[tenant_a_key] = _cache_payload(tenant_a, prompt_prefix)
        events.append(f"Tenant A wrote shared cache key: {tenant_a_key}")
        events.append(f"Tenant B queried same shared cache key: {tenant_b_key}")
        cache_hit = tenant_b_key in store
        events.append("No tenant namespace applied")
        if cache_hit:
            events.append("Cross-tenant cache hit detected")
        events.append("Cache bleed risk recorded")
        return {
            "lab": "prompt-cache-isolation",
            "mode": mode,
            "blocked": False,
            "risk": RISK,
            "control": "none",
            "events": events,
            "summary": (
                "Vulnerable mode allowed Tenant B to hit Tenant A's "
                "shared prompt cache entry."
            ),
            "_metrics_tenant_a": tenant_a,
            "_metrics_tenant_b": tenant_b,
            "_tenant_a_cache_key": tenant_a_key,
            "_tenant_b_cache_key": tenant_b_key,
            "_cache_key_mode": cache_key_mode,
            "_tenant_b_hit_type": "cross_tenant" if cache_hit else "miss",
            "_cache_hit_cross_tenant": cache_hit,
            "_cache_bleed_detected": cache_hit,
            "_isolation_applied": False,
        }

    tenant_a_key = tenant_cache_key(tenant_a, prompt_prefix)
    tenant_b_key = tenant_cache_key(tenant_b, prompt_prefix)
    cache_key_mode = "tenant_scoped"
    store[tenant_a_key] = _cache_payload(tenant_a, prompt_prefix)
    events.append(f"Tenant A wrote tenant-scoped cache key: {tenant_a_key}")
    events.append(f"Tenant B queried tenant-scoped cache key: {tenant_b_key}")
    cache_hit = tenant_b_key in store
    events.append("Tenant namespace isolation applied")
    if not cache_hit:
        events.append("No cross-tenant cache hit detected")
    events.append("Cache bleed prevented")
    return {
        "lab": "prompt-cache-isolation",
        "mode": mode,
        "blocked": True,
        "risk": RISK,
        "control": HARDENED_CONTROL,
        "events": events,
        "summary": (
            "Hardened mode prevented cross-tenant prompt cache bleed "
            "using tenant namespaces."
        ),
        "_metrics_tenant_a": tenant_a,
        "_metrics_tenant_b": tenant_b,
        "_tenant_a_cache_key": tenant_a_key,
        "_tenant_b_cache_key": tenant_b_key,
        "_cache_key_mode": cache_key_mode,
        "_tenant_b_hit_type": "tenant_scoped" if cache_hit else "miss",
        "_cache_hit_cross_tenant": False,
        "_cache_bleed_detected": False,
        "_isolation_applied": True,
    }


def _run_live(
    mode: str,
    tenant_a: str,
    tenant_b: str,
    prompt_prefix: str,
) -> dict:
    events: list[str] = []
    try:
        client = _get_redis_client()
    except Exception as exc:
        raise RuntimeError(
            "Redis is unavailable but BOUNDARY_LAYER_REDIS_LIVE=true. "
            f"Check REDIS_HOST={REDIS_HOST} REDIS_PORT={REDIS_PORT}. "
            f"Error: {exc}"
        ) from exc

    events.append(f"Connected to live Redis at {REDIS_HOST}:{REDIS_PORT}")
    payload = _cache_payload(tenant_a, prompt_prefix)

    if mode == "vulnerable":
        tenant_a_key = global_cache_key(prompt_prefix)
        tenant_b_key = global_cache_key(prompt_prefix)
        client.setex(tenant_a_key, REDIS_TTL_SECONDS, payload)
        events.append(f"Tenant A wrote shared cache key: {tenant_a_key}")
        events.append(f"Tenant B queried same shared cache key: {tenant_b_key}")
        stored = client.get(tenant_b_key)
        cache_hit = stored is not None
        events.append("No tenant namespace applied")
        if cache_hit:
            events.append("Cross-tenant cache hit detected")
        events.append("Cache bleed risk recorded")
        return {
            "lab": "prompt-cache-isolation",
            "mode": mode,
            "blocked": False,
            "risk": RISK,
            "control": "none",
            "events": events,
            "summary": (
                "Vulnerable mode allowed Tenant B to hit Tenant A's "
                "shared Redis cache entry."
            ),
            "_metrics_tenant_a": tenant_a,
            "_metrics_tenant_b": tenant_b,
            "_tenant_a_cache_key": tenant_a_key,
            "_tenant_b_cache_key": tenant_b_key,
            "_cache_key_mode": "global",
            "_tenant_b_hit_type": "cross_tenant" if cache_hit else "miss",
            "_cache_hit_cross_tenant": cache_hit,
            "_cache_bleed_detected": cache_hit,
            "_isolation_applied": False,
        }

    tenant_a_key = tenant_cache_key(tenant_a, prompt_prefix)
    tenant_b_key = tenant_cache_key(tenant_b, prompt_prefix)
    client.setex(tenant_a_key, REDIS_TTL_SECONDS, payload)
    events.append(f"Tenant A wrote tenant-scoped cache key: {tenant_a_key}")
    events.append(f"Tenant B queried tenant-scoped cache key: {tenant_b_key}")
    stored = client.get(tenant_b_key)
    cache_hit = stored is not None
    events.append("Tenant namespace isolation applied")
    if not cache_hit:
        events.append("No cross-tenant cache hit detected")
    events.append("Cache bleed prevented")
    return {
        "lab": "prompt-cache-isolation",
        "mode": mode,
        "blocked": True,
        "risk": RISK,
        "control": HARDENED_CONTROL,
        "events": events,
        "summary": (
            "Hardened mode prevented cross-tenant prompt cache bleed in Redis."
        ),
        "_metrics_tenant_a": tenant_a,
        "_metrics_tenant_b": tenant_b,
        "_tenant_a_cache_key": tenant_a_key,
        "_tenant_b_cache_key": tenant_b_key,
        "_cache_key_mode": "tenant_scoped",
        "_tenant_b_hit_type": "tenant_scoped" if cache_hit else "miss",
        "_cache_hit_cross_tenant": False,
        "_cache_bleed_detected": False,
        "_isolation_applied": True,
    }


def run_prompt_cache_isolation_lab(
    mode: str,
    tenant_a: str = DEFAULT_TENANT_A,
    tenant_b: str = DEFAULT_TENANT_B,
    prompt_prefix: str = DEFAULT_PROMPT_PREFIX,
) -> dict:
    _validate_tenant(tenant_a, "tenant_a")
    _validate_tenant(tenant_b, "tenant_b")
    _validate_prompt_prefix(prompt_prefix)
    if redis_live_enabled():
        return _run_live(mode, tenant_a, tenant_b, prompt_prefix)
    return _run_fallback(mode, tenant_a, tenant_b, prompt_prefix)
