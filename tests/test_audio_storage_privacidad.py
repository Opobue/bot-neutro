from datetime import datetime, timedelta
import importlib
import sys

import pytest

from bot_neutro.audio_storage import (
    AccessDeniedError,
    FileAudioSessionRepository,
    InMemoryAudioSessionRepository,
)
from bot_neutro.metrics_runtime import METRICS


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


def test_retention_env_invalid_falls_back_and_clamps(monkeypatch):
    monkeypatch.setenv("AUDIO_SESSION_RETENTION_DAYS", "invalid")
    repo = InMemoryAudioSessionRepository()

    stored = repo.create(_build_session("s-invalid", api_key_id="k1"))

    assert abs((stored["expires_at"] - stored["created_at"]) - timedelta(days=30)) <= timedelta(seconds=2)

    monkeypatch.setenv("AUDIO_SESSION_RETENTION_DAYS", "-5")
    repo2 = InMemoryAudioSessionRepository()

    stored2 = repo2.create(_build_session("s-negative", api_key_id="k1"))

    assert stored2["expires_at"] == stored2["created_at"]

    monkeypatch.setenv("AUDIO_SESSION_RETENTION_DAYS", "45")
    repo3 = InMemoryAudioSessionRepository()
    stored3 = repo3.create(_build_session("s-max", api_key_id="k1"))
    assert abs((stored3["expires_at"] - stored3["created_at"]) - timedelta(days=30)) <= timedelta(seconds=2)


def test_purge_disabled_keeps_expired_sessions(monkeypatch):
    monkeypatch.setenv("AUDIO_SESSION_PURGE_ENABLED", "0")
    repo = InMemoryAudioSessionRepository()
    repo.clear()

    expired_created_at = datetime.utcnow() - timedelta(days=40)
    expired = _build_session(
        "s-expired", api_key_id="k1", user_external_id="u1", created_at=expired_created_at
    )
    active = _build_session(
        "s-active", api_key_id="k1", user_external_id="u1", created_at=datetime.utcnow()
    )

    repo.create(expired)
    repo.create(active)

    sessions = repo.list_by_api_key("k1", limit=10, offset=0, api_key_id_autenticada="k1")
    assert len(sessions) == 2


def test_legacy_session_without_expires_at_is_treated_as_expired_on_purge():
    repo = InMemoryAudioSessionRepository()
    repo.clear()

    repo.create(_build_session("s1", api_key_id="k1", user_external_id="u1"))

    for item in repo._items:
        if item["id"] == "s1":
            item.pop("expires_at", None)
            break

    repo.purge_expired(now=datetime.utcnow())
    sessions = repo.list_by_api_key("k1", limit=10, offset=0, api_key_id_autenticada="k1")
    assert sessions == []


def test_sensitive_fields_are_not_persisted_by_default(monkeypatch):
    monkeypatch.delenv("AUDIO_SESSION_PERSIST_TRANSCRIPT", raising=False)
    monkeypatch.delenv("AUDIO_SESSION_PERSIST_REPLY_TEXT", raising=False)
    repo = InMemoryAudioSessionRepository()
    repo.clear()

    stored = repo.create(_build_session("s1", api_key_id="k1"))
    assert "transcript" not in stored
    assert "reply_text" not in stored


def test_sensitive_fields_persist_when_enabled_with_one_day_ttl(monkeypatch):
    monkeypatch.setenv("AUDIO_SESSION_PERSIST_TRANSCRIPT", "1")
    monkeypatch.setenv("AUDIO_SESSION_PERSIST_REPLY_TEXT", "1")
    monkeypatch.setenv("AUDIO_SESSION_RETENTION_DAYS", "30")
    repo = InMemoryAudioSessionRepository()
    repo.clear()

    created = datetime.utcnow()
    stored = repo.create(_build_session("s1", api_key_id="k1", created_at=created))

    assert stored["transcript"] == "t"
    assert stored["reply_text"] == "r"
    assert abs((stored["expires_at"] - created) - timedelta(days=1)) <= timedelta(seconds=2)


def test_purge_updates_metrics(monkeypatch):
    monkeypatch.setenv("AUDIO_SESSION_RETENTION_DAYS", "0")
    monkeypatch.setenv("AUDIO_SESSION_PURGE_ENABLED", "1")
    repo = InMemoryAudioSessionRepository(track_session_metrics=True)
    repo.clear()
    snapshot_before = METRICS.snapshot()

    repo.create(_build_session("s-expired", api_key_id="k1"))

    snapshot_after = METRICS.snapshot()
    assert snapshot_after["audio_sessions_purged_total"] >= snapshot_before["audio_sessions_purged_total"] + 1
    assert snapshot_after["audio_sessions_current"] == 0


def test_client_meta_is_sanitized():
    repo = InMemoryAudioSessionRepository()
    repo.clear()

    session = _build_session("s1", api_key_id="k1")
    session["client_meta"] = {
        "munay_user_id": "user-1",
        "munay_context": "diario_emocional",
        "email": "user@example.com",
    }

    stored = repo.create(session)
    assert stored["client_meta"] == {"munay_context": "diario_emocional"}


def test_import_audio_storage_has_no_disk_io_side_effects(monkeypatch, tmp_path):
    storage_path = tmp_path / "sessions.json"
    monkeypatch.setenv("AUDIO_SESSION_STORAGE_PATH", str(storage_path))

    sys.modules.pop("bot_neutro.audio_storage", None)
    importlib.import_module("bot_neutro.audio_storage")

    assert not storage_path.exists()


def test_create_does_not_raise_when_storage_path_unwritable(tmp_path):
    storage_path = tmp_path / "sessions.json"
    repo = FileAudioSessionRepository(storage_path=str(storage_path))
    repo.clear()
    snapshot_before = METRICS.snapshot()

    def _raise_os_error(*args, **kwargs):
        raise OSError("disk full")

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr("pathlib.Path.write_text", _raise_os_error)
        stored = repo.create(_build_session("s1", api_key_id="k1"))

    snapshot_after = METRICS.snapshot()
    assert stored["id"] == "s1"
    assert snapshot_after["errors_total"]["/audio"] >= snapshot_before["errors_total"]["/audio"] + 1


def test_clear_with_directory_storage_path_is_safe(tmp_path):
    repo = FileAudioSessionRepository(storage_path=str(tmp_path))
    repo.clear()
