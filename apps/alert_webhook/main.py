"""Local Alertmanager webhook receiver for BoundaryLayer validation."""

import secrets
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, status

from apps.alert_webhook.config import get_webhook_settings

app = FastAPI(title="BoundaryLayer Alert Webhook", version="1.1.0")

_stored_alerts: list[dict] = []


def verify_webhook_access(
    authorization: Annotated[str | None, Header()] = None,
    x_webhook_token: Annotated[str | None, Header()] = None,
) -> None:
    settings = get_webhook_settings()
    if not settings.auth_enabled:
        return

    provided = None
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            provided = token.strip()
    if not provided and x_webhook_token:
        provided = x_webhook_token.strip()

    expected = settings.auth_token.strip()
    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing webhook credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/health")
def health():
    settings = get_webhook_settings()
    return {
        "status": "ok",
        "service": "boundary-layer-alert-webhook",
        "auth_enabled": settings.auth_enabled,
    }


@app.post("/alerts", dependencies=[Depends(verify_webhook_access)])
def receive_alerts(payload: dict):
    alerts = payload.get("alerts")
    if alerts is None:
        raise HTTPException(
            status_code=422,
            detail="Missing alerts field in webhook payload",
        )
    if not isinstance(alerts, list):
        raise HTTPException(status_code=422, detail="alerts must be a list")

    for alert in alerts:
        if not isinstance(alert, dict):
            raise HTTPException(status_code=422, detail="Each alert must be an object")
        _stored_alerts.append(alert)

    return {"status": "ok", "received": len(alerts)}


@app.get("/alerts", dependencies=[Depends(verify_webhook_access)])
def list_alerts():
    return {"count": len(_stored_alerts), "alerts": list(_stored_alerts)}


@app.delete("/alerts", dependencies=[Depends(verify_webhook_access)])
def clear_alerts():
    cleared = len(_stored_alerts)
    _stored_alerts.clear()
    return {"status": "ok", "cleared": cleared}
