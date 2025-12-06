from uuid import uuid4
from typing import Dict, Optional

from fastapi import FastAPI, File, Form, Header, Request, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse

from . import __version__
from .audio_pipeline_stub import (
    AudioRequestContext,
    AudioResponseContext,
    PipelineError,
    StubAudioPipeline,
)
from .audio_storage_inmemory import InMemoryAudioSessionRepository
from .middleware import CorrelationIdMiddleware, JSONLoggingMiddleware, RateLimitMiddleware
from .metrics_runtime import METRICS


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
# HELP errors_total Total errors seen by route
# TYPE errors_total counter
# HELP mem_reads_total Memory reads
# TYPE mem_reads_total counter
# HELP mem_writes_total Memory writes
# TYPE mem_writes_total counter
# HELP sensei_requests_total Total requests by route
# TYPE sensei_requests_total counter
"""


def _with_outcome(response, outcome: str = "ok", detail: str | None = None) -> None:
    response.headers.setdefault("X-Outcome", outcome)
    if detail:
        response.headers["X-Outcome-Detail"] = detail


audio_session_repo = InMemoryAudioSessionRepository()
audio_pipeline = StubAudioPipeline(audio_session_repo)


def create_app() -> FastAPI:
    app = FastAPI(title="bot-neutro", version=__version__)

    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(JSONLoggingMiddleware)

    @app.middleware("http")
    async def set_default_outcome(request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Outcome", "ok")
        return response

    @app.get("/healthz")
    async def healthcheck(request: Request):
        METRICS.inc_request("/healthz")
        response = JSONResponse({"status": "ok"})
        _with_outcome(response)
        return response

    @app.get("/readyz")
    async def readiness(request: Request):
        METRICS.inc_request("/readyz")
        response = JSONResponse({"status": "ok"})
        _with_outcome(response)
        return response

    @app.get("/version")
    async def version(request: Request):
        METRICS.inc_request("/version")
        response = JSONResponse({"version": __version__})
        _with_outcome(response)
        return response

    @app.get("/metrics")
    async def metrics(request: Request):
        METRICS.inc_request("/metrics")
        snapshot = METRICS.snapshot()
        dynamic_lines = []

        dynamic_lines.append(
            f'sensei_rate_limit_hits_total {snapshot["rate_limit_hits_total"]}'
        )
        dynamic_lines.append(f'mem_reads_total {snapshot["mem_reads_total"]}')
        dynamic_lines.append(f'mem_writes_total {snapshot["mem_writes_total"]}')

        for route, value in snapshot["requests_total"].items():
            dynamic_lines.append(f'sensei_requests_total{{route="{route}"}} {value}')

        for route, value in snapshot["errors_total"].items():
            dynamic_lines.append(f'errors_total{{route="{route}"}} {value}')

        payload = METRICS_PAYLOAD + "\n" + "\n".join(dynamic_lines) if dynamic_lines else METRICS_PAYLOAD
        response = PlainTextResponse(
            payload,
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
    async def audio_endpoint(
        request: Request,
        audio_file: UploadFile = File(..., description="Audio en formato soportado"),
        locale: str = Form("es-CO"),
        user_external_id: Optional[str] = Form(None),
    ):
        METRICS.inc_request("/audio")

        corr_id = request.headers.get("X-Correlation-Id") or str(uuid4())
        api_key_id = request.headers.get("X-Api-Key-Id") or request.headers.get("X-API-Key")
        munay_context = request.headers.get("x-munay-context")

        if munay_context and munay_context not in VALID_MUNAY_CONTEXTS:
            METRICS.inc_error("/audio")
            response = JSONResponse(
                {"detail": "invalid x-munay-context"}, status_code=400
            )
            _with_outcome(response, outcome="error", detail="audio.bad_request")
            response.headers.setdefault("X-Correlation-Id", corr_id)
            return response

        audio_bytes = await audio_file.read()
        if not audio_bytes:
            METRICS.inc_error("/audio")
            response = JSONResponse({"detail": "empty audio"}, status_code=400)
            _with_outcome(response, outcome="error", detail="audio.bad_request")
            response.headers.setdefault("X-Correlation-Id", corr_id)
            return response

        mime_type = audio_file.content_type or ""
        client_meta: Dict[str, str] = {}

        munay_user_id = request.headers.get("x-munay-user-id")
        if munay_user_id:
            client_meta["munay_user_id"] = munay_user_id
        if munay_context:
            client_meta["munay_context"] = munay_context

        ctx: AudioRequestContext = {
            "corr_id": corr_id,
            "api_key_id": api_key_id or "",
            "audio_bytes": audio_bytes,
            "mime_type": mime_type,
            "locale": locale,
            "user_external_id": user_external_id,
            "client_meta": client_meta or None,
        }

        result: AudioResponseContext | PipelineError = audio_pipeline.process(ctx)

        if "code" in result:
            status_code, detail_value = ERROR_STATUS_MAPPING.get(
                result["code"], (500, "audio.internal_error")
            )
            METRICS.inc_error("/audio")
            response = JSONResponse(
                {"detail": result.get("message")}, status_code=status_code
            )
            _with_outcome(response, outcome="error", detail=detail_value)
        else:
            body = {
                "session_id": result.get("session_id"),
                "corr_id": result.get("corr_id") or corr_id,
                "transcript": result["transcript"],
                "reply_text": result["reply_text"],
                "tts_url": result.get("tts_url"),
                "usage": {
                    "input_seconds": result["usage"]["input_seconds"],
                    "output_seconds": result["usage"]["output_seconds"],
                    "stt_ms": result["usage"]["stt_ms"],
                    "llm_ms": result["usage"]["llm_ms"],
                    "tts_ms": result["usage"]["tts_ms"],
                    "total_ms": result["usage"]["total_ms"],
                    "provider_stt": result["usage"]["provider_stt"],
                    "provider_llm": result["usage"]["provider_llm"],
                    "provider_tts": result["usage"]["provider_tts"],
                },
                "meta": result.get("meta"),
            }
            response = JSONResponse(body, status_code=200)
            _with_outcome(response, outcome="success", detail="audio_processed")

        response.headers.setdefault("X-Correlation-Id", corr_id)
        return response

    return app


app = create_app()
