from bot_neutro.api import create_app
from fastapi.testclient import TestClient


client = TestClient(create_app())


def test_metrics_content_type_and_headers():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain; version=0.0.4")
    assert response.headers.get("X-Outcome") == "ok"
    assert response.headers.get("X-Correlation-Id")


def test_metrics_payload_includes_core_counters():
    response = client.get("/metrics")
    body = response.text
    assert "sensei_request_latency_seconds_bucket" in body
    assert "sensei_rate_limit_hits_total" in body
    assert "errors_total" in body
    assert "mem_reads_total" in body
    assert "mem_writes_total" in body
    assert "sensei_requests_total" in body
