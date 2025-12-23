import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, TypedDict

from .metrics_runtime import METRICS


class AccessDeniedError(Exception):
    """Señala violaciones de control de acceso multi-tenant en el storage."""


class UsagePayload(TypedDict):
    input_seconds: float
    output_seconds: float
    stt_ms: int
    llm_ms: int
    tts_ms: int
    total_ms: int
    providers: Dict[str, str]


class AudioSession(TypedDict, total=False):
    id: str
    session_id: str
    corr_id: str
    api_key_id: str
    user_external_id: Optional[str]
    created_at: datetime
    expires_at: datetime
    status: str
    request_mime_type: str
    request_duration_seconds: Optional[float]
    transcript: str
    reply_text: str
    tts_available: bool
    tts_storage_ref: Optional[str]
    usage_stt_ms: int
    usage_llm_ms: int
    usage_tts_ms: int
    usage_total_ms: int
    provider_stt: str
    provider_llm: str
    provider_tts: str
    usage: UsagePayload
    client_meta: Optional[Dict[str, str]]
    meta_tags: Optional[Dict[str, str]]


def _parse_retention_days() -> int:
    raw_retention = os.getenv("AUDIO_SESSION_RETENTION_DAYS", "30")
    try:
        retention_days = int(raw_retention)
    except ValueError:
        retention_days = 30
    if retention_days < 0:
        retention_days = 0
    if retention_days > 30:
        retention_days = 30
    return retention_days


def _parse_flag(name: str, default: str) -> bool:
    return os.getenv(name, default) != "0"


def _sanitize_client_meta(meta: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
    if not meta:
        return None
    sanitized: Dict[str, str] = {}
    if "munay_context" in meta:
        sanitized["munay_context"] = meta["munay_context"]
    elif "context" in meta:
        sanitized["munay_context"] = meta["context"]
    return sanitized or None


def _build_usage_payload(session: AudioSession) -> UsagePayload:
    usage = session.get("usage")
    if usage:
        return usage
    providers = {
        "stt": session.get("provider_stt", "stt"),
        "llm": session.get("provider_llm", "llm"),
        "tts": session.get("provider_tts", "tts"),
    }
    return UsagePayload(
        input_seconds=float(session.get("request_duration_seconds") or 0.0),
        output_seconds=0.0,
        stt_ms=session.get("usage_stt_ms", 0),
        llm_ms=session.get("usage_llm_ms", 0),
        tts_ms=session.get("usage_tts_ms", 0),
        total_ms=session.get("usage_total_ms", 0),
        providers=providers,
    )


class FileAudioSessionRepository:
    def __init__(
        self,
        track_session_metrics: bool = False,
        storage_path: Optional[str] = None,
    ) -> None:
        self._items: List[AudioSession] = []
        self._retention_days = _parse_retention_days()
        self._purge_enabled = _parse_flag("AUDIO_SESSION_PURGE_ENABLED", "1")
        self._persist_transcript = _parse_flag(
            "AUDIO_SESSION_PERSIST_TRANSCRIPT", "0"
        )
        self._persist_reply_text = _parse_flag(
            "AUDIO_SESSION_PERSIST_REPLY_TEXT", "0"
        )
        self._track_session_metrics = track_session_metrics
        self._storage_path = Path(
            storage_path
            or os.getenv("AUDIO_SESSION_STORAGE_PATH", "/tmp/bot_neutro_audio_sessions.json")
        )
        self._load_from_disk()
        if self._purge_enabled:
            self.purge_expired(now=datetime.utcnow())

    def clear(self) -> None:
        """Borra todas las sesiones (para tests)."""

        self._items.clear()
        if self._storage_path.exists():
            if self._storage_path.is_file():
                self._storage_path.unlink()
        if self._track_session_metrics:
            METRICS.set_audio_sessions_current(0)

    def create(self, session: AudioSession) -> AudioSession:
        """Inserta la sesión; si ya existe `id`, puede sobrescribir o ignorar."""

        now = datetime.utcnow()
        created_at = session.get("created_at", now)
        retention_delta = timedelta(days=self._retention_days)
        expires_at = created_at + retention_delta
        if self._persist_transcript or self._persist_reply_text:
            expires_at = min(expires_at, created_at + timedelta(days=1))

        session_id = session.get("id") or session.get("session_id") or ""
        stored: AudioSession = dict(session)
        stored["id"] = session_id
        stored["session_id"] = session_id
        stored["created_at"] = created_at
        stored["expires_at"] = expires_at
        stored["status"] = session.get("status", "processed")
        stored["usage"] = _build_usage_payload(session)
        stored["client_meta"] = _sanitize_client_meta(session.get("client_meta"))

        if not self._persist_transcript:
            stored.pop("transcript", None)
        if not self._persist_reply_text:
            stored.pop("reply_text", None)

        if self._purge_enabled:
            self.purge_expired(now=now)

        if self._purge_enabled and expires_at <= now:
            METRICS.inc_audio_sessions_purged(1)
            if self._track_session_metrics:
                METRICS.set_audio_sessions_current(len(self._items))
            return stored

        self._items.append(stored)
        METRICS.inc_mem_write()
        if self._track_session_metrics:
            METRICS.set_audio_sessions_current(len(self._items))
        self._persist()
        return stored

    def list_by_user(
        self,
        user_external_id: str,
        limit: int = 50,
        offset: int = 0,
        api_key_id_autenticada: Optional[str] = None,
    ) -> List[AudioSession]:
        """Filtra por `user_external_id`, ordena por `created_at DESC`, aplica offset/limit."""

        if api_key_id_autenticada is None:
            raise AccessDeniedError("api_key_id_autenticada is required")

        if self._purge_enabled:
            self.purge_expired(now=datetime.utcnow())

        filtered = [
            item
            for item in self._items
            if item.get("user_external_id") == user_external_id
            and item.get("api_key_id") == api_key_id_autenticada
        ]
        sorted_items = sorted(filtered, key=lambda s: s["created_at"], reverse=True)
        METRICS.inc_mem_read()
        return sorted_items[offset : offset + limit]

    def list_by_api_key(
        self,
        api_key_id: str,
        limit: int = 50,
        offset: int = 0,
        api_key_id_autenticada: Optional[str] = None,
    ) -> List[AudioSession]:
        """Filtra por `api_key_id`, ordena por `created_at DESC`, aplica offset/limit."""

        if api_key_id_autenticada is None:
            raise AccessDeniedError("api_key_id_autenticada is required")
        if api_key_id != api_key_id_autenticada:
            raise AccessDeniedError("access denied for api_key_id")

        if self._purge_enabled:
            self.purge_expired(now=datetime.utcnow())

        filtered = [item for item in self._items if item.get("api_key_id") == api_key_id]
        sorted_items = sorted(filtered, key=lambda s: s["created_at"], reverse=True)
        METRICS.inc_mem_read()
        return sorted_items[offset : offset + limit]

    def purge_expired(self, now: Optional[datetime] = None) -> None:
        if now is None:
            now = datetime.utcnow()

        try:
            before_count = len(self._items)
            self._items = [
                item for item in self._items if item.get("expires_at", now) > now
            ]
            purged = before_count - len(self._items)
            if purged > 0:
                METRICS.inc_audio_sessions_purged(purged)
            if self._track_session_metrics:
                METRICS.set_audio_sessions_current(len(self._items))
            if purged > 0:
                self._persist()
        except Exception:
            METRICS.inc_error("/audio")

    def _load_from_disk(self) -> None:
        if not self._storage_path.exists():
            if self._track_session_metrics:
                METRICS.set_audio_sessions_current(0)
            return
        try:
            data = json.loads(self._storage_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = []
        items: List[AudioSession] = []
        for item in data if isinstance(data, list) else []:
            if not isinstance(item, dict):
                continue
            created_at = item.get("created_at")
            expires_at = item.get("expires_at")
            if isinstance(created_at, str):
                try:
                    item["created_at"] = datetime.fromisoformat(created_at)
                except ValueError:
                    continue
            if isinstance(expires_at, str):
                try:
                    item["expires_at"] = datetime.fromisoformat(expires_at)
                except ValueError:
                    continue
            items.append(item)
        self._items = items
        if self._track_session_metrics:
            METRICS.set_audio_sessions_current(len(self._items))

    def _serialize(self, item: AudioSession) -> AudioSession:
        payload = dict(item)
        created_at = payload.get("created_at")
        expires_at = payload.get("expires_at")
        if isinstance(created_at, datetime):
            payload["created_at"] = created_at.isoformat()
        if isinstance(expires_at, datetime):
            payload["expires_at"] = expires_at.isoformat()
        return payload

    def _persist(self) -> None:
        try:
            if len(self._items) == 0:
                return
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            serialized = [self._serialize(item) for item in self._items]
            tmp_path = self._storage_path.with_suffix(".tmp")
            tmp_path.write_text(
                json.dumps(serialized, ensure_ascii=False), encoding="utf-8"
            )
            tmp_path.replace(self._storage_path)
        except OSError:
            METRICS.inc_error("/audio")
        except Exception:
            METRICS.inc_error("/audio")


class InMemoryAudioSessionRepository(FileAudioSessionRepository):
    def __init__(self, track_session_metrics: bool = False) -> None:
        self._items = []
        self._retention_days = _parse_retention_days()
        self._purge_enabled = _parse_flag("AUDIO_SESSION_PURGE_ENABLED", "1")
        self._persist_transcript = _parse_flag("AUDIO_SESSION_PERSIST_TRANSCRIPT", "0")
        self._persist_reply_text = _parse_flag("AUDIO_SESSION_PERSIST_REPLY_TEXT", "0")
        self._track_session_metrics = track_session_metrics
        self._storage_path: Optional[Path] = None
        if self._track_session_metrics:
            METRICS.set_audio_sessions_current(0)

    def clear(self) -> None:
        self._items.clear()
        if self._track_session_metrics:
            METRICS.set_audio_sessions_current(0)

    def _load_from_disk(self) -> None:
        self._items = []
        if self._track_session_metrics:
            METRICS.set_audio_sessions_current(0)

    def _persist(self) -> None:
        return


_DEFAULT_AUDIO_SESSION_REPOSITORY: Optional[FileAudioSessionRepository] = None


def get_default_audio_session_repository() -> FileAudioSessionRepository:
    global _DEFAULT_AUDIO_SESSION_REPOSITORY
    if _DEFAULT_AUDIO_SESSION_REPOSITORY is None:
        _DEFAULT_AUDIO_SESSION_REPOSITORY = FileAudioSessionRepository(
            track_session_metrics=True
        )
    return _DEFAULT_AUDIO_SESSION_REPOSITORY

__all__ = [
    "AudioSession",
    "AccessDeniedError",
    "FileAudioSessionRepository",
    "InMemoryAudioSessionRepository",
    "get_default_audio_session_repository",
]
