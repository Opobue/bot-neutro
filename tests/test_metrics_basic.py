from fastapi.testclient import TestClient

from bot_neutro.api import create_app
from bot_neutro.metrics_runtime import METRICS

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
    assert "llm_tier_denied_total" in body
    assert "mem_reads_total" in body
    assert "mem_writes_total" in body
    assert "sensei_requests_total" in body


def test_dynamic_metrics_for_audio_requests():
    metrics_before = METRICS.snapshot()
    audio_requests_before = metrics_before["requests_total"].get("/audio", 0)
    audio_errors_before = metrics_before["errors_total"].get("/audio", 0)

    response_ok = client.post(
        "/audio",
        files={"audio_file": ("test.wav", b"RIFFDATA", "audio/wav")},
        headers={"X-API-Key": "dummy"},
    )
    assert response_ok.status_code == 200

    response_error = client.post(
        "/audio", files={"audio_file": ("test.wav", b"RIFFDATA", "audio/wav")}
    )
    assert response_error.status_code == 401

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200

    expected_requests = audio_requests_before + 2
    expected_errors = audio_errors_before + 1

    body = metrics_response.text
    assert (
        f'sensei_requests_total{{route="/audio"}} {expected_requests}'
        in body
    )
    assert f'errors_total{{route="/audio"}} {expected_errors}' in body


def test_audio_latency_histogram_exposed_and_counts_increment():
    snapshot_before = METRICS.snapshot()
    latency_before = snapshot_before["latency"].get("/audio", {}).get("count", 0)

    response = client.post(
        "/audio",
        files={"audio_file": ("test.wav", b"RIFFDATA", "audio/wav")},
        headers={"X-API-Key": "latency-test"},
    )
    assert response.status_code == 200

    snapshot_after = METRICS.snapshot()
    latency_after = snapshot_after["latency"].get("/audio", {}).get("count", 0)
    assert latency_after >= latency_before + 1
    assert snapshot_after["latency"].get("/audio", {}).get("sum", 0) > 0

    metrics_response = client.get("/metrics")
    body = metrics_response.text

    assert 'sensei_request_latency_seconds_bucket{route="/audio",le="0.1"}' in body
    assert 'sensei_request_latency_seconds_bucket{route="/audio",le="0.5"}' in body
    assert 'sensei_request_latency_seconds_bucket{route="/audio",le="1.0"}' in body
    assert 'sensei_request_latency_seconds_bucket{route="/audio",le="+Inf"}' in body
    assert 'sensei_request_latency_seconds_count{route="/audio"}' in body
    assert 'sensei_request_latency_seconds_sum{route="/audio"}' in body
