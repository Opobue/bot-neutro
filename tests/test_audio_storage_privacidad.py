from datetime import datetime, timedelta

import pytest

from bot_neutro.audio_storage_inmemory import AccessDeniedError, InMemoryAudioSessionRepository


def _build_session(session_id: str, api_key_id: str, user_external_id: str | None = None, created_at: datetime | None = None):
    return {
        "id": session_id,
        "corr_id": f"corr-{session_id}",
        "api_key_id": api_key_id,
        "user_external_id": user_external_id,
        "created_at": created_at or datetime.utcnow(),
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


def test_create_calculates_expires_at_with_default_retention():
    repo = InMemoryAudioSessionRepository()
    repo.clear()

    session = _build_session("s1", api_key_id="k1")
    created = datetime.utcnow()
    session["created_at"] = created

    stored = repo.create(session)

    assert "expires_at" in stored
    assert stored["expires_at"] > stored["created_at"]
    assert abs((stored["expires_at"] - created) - timedelta(days=30)) <= timedelta(seconds=2)


def test_purge_removes_expired_before_listing():
    repo = InMemoryAudioSessionRepository()
    repo.clear()

    expired_created_at = datetime.utcnow() - timedelta(days=40)
    active_created_at = datetime.utcnow()

    expired = _build_session("s-expired", api_key_id="k1", user_external_id="u1", created_at=expired_created_at)
    active = _build_session("s-active", api_key_id="k1", user_external_id="u1", created_at=active_created_at)

    repo.create(expired)
    repo.create(active)

    sessions = repo.list_by_api_key("k1", limit=10, offset=0, api_key_id_autenticada="k1")

    assert len(sessions) == 1
    assert sessions[0]["id"] == "s-active"

    sessions_by_user = repo.list_by_user("u1", limit=10, offset=0, api_key_id_autenticada="k1")
    assert len(sessions_by_user) == 1
    assert sessions_by_user[0]["id"] == "s-active"


def test_isolation_blocks_cross_tenant_reads():
    repo = InMemoryAudioSessionRepository()
    repo.clear()

    repo.create(_build_session("s1", api_key_id="tenant-a", user_external_id="user-1"))

    with pytest.raises(AccessDeniedError):
        repo.list_by_api_key("tenant-a", api_key_id_autenticada="tenant-b")

    assert repo.list_by_user("user-1", api_key_id_autenticada="tenant-b") == []


def test_reads_require_api_key_id_autenticada():
    repo = InMemoryAudioSessionRepository()
    repo.clear()
    repo.create(_build_session("s1", api_key_id="tenant-a", user_external_id="user-1"))

    with pytest.raises(AccessDeniedError):
        repo.list_by_api_key("tenant-a")

    with pytest.raises(AccessDeniedError):
        repo.list_by_user("user-1")
