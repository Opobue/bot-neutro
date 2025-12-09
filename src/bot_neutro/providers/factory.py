import os

from .azure import AzureSTTProvider, AzureTTSProvider
from .interfaces import LLMProvider, STTProvider, TTSProvider
from .stub import StubLLMProvider, StubSTTProvider, StubTTSProvider


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


def build_llm_provider() -> LLMProvider:
    return StubLLMProvider()


__all__ = ["build_stt_provider", "build_tts_provider", "build_llm_provider"]
