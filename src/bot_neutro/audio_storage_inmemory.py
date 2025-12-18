import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, TypedDict

from .metrics_runtime import METRICS


class AccessDeniedError(Exception):
    """Señala violaciones de control de acceso multi-tenant en el storage."""


class AudioSession(TypedDict):
    id: str
    corr_id: str
    api_key_id: str
    user_external_id: Optional[str]
    created_at: datetime
    expires_at: datetime
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
    meta_tags: Optional[Dict[str, str]]


class InMemoryAudioSessionRepository:
    def __init__(self, track_session_metrics: bool = False) -> None:
        self._items: List[AudioSession] = []
        raw_retention = os.getenv("AUDIO_SESSION_RETENTION_DAYS", "30")
        try:
            self._retention_days = int(raw_retention)
        except ValueError:
            self._retention_days = 30
        if self._retention_days < 0:
            self._retention_days = 0
        self._purge_enabled = os.getenv("AUDIO_SESSION_PURGE_ENABLED", "1") != "0"
        self._track_session_metrics = track_session_metrics

    def clear(self) -> None:
        """Borra todas las sesiones (para tests)."""

        self._items.clear()
        if self._track_session_metrics:
            METRICS.set_audio_sessions_current(0)

    def create(self, session: AudioSession) -> AudioSession:
        """Inserta la sesión; si ya existe `id`, puede sobrescribir o ignorar."""

        now = datetime.utcnow()
        created_at = session.get("created_at", now)
        session["created_at"] = created_at
        session["expires_at"] = created_at + timedelta(days=self._retention_days)

        if self._purge_enabled:
            self.purge_expired(now=now)

        self._items.append(session)
        METRICS.inc_mem_write()
        if self._track_session_metrics:
            METRICS.set_audio_sessions_current(len(self._items))
        return session

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

        now = datetime.utcnow()
        if self._purge_enabled:
            self.purge_expired(now=now)

        filtered = [
            item
            for item in self._items
            if item["user_external_id"] == user_external_id
            and item["api_key_id"] == api_key_id_autenticada
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

        now = datetime.utcnow()
        if self._purge_enabled:
            self.purge_expired(now=now)

        filtered = [item for item in self._items if item["api_key_id"] == api_key_id]
        sorted_items = sorted(filtered, key=lambda s: s["created_at"], reverse=True)
        METRICS.inc_mem_read()
        return sorted_items[offset : offset + limit]

    def purge_expired(self, now: Optional[datetime] = None) -> None:
        if now is None:
            now = datetime.utcnow()

        before_count = len(self._items)
        # Sesiones sin `expires_at` (legado) se consideran expiradas para evitar retener datos
        # sensibles sin límite explícito.
        self._items = [
            item for item in self._items if item.get("expires_at", now) > now
        ]
        purged = before_count - len(self._items)
        if purged > 0:
            METRICS.inc_audio_sessions_purged(purged)
        if self._track_session_metrics:
            METRICS.set_audio_sessions_current(len(self._items))


DEFAULT_AUDIO_SESSION_REPOSITORY = InMemoryAudioSessionRepository(track_session_metrics=True)

__all__ = [
    "AudioSession",
    "AccessDeniedError",
    "InMemoryAudioSessionRepository",
    "DEFAULT_AUDIO_SESSION_REPOSITORY",
]
