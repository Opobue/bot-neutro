from uuid import uuid4
from typing import Dict, Optional

from fastapi import FastAPI, File, Header, Request, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse

from . import __version__
from .audio_pipeline_stub import AudioRequestContext, StubAudioPipeline
from .middleware import CorrelationIdMiddleware, JSONLoggingMiddleware, RateLimitMiddleware


METRICS_PAYLOAD = """# HELP sensei_request_latency_seconds Request latency
# TYPE sensei_request_latency_seconds histogram
sensei_request_latency_seconds_bucket{route="/healthz",le="0.1"} 0
sensei_request_latency_seconds_bucket{route="/healthz",le="0.5"} 0
sensei_request_latency_seconds_bucket{route="/healthz",le="1.0"} 0
sensei_request_latency_seconds_bucket{route="/healthz",le="+Inf"} 1
sensei_request_latency_seconds_count{route="/healthz"} 1
sensei_request_latency_seconds_sum{route="/healthz"} 0.01
# HELP sensei_rate_limit_hits_total Total requests rejected by rate limit
# TYPE sensei_rate_limit_hits_total counter
sensei_rate_limit_hits_total 0
# HELP errors_total Total errors seen by route
# TYPE errors_total counter
errors_total{route="/audio"} 0
# HELP mem_reads_total Memory reads
# TYPE mem_reads_total counter
mem_reads_total 0
# HELP mem_writes_total Memory writes
# TYPE mem_writes_total counter
mem_writes_total 0
# HELP sensei_requests_total Total requests by route
# TYPE sensei_requests_total counter
sensei_requests_total{route="/metrics"} 1
"""


def _with_outcome(response, outcome: str = "ok", detail: str | None = None) -> None:
    response.headers.setdefault("X-Outcome", outcome)
    if detail:
        response.headers["X-Outcome-Detail"] = detail


def create_app() -> FastAPI:
    app = FastAPI(title="bot-neutro", version=__version__)

    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(JSONLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)

    @app.middleware("http")
    async def set_default_outcome(request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Outcome", "ok")
        return response

    @app.get("/healthz")
    async def healthcheck(request: Request):
        response = JSONResponse({"status": "ok"})
        _with_outcome(response)
        return response

    @app.get("/readyz")
    async def readiness(request: Request):
        response = JSONResponse({"status": "ok"})
        _with_outcome(response)
        return response

    @app.get("/version")
    async def version(request: Request):
        response = JSONResponse({"version": __version__})
        _with_outcome(response)
        return response

    @app.get("/metrics")
    async def metrics(request: Request):
        response = PlainTextResponse(
            METRICS_PAYLOAD,
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )
        _with_outcome(response)
        return response

    ERROR_STATUS_MAPPING = {
        "bad_request": (400, "audio.bad_request"),
        "unsupported_media_type": (415, "audio.unsupported_media_type"),
        "unauthorized": (401, "auth.unauthorized"),
        "stt_error": (502, "audio.stt_error"),
        "llm_error": (502, "audio.llm_error"),
        "tts_error": (502, "audio.tts_error"),
        "provider_timeout": (504, "audio.provider_timeout"),
        "storage_error": (503, "audio.storage_error"),
        "internal_error": (500, "audio.internal_error"),
    }

    VALID_MUNAY_CONTEXTS = {"diario_emocional", "coach_habitos", "reflexion_general"}

    @app.post("/audio")
    async def audio(
        file: UploadFile = File(...),
        x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
        x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-Id"),
        x_munay_user_id: Optional[str] = Header(None, alias="x-munay-user-id"),
        x_munay_context: Optional[str] = Header(None, alias="x-munay-context"),
    ):
        corr_id = x_correlation_id or str(uuid4())

        if file is None:
            result = {"code": "bad_request", "message": "file required", "details": None}
        else:
            mime_type = file.content_type or ""
            if not mime_type.startswith("audio/"):
                result = {
                    "code": "unsupported_media_type",
                    "message": "unsupported media type",
                    "details": {"mime_type": mime_type},
                }
            else:
                raw_audio = await file.read()
                if not raw_audio:
                    result = {"code": "bad_request", "message": "empty audio", "details": None}
                elif x_munay_context and x_munay_context not in VALID_MUNAY_CONTEXTS:
                    result = {
                        "code": "bad_request",
                        "message": "invalid x-munay-context",
                        "details": {"x-munay-context": x_munay_context},
                    }
                else:
                    client_metadata: Dict[str, str] = {}

                    if x_munay_user_id:
                        client_metadata["munay_user_id"] = x_munay_user_id
                    if x_munay_context:
                        client_metadata["munay_context"] = x_munay_context

                    ctx: AudioRequestContext = {
                        "corr_id": corr_id,
                        "api_key_id": x_api_key or "",
                        "raw_audio": raw_audio,
                        "mime_type": mime_type,
                        "language_hint": None,
                        "client_metadata": client_metadata or None,
                    }
                    pipeline = StubAudioPipeline()
                    result = pipeline.process(ctx)

        if "code" in result:
            status_code, detail_value = ERROR_STATUS_MAPPING.get(
                result["code"], (500, "audio.internal_error")
            )
            response = JSONResponse({"detail": result.get("message")}, status_code=status_code)
            _with_outcome(response, outcome="error", detail=detail_value)
        else:
            response_body = {
                "transcript": result["transcript"],
                "reply_text": result["reply_text"],
                "audio_url": result["tts_audio_url"],
                "usage": {
                    "stt_ms": result["usage"]["stt_ms"],
                    "llm_ms": result["usage"]["llm_ms"],
                    "tts_ms": result["usage"]["tts_ms"],
                    "total_ms": result["usage"]["total_ms"],
                    "provider_stt": result["usage"]["provider_stt"],
                    "provider_llm": result["usage"]["provider_llm"],
                    "provider_tts": result["usage"]["provider_tts"],
                },
                "session_id": result["session_id"],
            }
            response = JSONResponse(response_body)
            _with_outcome(response, outcome="ok")

        response.headers.setdefault("X-Correlation-Id", corr_id)
        return response

    return app


app = create_app()
