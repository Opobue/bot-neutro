from bot_neutro.audio_pipeline import AudioPipeline
from bot_neutro.audio_storage_inmemory import InMemoryAudioSessionRepository
from bot_neutro.providers.azure import AzureSTTProvider, AzureTTSProvider, AzureSpeechConfig
from bot_neutro.providers.stub import StubLLMProvider, StubSTTProvider, StubTTSProvider


def test_audio_pipeline_with_stub_providers_matches_stub_contract():
    repo = InMemoryAudioSessionRepository()
    pipeline = AudioPipeline(
        session_repo=repo,
        stt_provider=StubSTTProvider(),
        tts_provider=StubTTSProvider(),
        llm_provider=StubLLMProvider(),
    )

    result = pipeline.process(
        {
            "api_key_id": "test-key",
            "audio_bytes": b"fake audio",
            "mime_type": "audio/wav",
            "locale": "es-CO",
            "corr_id": "corr-123",
            "client_meta": {"munay_context": "diario_emocional"},
        }
    )

    assert "code" not in result
    assert result["transcript"] == "stub transcript"
    assert result["reply_text"] == "stub reply text"
    assert result["tts_url"] == "https://example.com/audio/stub.wav"

    usage = result["usage"]
    assert usage["stt_ms"] == 100
    assert usage["llm_ms"] == 200
    assert usage["tts_ms"] == 150
    assert usage["total_ms"] == 450
    assert usage["provider_stt"] == "stub-stt"
    assert usage["provider_llm"] == "stub-llm"
    assert usage["provider_tts"] == "stub-tts"
    assert usage["input_seconds"] == 1.0
    assert usage["output_seconds"] == 1.5

    sessions = repo.list_by_api_key("test-key", limit=10, offset=0)
    assert len(sessions) == 1
    session = sessions[0]
    assert session["tts_storage_ref"] == "https://example.com/audio/stub.wav"
    assert session["provider_stt"] == "stub-stt"
    assert session["provider_llm"] == "stub-llm"
    assert session["provider_tts"] == "stub-tts"
    assert session["corr_id"] == "corr-123"
    assert session["meta_tags"] == {"context": "diario_emocional"}


def test_audio_pipeline_falls_back_when_azure_stt_fails(monkeypatch):
    repo = InMemoryAudioSessionRepository()
    azure_stt = AzureSTTProvider(
        AzureSpeechConfig(
            key="dummy", region="region", stt_language_default="es-ES", tts_voice_default="voice"
        ),
        fallback=StubSTTProvider(),
    )

    def _fail_transcribe(*args, **kwargs):
        raise RuntimeError("azure stt down")

    monkeypatch.setattr(azure_stt, "_transcribe_with_sdk", _fail_transcribe)

    pipeline = AudioPipeline(
        session_repo=repo,
        stt_provider=azure_stt,
        tts_provider=StubTTSProvider(),
        llm_provider=StubLLMProvider(),
    )

    result = pipeline.process(
        {
            "api_key_id": "test-key",
            "audio_bytes": b"fake audio",
            "mime_type": "audio/wav",
            "locale": "es-CO",
        }
    )

    assert "code" not in result
    usage = result["usage"]
    assert usage["provider_stt"] == "azure-stt|stub-stt"
    assert usage["provider_tts"] == "stub-tts"


def test_audio_pipeline_falls_back_when_azure_tts_fails(monkeypatch):
    repo = InMemoryAudioSessionRepository()
    azure_tts = AzureTTSProvider(
        AzureSpeechConfig(
            key="dummy", region="region", stt_language_default="es-ES", tts_voice_default="voice"
        ),
        fallback=StubTTSProvider(),
    )

    def _fail_synthesize(*args, **kwargs):
        raise RuntimeError("azure tts down")

    monkeypatch.setattr(azure_tts, "_synthesize_with_sdk", _fail_synthesize)

    pipeline = AudioPipeline(
        session_repo=repo,
        stt_provider=StubSTTProvider(),
        tts_provider=azure_tts,
        llm_provider=StubLLMProvider(),
    )

    result = pipeline.process(
        {
            "api_key_id": "test-key",
            "audio_bytes": b"fake audio",
            "mime_type": "audio/wav",
            "locale": "es-CO",
        }
    )

    assert "code" not in result
    usage = result["usage"]
    assert usage["provider_tts"] == "azure-tts|stub-tts"
    assert result["tts_url"] == "https://example.com/audio/stub.wav"
