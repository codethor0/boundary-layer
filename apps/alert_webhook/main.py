"""Local Alertmanager webhook receiver for BoundaryLayer validation."""

from fastapi import FastAPI, HTTPException

app = FastAPI(title="BoundaryLayer Alert Webhook", version="0.7.0")

_stored_alerts: list[dict] = []


@app.get("/health")
def health():
    return {"status": "ok", "service": "boundary-layer-alert-webhook"}


@app.post("/alerts")
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


@app.get("/alerts")
def list_alerts():
    return {"count": len(_stored_alerts), "alerts": list(_stored_alerts)}


@app.delete("/alerts")
def clear_alerts():
    cleared = len(_stored_alerts)
    _stored_alerts.clear()
    return {"status": "ok", "cleared": cleared}
