import os
from datetime import datetime

from fastapi.testclient import TestClient

from bot_neutro.api import audio_session_repo, create_app
from bot_neutro.metrics_runtime import METRICS


def _restore_env(previous: dict) -> None:
    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def test_rate_limit_metric_increments_on_rejection():
    previous_env = {
        "RATE_LIMIT_ENABLED": os.environ.get("RATE_LIMIT_ENABLED"),
        "RATE_LIMIT_AUDIO_WINDOW_SECONDS": os.environ.get(
            "RATE_LIMIT_AUDIO_WINDOW_SECONDS"
        ),
        "RATE_LIMIT_AUDIO_MAX_REQUESTS": os.environ.get("RATE_LIMIT_AUDIO_MAX_REQUESTS"),
    }

    try:
        os.environ["RATE_LIMIT_ENABLED"] = "1"
        os.environ["RATE_LIMIT_AUDIO_WINDOW_SECONDS"] = "60"
        os.environ["RATE_LIMIT_AUDIO_MAX_REQUESTS"] = "1"

        snapshot_before = METRICS.snapshot()
        rl_hits_before = snapshot_before["rate_limit_hits_total"]

        client = TestClient(create_app())

        response_ok = client.post(
            "/audio",
            files={"audio_file": ("test.wav", b"fake audio", "audio/wav")},
            headers={"X-API-Key": "rl-metric"},
        )
        assert response_ok.status_code == 200

        response_blocked = client.post(
            "/audio",
            files={"audio_file": ("test.wav", b"fake audio", "audio/wav")},
            headers={"X-API-Key": "rl-metric"},
        )

        assert response_blocked.status_code == 429
        assert response_blocked.headers.get("X-Outcome") == "error"
        assert response_blocked.headers.get("X-Outcome-Detail") == "rate_limit"

        snapshot_after = METRICS.snapshot()
        rl_hits_after = snapshot_after["rate_limit_hits_total"]
        assert rl_hits_after >= rl_hits_before + 1

        metrics_response = client.get("/metrics")
        assert metrics_response.status_code == 200
        body = metrics_response.text
        assert "sensei_rate_limit_hits_total" in body
        assert f"sensei_rate_limit_hits_total {rl_hits_after}" in body
    finally:
        _restore_env(previous_env)


def test_mem_counters_cover_repository_reads_and_writes():
    snapshot_before = METRICS.snapshot()
    mem_reads_before = snapshot_before["mem_reads_total"]
    mem_writes_before = snapshot_before["mem_writes_total"]

    audio_session_repo.clear()
    session = {
        "id": "session-metric",
        "corr_id": "corr-metric",
        "api_key_id": "api-metric",
        "user_external_id": "user-1",
        "created_at": datetime.utcnow(),
        "request_mime_type": "audio/wav",
        "request_duration_seconds": None,
        "transcript": "t",
        "reply_text": "r",
        "tts_available": True,
        "tts_storage_ref": "https://example.com/audio.wav",
        "usage_stt_ms": 1,
        "usage_llm_ms": 1,
        "usage_tts_ms": 1,
        "usage_total_ms": 3,
        "provider_stt": "stub-stt",
        "provider_llm": "stub-llm",
        "provider_tts": "stub-tts",
        "meta_tags": None,
    }

    audio_session_repo.create(session)
    audio_session_repo.list_by_user("user-1")

    snapshot_after = METRICS.snapshot()

    assert snapshot_after["mem_writes_total"] >= mem_writes_before + 1
    assert snapshot_after["mem_reads_total"] >= mem_reads_before + 1
