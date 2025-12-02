from datetime import datetime
from typing import Dict, List, Optional, TypedDict


class AudioSession(TypedDict):
    id: str
    corr_id: str
    api_key_id: str
    user_external_id: Optional[str]
    created_at: datetime
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
    def __init__(self) -> None:
        self._items: List[AudioSession] = []

    def clear(self) -> None:
        """Borra todas las sesiones (para tests)."""

        self._items.clear()

    def create(self, session: AudioSession) -> AudioSession:
        """Inserta la sesión; si ya existe `id`, puede sobrescribir o ignorar."""

        self._items.append(session)
        return session

    def list_by_user(
        self,
        user_external_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AudioSession]:
        """Filtra por `user_external_id`, ordena por `created_at DESC`, aplica offset/limit."""

        filtered = [item for item in self._items if item["user_external_id"] == user_external_id]
        sorted_items = sorted(filtered, key=lambda s: s["created_at"], reverse=True)
        return sorted_items[offset : offset + limit]

    def list_by_api_key(
        self,
        api_key_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AudioSession]:
        """Filtra por `api_key_id`, ordena por `created_at DESC`, aplica offset/limit."""

        filtered = [item for item in self._items if item["api_key_id"] == api_key_id]
        sorted_items = sorted(filtered, key=lambda s: s["created_at"], reverse=True)
        return sorted_items[offset : offset + limit]


DEFAULT_AUDIO_SESSION_REPOSITORY = InMemoryAudioSessionRepository()

__all__ = [
    "AudioSession",
    "InMemoryAudioSessionRepository",
    "DEFAULT_AUDIO_SESSION_REPOSITORY",
]
