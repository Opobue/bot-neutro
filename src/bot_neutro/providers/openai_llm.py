"""OpenAI LLM provider implementation."""

import logging
import os
import time
from typing import Optional

from .interfaces import LLMProvider

logger = logging.getLogger(__name__)


class OpenAILLMProvider(LLMProvider):
    provider_id = "openai-llm"
    latency_ms = 0

    def __init__(
        self,
        api_key: str,
        model_freemium: str,
        model_premium: Optional[str] = None,
        base_url: Optional[str] = None,
        fallback: Optional[LLMProvider] = None,
        timeout_seconds: Optional[float] = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._model_freemium = model_freemium
        self._model_premium = model_premium or model_freemium
        self._fallback = fallback
        self._timeout_seconds = timeout_seconds
        self._client = None
        self._client_factory = self._require_client()

    @staticmethod
    def _require_client():
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - defensive path
            raise RuntimeError("openai SDK not installed") from exc
        return OpenAI

    @classmethod
    def from_env(cls, fallback: Optional[LLMProvider] = None) -> "OpenAILLMProvider":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required for OpenAILLMProvider")

        model_freemium = os.getenv("OPENAI_MODEL_FREEMIUM")
        if not model_freemium:
            raise RuntimeError("OPENAI_MODEL_FREEMIUM is required for OpenAILLMProvider")

        model_premium = os.getenv("OPENAI_MODEL_PREMIUM")
        base_url = os.getenv("OPENAI_BASE_URL")
        timeout_env = os.getenv("OPENAI_TIMEOUT_SECONDS")
        timeout_seconds = float(timeout_env) if timeout_env else None

        return cls(
            api_key=api_key,
            model_freemium=model_freemium,
            model_premium=model_premium,
            base_url=base_url,
            fallback=fallback,
            timeout_seconds=timeout_seconds,
        )

    def _get_client(self):
        if self._client is None:
            self._client = self._client_factory(api_key=self._api_key, base_url=self._base_url)
        return self._client

    def generate_reply(self, transcript: str, context: dict) -> str:
        tier = context.get("llm_tier", "freemium") if context else "freemium"
        model = self._model_premium if tier == "premium" else self._model_freemium

        start = time.perf_counter()
        client = self._get_client()

        messages = [
            {"role": "system", "content": "Eres el núcleo neutral de Bot Neutro. Responde claro y breve."},
            {"role": "user", "content": transcript},
        ]

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                timeout=self._timeout_seconds,
            )
            reply = response.choices[0].message.content.strip()
            self.latency_ms = int((time.perf_counter() - start) * 1000)
            return reply
        except Exception as exc:  # pragma: no cover - requires network
            logger.warning(
                "openai_llm_error",
                exc_info=exc,
                extra={"provider_id": self.provider_id, "tier": tier, "model": model},
            )
            fallback = self._fallback
            if fallback:
                reply = fallback.generate_reply(transcript, context)
                self.latency_ms = getattr(fallback, "latency_ms", self.latency_ms)
                self.provider_id = f"{self.provider_id}|{fallback.provider_id}"
                return reply
            raise
