"""Flat AuthN/AuthZ Lab."""

RESTRICTED_TOOL = "export_customer_pii"
REQUIRED_SCOPE = "pii:export"
REQUIRED_TENANT = "tenant-a"


def _check_access_vulnerable(token: dict, tool: str) -> bool:
    return bool(token.get("authenticated"))


def _check_access_hardened(token: dict, tool: str) -> tuple[bool, str]:
    if not token.get("authenticated"):
        return False, "missing authentication"
    scopes = token.get("scopes", [])
    if REQUIRED_SCOPE not in scopes:
        return False, f"missing required scope: {REQUIRED_SCOPE}"
    if token.get("tenant_id") != REQUIRED_TENANT:
        return False, f"tenant mismatch: expected {REQUIRED_TENANT}"
    return True, "scope and tenant verified"


def run_authz_lab(mode: str) -> dict:
    events: list[str] = []
    broad_token = {
        "authenticated": True,
        "user_id": "user-99",
        "tenant_id": "tenant-b",
        "scopes": ["read:basic"],
    }
    events.append(f"Presented broad token for tool: {RESTRICTED_TOOL}")
    events.append(f"Token scopes: {broad_token['scopes']}")
    events.append(f"Token tenant: {broad_token['tenant_id']}")

    if mode == "vulnerable":
        allowed = _check_access_vulnerable(broad_token, RESTRICTED_TOOL)
        if allowed:
            events.append("Flat auth check passed; restricted tool invoked")
        return {
            "lab": "authz",
            "mode": mode,
            "blocked": not allowed,
            "risk": "Horizontal privilege escalation via flat authorization",
            "control": "none",
            "events": events,
            "summary": (
                "Vulnerable mode allowed export_customer_pii with a broad "
                "authenticated token lacking tenant and scope checks."
            ),
        }

    allowed, reason = _check_access_hardened(broad_token, RESTRICTED_TOOL)
    if not allowed:
        events.append(f"Authorization denied: {reason}")
    return {
        "lab": "authz",
        "mode": mode,
        "blocked": not allowed,
        "risk": "Horizontal privilege escalation via flat authorization",
        "control": "explicit scope and tenant match enforcement",
        "events": events,
        "summary": (f"Hardened mode blocked restricted tool access: {reason}."),
    }
