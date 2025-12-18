import importlib

from fastapi.testclient import TestClient

from bot_neutro import api
from bot_neutro.api import audio_session_repo, create_app


client = TestClient(create_app())


def test_audio_stats_is_per_tenant_and_has_no_sensitive_fields():
    audio_session_repo.clear()

    resp_a = client.post(
        "/audio",
        files={"audio_file": ("a.wav", b"fake", "audio/wav")},
        headers={"X-API-Key": "tenant-a", "X-Correlation-Id": "corr-a"},
        data={"user_external_id": "user-a"},
    )
    assert resp_a.status_code == 200

    resp_b = client.post(
        "/audio",
        files={"audio_file": ("b.wav", b"fake", "audio/wav")},
        headers={"X-API-Key": "tenant-b", "X-Correlation-Id": "corr-b"},
        data={"user_external_id": "user-b"},
    )
    assert resp_b.status_code == 200

    stats_a = client.get("/audio/stats", headers={"X-API-Key": "tenant-a"})
    assert stats_a.status_code == 200
    body_a = stats_a.json()
    assert "api_key_id" in body_a
    assert body_a["api_key_id"] != "tenant-a"
    assert len(body_a["api_key_id"]) == 12
    assert body_a["totals"]["sessions_current"] == 1
    assert "limit_applied" in body_a["totals"]

    stats_b = client.get("/audio/stats", headers={"X-API-Key": "tenant-b"})
    assert stats_b.status_code == 200
    body_b = stats_b.json()
    assert "api_key_id" in body_b
    assert body_b["api_key_id"] != "tenant-b"
    assert len(body_b["api_key_id"]) == 12
    assert body_b["totals"]["sessions_current"] == 1

    serialized = str(body_a).lower()
    for forbidden in [
        "transcript",
        "reply_text",
        "meta_tags",
        "user_external_id",
        "corr_id",
        "tts_storage_ref",
    ]:
        assert forbidden not in serialized


def test_audio_stats_requires_api_key_header():
    audio_session_repo.clear()

    resp = client.get("/audio/stats")
    assert resp.status_code == 401
    assert resp.json()["detail"] == "X-API-Key required"
    assert resp.headers.get("X-Outcome") == "error"


def test_audio_stats_ignores_client_supplied_public_id():
    audio_session_repo.clear()

    resp = client.post(
        "/audio",
        files={"audio_file": ("a.wav", b"fake", "audio/wav")},
        headers={"X-API-Key": "tenant-a", "X-Correlation-Id": "corr-a"},
        data={"user_external_id": "user-a"},
    )
    assert resp.status_code == 200

    spoofed = client.get(
        "/audio/stats",
        headers={"X-API-Key": "tenant-a", "X-API-Key-Id": "spoofed-public"},
    )
    assert spoofed.status_code == 200
    body = spoofed.json()
    assert body["api_key_id"] != "spoofed-public"


def test_audio_stats_env_invalid_does_not_crash_import(monkeypatch):
    monkeypatch.setenv("AUDIO_STATS_MAX_SESSIONS", "invalid")
    importlib.reload(api)
    client_local = TestClient(api.create_app())

    resp = client_local.get("/audio/stats")
    assert resp.status_code == 401
