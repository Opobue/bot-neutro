import logging
import os

from .azure import AzureSTTProvider, AzureTTSProvider
from .interfaces import LLMProvider, STTProvider, TTSProvider
from .openai_llm import OpenAILLMProvider
from .stub import StubLLMProvider, StubSTTProvider, StubTTSProvider

logger = logging.getLogger(__name__)


def build_stt_provider() -> STTProvider:
    provider_name = os.getenv("AUDIO_STT_PROVIDER", "stub").lower()
    if provider_name == "azure":
        fallback = StubSTTProvider()
        return AzureSTTProvider.from_env(fallback=fallback)
    return StubSTTProvider()


def build_tts_provider() -> TTSProvider:
    provider_name = os.getenv("AUDIO_TTS_PROVIDER", "stub").lower()
    if provider_name == "azure":
        fallback = StubTTSProvider()
        return AzureTTSProvider.from_env(fallback=fallback)
    return StubTTSProvider()


def get_llm_provider() -> LLMProvider:
    name = os.getenv("LLM_PROVIDER", "stub").lower()
    if name in {"", "stub"}:
        return StubLLMProvider()
    if name == "openai":
        fallback = StubLLMProvider()
        return OpenAILLMProvider.from_env(fallback=fallback)

    logger.warning("llm_provider_unknown", extra={"provider": name})
    return StubLLMProvider()


def build_llm_provider() -> LLMProvider:
    return get_llm_provider()


__all__ = ["build_stt_provider", "build_tts_provider", "build_llm_provider", "get_llm_provider"]
