"""Tests for local Alertmanager webhook receiver."""

import pytest
from fastapi.testclient import TestClient

from apps.alert_webhook.main import _stored_alerts, app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_stored_alerts():
    _stored_alerts.clear()
    yield
    _stored_alerts.clear()


def test_alert_webhook_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "boundary-layer-alert-webhook"


def test_post_alerts_stores_alerts():
    payload = {
        "status": "firing",
        "alerts": [
            {
                "status": "firing",
                "labels": {"alertname": "BoundaryLayerInferenceCircuitBreakerOpen"},
                "annotations": {"summary": "test"},
            }
        ],
    }
    response = client.post("/alerts", json=payload)
    assert response.status_code == 200
    assert response.json()["received"] == 1

    listed = client.get("/alerts")
    assert listed.status_code == 200
    data = listed.json()
    assert data["count"] == 1
    assert data["alerts"][0]["labels"]["alertname"] == (
        "BoundaryLayerInferenceCircuitBreakerOpen"
    )


def test_get_alerts_empty():
    response = client.get("/alerts")
    assert response.status_code == 200
    assert response.json() == {"count": 0, "alerts": []}


def test_delete_alerts_clears_store():
    client.post(
        "/alerts",
        json={"alerts": [{"labels": {"alertname": "TestAlert"}}]},
    )
    response = client.delete("/alerts")
    assert response.status_code == 200
    assert response.json()["cleared"] == 1
    assert client.get("/alerts").json()["count"] == 0


def test_post_alerts_invalid_payload():
    response = client.post("/alerts", json={"status": "firing"})
    assert response.status_code == 422

    response = client.post("/alerts", json={"alerts": "not-a-list"})
    assert response.status_code == 422
