import sys
import types

import pytest

from bot_neutro.providers import factory
from bot_neutro.providers.azure import AzureSTTProvider, AzureTTSProvider
from bot_neutro.providers.openai_llm import OpenAILLMProvider
from bot_neutro.providers.stub import StubLLMProvider, StubSTTProvider, StubTTSProvider


def _fake_speech_sdk(monkeypatch):
    azure = types.ModuleType("azure")
    cognitiveservices = types.ModuleType("azure.cognitiveservices")
    speech = types.ModuleType("azure.cognitiveservices.speech")

    monkeypatch.setattr(azure, "cognitiveservices", cognitiveservices, raising=False)
    monkeypatch.setattr(cognitiveservices, "speech", speech, raising=False)

    monkeypatch.setitem(sys.modules, "azure", azure)
    monkeypatch.setitem(sys.modules, "azure.cognitiveservices", cognitiveservices)
    monkeypatch.setitem(sys.modules, "azure.cognitiveservices.speech", speech)


def test_build_stt_provider_defaults_to_stub(monkeypatch):
    monkeypatch.delenv("AUDIO_STT_PROVIDER", raising=False)
    provider = factory.build_stt_provider()
    assert isinstance(provider, StubSTTProvider)


def test_build_tts_provider_defaults_to_stub(monkeypatch):
    monkeypatch.delenv("AUDIO_TTS_PROVIDER", raising=False)
    provider = factory.build_tts_provider()
    assert isinstance(provider, StubTTSProvider)


def test_build_llm_provider_is_stub(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    provider = factory.build_llm_provider()
    assert isinstance(provider, StubLLMProvider)


def test_build_llm_provider_stub_selected_explicitly(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    provider = factory.build_llm_provider()
    assert isinstance(provider, StubLLMProvider)


def test_build_llm_provider_openai_missing_api_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL_FREEMIUM", raising=False)

    with pytest.raises(RuntimeError):
        factory.build_llm_provider()


def test_build_llm_provider_openai_missing_dependency(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    monkeypatch.setenv("OPENAI_MODEL_FREEMIUM", "gpt-4.1-mini")

    def _raise_runtime_error():
        raise RuntimeError("openai SDK not installed")

    monkeypatch.setattr(
        OpenAILLMProvider, "_require_client", staticmethod(_raise_runtime_error), raising=True
    )

    with pytest.raises(RuntimeError):
        factory.build_llm_provider()


def test_build_stt_provider_azure_missing_config(monkeypatch):
    monkeypatch.setenv("AUDIO_STT_PROVIDER", "azure")
    monkeypatch.delenv("AZURE_SPEECH_KEY", raising=False)
    monkeypatch.delenv("AZURE_SPEECH_REGION", raising=False)

    with pytest.raises(ValueError):
        factory.build_stt_provider()


def test_build_tts_provider_returns_azure_when_configured(monkeypatch):
    monkeypatch.setenv("AUDIO_TTS_PROVIDER", "azure")
    monkeypatch.setenv("AZURE_SPEECH_KEY", "dummy-key")
    monkeypatch.setenv("AZURE_SPEECH_REGION", "eastus")
    monkeypatch.setenv("AZURE_SPEECH_STT_LANGUAGE_DEFAULT", "es-ES")
    monkeypatch.setenv("AZURE_SPEECH_TTS_VOICE_DEFAULT", "es-ES-AlonsoNeural")
    _fake_speech_sdk(monkeypatch)

    provider = factory.build_tts_provider()
    assert isinstance(provider, AzureTTSProvider)


def test_build_stt_provider_returns_azure_when_configured(monkeypatch):
    monkeypatch.setenv("AUDIO_STT_PROVIDER", "azure")
    monkeypatch.setenv("AZURE_SPEECH_KEY", "dummy-key")
    monkeypatch.setenv("AZURE_SPEECH_REGION", "eastus")
    _fake_speech_sdk(monkeypatch)

    provider = factory.build_stt_provider()
    assert isinstance(provider, AzureSTTProvider)


def test_build_tts_provider_missing_dependency(monkeypatch):
    monkeypatch.setenv("AUDIO_TTS_PROVIDER", "azure")
    monkeypatch.setenv("AZURE_SPEECH_KEY", "dummy-key")
    monkeypatch.setenv("AZURE_SPEECH_REGION", "eastus")

    def _raise_import_error():
        raise ImportError("no azure sdk for tests")

    monkeypatch.setattr(
        AzureTTSProvider, "_require_sdk", staticmethod(_raise_import_error), raising=True
    )

    with pytest.raises(ValueError):
        factory.build_tts_provider()


def test_build_stt_provider_missing_dependency(monkeypatch):
    monkeypatch.setenv("AUDIO_STT_PROVIDER", "azure")
    monkeypatch.setenv("AZURE_SPEECH_KEY", "dummy-key")
    monkeypatch.setenv("AZURE_SPEECH_REGION", "eastus")

    def _raise_import_error():
        raise ImportError("no azure sdk for tests")

    monkeypatch.setattr(
        AzureSTTProvider, "_require_sdk", staticmethod(_raise_import_error), raising=True
    )

    with pytest.raises(ValueError):
        factory.build_stt_provider()
