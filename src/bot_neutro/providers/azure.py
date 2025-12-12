"""Azure Speech providers with stub-friendly fallbacks.

Estas implementaciones siguen siendo opt-in: solo se activan cuando las
variables de entorno `AUDIO_STT_PROVIDER`/`AUDIO_TTS_PROVIDER` se fijan a
`azure` y existen las credenciales necesarias. Las importaciones del SDK de
Azure son perezosas para no impactar entornos sin la dependencia instalada
cuando se usa el modo stub.
"""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass
from typing import Optional

from .interfaces import LLMProvider, STTProvider, STTResult, TTSProvider, TTSResult


logger = logging.getLogger("bot_neutro")


@dataclass
class AzureSpeechConfig:
    key: str
    region: str
    stt_language_default: str
    tts_voice_default: str


class AzureProviderError(RuntimeError):
    """Errores específicos de Azure que permiten diferenciar fallbacks."""


class AzureSTTProvider(STTProvider):
    provider_id = "azure-stt"
    latency_ms = 0
    input_seconds = 0.0

    def __init__(self, config: AzureSpeechConfig, fallback: Optional[STTProvider] = None) -> None:
        self._config = config
        self._fallback = fallback

    @staticmethod
    def _require_sdk():
        """Carga perezosa del SDK de Azure.

        Se invoca tanto en `from_env` (para fail-fast de dependencias) como en
        las llamadas reales. No se usa try/except alrededor de imports para no
        ocultar errores genuinos.
        """

        import azure.cognitiveservices.speech as speechsdk  # type: ignore

        return speechsdk

    @classmethod
    def from_env(cls, fallback: Optional[STTProvider] = None) -> "AzureSTTProvider":
        key = os.getenv("AZURE_SPEECH_KEY")
        region = os.getenv("AZURE_SPEECH_REGION")
        language_default = os.getenv("AZURE_SPEECH_STT_LANGUAGE_DEFAULT", "es-ES")
        voice_default = os.getenv("AZURE_SPEECH_TTS_VOICE_DEFAULT", "")

        if not key or not region:
            raise ValueError("Missing Azure Speech credentials: AZURE_SPEECH_KEY/AZURE_SPEECH_REGION")

        try:
            cls._require_sdk()
        except ImportError as exc:
            raise ValueError("Azure Speech SDK is required for Azure providers (pip install azure-cognitiveservices-speech)") from exc

        return cls(
            AzureSpeechConfig(
                key=key,
                region=region,
                stt_language_default=language_default,
                tts_voice_default=voice_default,
            ),
            fallback=fallback,
        )

    def _transcribe_with_sdk(self, audio_bytes: bytes, locale: str) -> STTResult:
        speechsdk = self._require_sdk()

        speech_config = speechsdk.SpeechConfig(subscription=self._config.key, region=self._config.region)
        speech_config.speech_recognition_language = locale or self._config.stt_language_default

        stream = speechsdk.audio.PushAudioInputStream()
        stream.write(audio_bytes)
        stream.close()

        audio_config = speechsdk.audio.AudioConfig(stream=stream)
        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        result = recognizer.recognize_once()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            raw_transcript = {
                "text": result.text,
                "reason": getattr(result.reason, "name", str(result.reason)),
            }
            return STTResult(text=result.text, provider_id=self.provider_id, raw_transcript=raw_transcript)

        if result.reason == speechsdk.ResultReason.NoMatch:
            logger.warning(
                "azure_stt_no_match",
                extra={
                    "provider_id": self.provider_id,
                    "locale": locale,
                    "reason": getattr(result.reason, "name", str(result.reason)),
                },
            )
            raise AzureProviderError("Azure STT returned NoMatch")

        if result.reason == speechsdk.ResultReason.Canceled:
            details = speechsdk.CancellationDetails.from_result(result)
            logger.warning(
                "azure_stt_canceled",
                extra={
                    "provider_id": self.provider_id,
                    "locale": locale,
                    "reason": getattr(details.reason, "name", str(details.reason)),
                    "error_details": getattr(details, "error_details", None),
                },
            )
            raise AzureProviderError(
                f"Azure STT canceled: {details.reason}; {details.error_details}"
            )

        raise AzureProviderError("Azure STT returned unknown result")

    def transcribe(self, audio_bytes: bytes, locale: str) -> STTResult:
        try:
            return self._transcribe_with_sdk(audio_bytes, locale)
        except Exception as exc:  # pragma: no cover - exercised via fallback tests
            logger.warning(
                "azure_stt_error",
                exc_info=exc,
                extra={
                    "provider_id": self.provider_id,
                    "locale": locale,
                    "exc_type": type(exc).__name__,
                },
            )
            if not self._fallback:
                raise

            fallback_result = self._fallback.transcribe(audio_bytes, locale)
            self.latency_ms = getattr(self._fallback, "latency_ms", self.latency_ms)
            self.input_seconds = getattr(self._fallback, "input_seconds", self.input_seconds)
            fallback_result.provider_id = f"{self.provider_id}|{fallback_result.provider_id}"
            return fallback_result


class AzureTTSProvider(TTSProvider):
    provider_id = "azure-tts"
    latency_ms = 0
    output_seconds = 0.0

    def __init__(self, config: AzureSpeechConfig, fallback: Optional[TTSProvider] = None) -> None:
        self._config = config
        self._fallback = fallback

    @staticmethod
    def _require_sdk():
        import azure.cognitiveservices.speech as speechsdk  # type: ignore

        return speechsdk

    @classmethod
    def from_env(cls, fallback: Optional[TTSProvider] = None) -> "AzureTTSProvider":
        key = os.getenv("AZURE_SPEECH_KEY")
        region = os.getenv("AZURE_SPEECH_REGION")
        language_default = os.getenv("AZURE_SPEECH_STT_LANGUAGE_DEFAULT", "es-ES")
        voice_default = os.getenv("AZURE_SPEECH_TTS_VOICE_DEFAULT", "es-ES-AlonsoNeural")

        if not key or not region:
            raise ValueError("Missing Azure Speech credentials: AZURE_SPEECH_KEY/AZURE_SPEECH_REGION")

        try:
            cls._require_sdk()
        except ImportError as exc:
            raise ValueError("Azure Speech SDK is required for Azure providers (pip install azure-cognitiveservices-speech)") from exc

        return cls(
            AzureSpeechConfig(
                key=key,
                region=region,
                stt_language_default=language_default,
                tts_voice_default=voice_default,
            ),
            fallback=fallback,
        )

    def _synthesize_with_sdk(self, text: str, locale: str, voice: str | None = None) -> TTSResult:
        speechsdk = self._require_sdk()

        speech_config = speechsdk.SpeechConfig(subscription=self._config.key, region=self._config.region)
        speech_config.speech_synthesis_language = locale or self._config.stt_language_default
        speech_config.speech_synthesis_voice_name = voice or self._config.tts_voice_default

        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        result = synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            audio_bytes = bytes(result.audio_data)
            return TTSResult(
                audio_bytes=audio_bytes,
                audio_mime_type="audio/wav",
                provider_id=self.provider_id,
                audio_url=None,
            )

        if result.reason == speechsdk.ResultReason.Canceled:
            details = speechsdk.CancellationDetails.from_result(result)
            logger.warning(
                "azure_tts_canceled",
                extra={
                    "provider_id": self.provider_id,
                    "locale": locale,
                    "voice": voice or self._config.tts_voice_default,
                    "reason": getattr(details.reason, "name", str(details.reason)),
                    "error_details": getattr(details, "error_details", None),
                },
            )
            raise AzureProviderError(
                f"Azure TTS canceled: {details.reason}; {details.error_details}"
            )

        raise AzureProviderError("Azure TTS returned unknown result")

    def synthesize(self, text: str, locale: str, voice: str | None = None) -> TTSResult:
        try:
            return self._synthesize_with_sdk(text, locale, voice)
        except Exception as exc:  # pragma: no cover - exercised via fallback tests
            logger.warning(
                "azure_tts_error",
                exc_info=exc,
                extra={
                    "provider_id": self.provider_id,
                    "locale": locale,
                    "voice": voice,
                    "exc_type": type(exc).__name__,
                },
            )
            if not self._fallback:
                raise

            fallback_result = self._fallback.synthesize(text, locale, voice)
            self.latency_ms = getattr(self._fallback, "latency_ms", self.latency_ms)
            self.output_seconds = getattr(self._fallback, "output_seconds", self.output_seconds)
            fallback_result.provider_id = f"{self.provider_id}|{fallback_result.provider_id}"
            return fallback_result


class AzureLLMProvider(LLMProvider):  # pragma: no cover - placeholder
    provider_id = "azure-llm"
    latency_ms = 0

    def generate_reply(self, transcript: str, context: dict) -> str:
        raise NotImplementedError("Azure LLM integration pending")


__all__ = ["AzureSTTProvider", "AzureTTSProvider", "AzureLLMProvider", "AzureSpeechConfig", "AzureProviderError"]
