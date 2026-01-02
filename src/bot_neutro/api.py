import logging
import os
from typing import Any, Awaitable, Callable, Dict, Optional, cast
from uuid import uuid4

from fastapi import FastAPI, File, Form, Header, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from . import __version__
from .audio_pipeline import AudioPipeline, AudioRequestContext, AudioResponseContext, PipelineError
from .audio_storage import get_default_audio_session_repository
from .llm_tiers import (
    TierInvalidError,
    effective_tier,
    is_forbidden,
    normalize_requested_tier,
    resolve_authorized_tier,
)
from .metrics_runtime import METRICS
from .middleware import (
    CorrelationIdMiddleware,
    JSONLoggingMiddleware,
    RateLimitMiddleware,
    RequestLatencyMiddleware,
)
from .providers.factory import build_llm_provider, build_stt_provider, build_tts_provider
from .security_ids import derive_api_key_id

METRICS_PAYLOAD = """# HELP sensei_request_latency_seconds Request latency
# TYPE sensei_request_latency_seconds histogram
# HELP sensei_rate_limit_hits_total Total requests rejected by rate limit
# TYPE sensei_rate_limit_hits_total counter
# HELP errors_total Total errors seen by route
# TYPE errors_total counter
# HELP llm_tier_denied_total Total denied LLM tier requests
# TYPE llm_tier_denied_total counter
# HELP mem_reads_total Memory reads
# TYPE mem_reads_total counter
# HELP mem_writes_total Memory writes
# TYPE mem_writes_total counter
# HELP audio_sessions_purged_total Audio sessions purged from storage
# TYPE audio_sessions_purged_total counter
# HELP audio_sessions_current Current audio sessions stored
# TYPE audio_sessions_current gauge
# HELP sensei_requests_total Total requests by route
# TYPE sensei_requests_total counter
"""


def _parse_stats_max_sessions() -> int:
    raw = os.getenv("AUDIO_STATS_MAX_SESSIONS", "20000")
    try:
        value = int(raw)
    except ValueError:
        return 20000
    if value < 0:
        return 0
    return value


STATS_MAX_SESSIONS = _parse_stats_max_sessions()

def _parse_cors_origins() -> list[str]:
    raw = os.getenv("MUNAY_CORS_ORIGINS", "")
    if not raw:
        return ["http://localhost:5173", "http://127.0.0.1:5173"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


CORS_ORIGINS = _parse_cors_origins()


def _with_outcome(response: Response, outcome: str = "ok", detail: str | None = None) -> None:
    response.headers.setdefault("X-Outcome", outcome)
    if outcome == "error" and detail is not None:
        response.headers["X-Outcome-Detail"] = detail


logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="bot-neutro", version=__version__)
    app.state.audio_session_repo = get_default_audio_session_repository()
    app.state.audio_pipeline = AudioPipeline(
        session_repo=app.state.audio_session_repo,
        stt_provider=build_stt_provider(),
        tts_provider=build_tts_provider(),
        llm_provider=build_llm_provider(),
    )


    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(RequestLatencyMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(JSONLoggingMiddleware)

    @app.middleware("http")
    async def set_default_outcome(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Outcome", "ok")
        return response

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> Response:
        corr_id = request.headers.get("X-Correlation-Id") or str(uuid4())
        logger.exception(
            "Unhandled exception",
            exc_info=exc,
            extra={"corr_id": corr_id}
        )
        response = JSONResponse(
            {"detail": "Internal Server Error"},
            status_code=500
        )
        _with_outcome(response, outcome="error", detail="internal_error")
        response.headers["X-Correlation-Id"] = corr_id
        return response

    @app.get("/healthz")
    async def healthcheck(request: Request) -> JSONResponse:
        METRICS.inc_request("/healthz")
        response = JSONResponse({"status": "ok"})
        _with_outcome(response)
        return response

    @app.get("/readyz")
    async def readiness(request: Request) -> JSONResponse:
        METRICS.inc_request("/readyz")
        response = JSONResponse({"status": "ok"})
        _with_outcome(response)
        return response

    @app.get("/version")
    async def version(request: Request) -> JSONResponse:
        METRICS.inc_request("/version")
        response = JSONResponse({"version": __version__})
        _with_outcome(response)
        return response

    @app.get("/metrics")
    async def metrics(request: Request) -> PlainTextResponse:
        METRICS.inc_request("/metrics")
        snapshot = METRICS.snapshot()
        dynamic_lines = []

        for route, latency in snapshot["latency"].items():
            for bound in snapshot["latency_bucket_bounds"]:
                bound_label = "+Inf" if bound == float("inf") else str(bound)
                value = latency["buckets"].get(bound, 0)
                dynamic_lines.append(
                    f'sensei_request_latency_seconds_bucket{{route="{route}",'
                    f'le="{bound_label}"}} {value}'
                )
            dynamic_lines.append(
                f'sensei_request_latency_seconds_count{{route="{route}"}} {latency["count"]}'
            )
            dynamic_lines.append(
                f'sensei_request_latency_seconds_sum{{route="{route}"}} {latency["sum"]}'
            )

        dynamic_lines.append(
            f'sensei_rate_limit_hits_total {snapshot["rate_limit_hits_total"]}'
        )
        dynamic_lines.append(f'mem_reads_total {snapshot["mem_reads_total"]}')
        dynamic_lines.append(f'mem_writes_total {snapshot["mem_writes_total"]}')
        dynamic_lines.append(
            f'audio_sessions_purged_total {snapshot["audio_sessions_purged_total"]}'
        )
        dynamic_lines.append(
            f'audio_sessions_current {snapshot["audio_sessions_current"]}'
        )

        for route, value in snapshot["requests_total"].items():
            dynamic_lines.append(f'sensei_requests_total{{route="{route}"}} {value}')

        for route, value in snapshot["errors_total"].items():
            dynamic_lines.append(f'errors_total{{route="{route}"}} {value}')

        for item in snapshot.get("llm_tier_denied_total", []):
            dynamic_lines.append(
                "llm_tier_denied_total"
                f'{{route="{item["route"]}",requested_tier="{item["requested_tier"]}",'
                f'authorized_tier="{item["authorized_tier"]}"}} {item["value"]}'
            )

        payload = METRICS_PAYLOAD + "\n".join(dynamic_lines)
        response = PlainTextResponse(
            payload,
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )
        _with_outcome(response)
        return response

    @app.get("/audio/stats")
    async def audio_stats(
        request: Request, x_api_key: Optional[str] = Header(None, alias="X-API-Key")
    ) -> JSONResponse:
        """
        Stats agregados por tenant. NO expone sesiones ni PII.
        Cumple CONTRATO_NEUTRO_AUDIO_STATS_V1 + POLITICA_PRIVACIDAD_SESIONES.
        """

        corr_id = request.headers.get("X-Correlation-Id") or str(uuid4())
        if not x_api_key:
            response = JSONResponse({"detail": "X-API-Key required"}, status_code=401)
            _with_outcome(response, outcome="error", detail="auth.missing_api_key")
            response.headers.setdefault("X-Correlation-Id", corr_id)
            return response

        METRICS.inc_request("/audio/stats")

        api_key_id = derive_api_key_id(x_api_key)
        sessions = request.app.state.audio_session_repo.list_by_api_key(
            api_key_id,
            limit=STATS_MAX_SESSIONS,
            offset=0,
            api_key_id_autenticada=api_key_id,
        )

        by_stt: Dict[str, int] = {}
        by_llm: Dict[str, int] = {}
        by_tts: Dict[str, int] = {}
        for session in sessions:
            by_stt[session["provider_stt"]] = by_stt.get(session["provider_stt"], 0) + 1
            by_llm[session["provider_llm"]] = by_llm.get(session["provider_llm"], 0) + 1
            by_tts[session["provider_tts"]] = by_tts.get(session["provider_tts"], 0) + 1

        snapshot = METRICS.snapshot()
        payload = {
            "api_key_id": api_key_id,
            "totals": {
                "sessions_current": len(sessions),
                "limit_applied": STATS_MAX_SESSIONS,
                "sessions_purged_total": snapshot.get("audio_sessions_purged_total", 0),
            },
            "by_provider": {
                "stt": by_stt,
                "llm": by_llm,
                "tts": by_tts,
            },
        }

        response = JSONResponse(payload)
        _with_outcome(response)
        response.headers.setdefault("X-Correlation-Id", corr_id)
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
        x_munay_llm_tier: Optional[str] = Header(
            default=None, alias="x-munay-llm-tier"
        ),
    ) -> Response:
        METRICS.inc_request("/audio")

        corr_id = request.headers.get("X-Correlation-Id") or str(uuid4())
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            METRICS.inc_error("/audio")
            response = JSONResponse({"detail": "X-API-Key required"}, status_code=401)
            _with_outcome(response, outcome="error", detail="auth.unauthorized")
            response.headers.setdefault("X-Correlation-Id", corr_id)
            return response
        api_key_id = derive_api_key_id(api_key)
        munay_context = request.headers.get("x-munay-context")

        try:
            requested_tier = normalize_requested_tier(x_munay_llm_tier)
        except TierInvalidError:
            METRICS.inc_error("/audio")
            response = JSONResponse({"detail": "llm.tier_invalid"}, status_code=400)
            _with_outcome(response, outcome="error", detail="llm.tier_invalid")
            response.headers.setdefault("X-Correlation-Id", corr_id)
            return response

        authorized_tier = resolve_authorized_tier(api_key)

        if is_forbidden(requested_tier, authorized_tier):
            METRICS.inc_error("/audio")
            METRICS.inc_llm_tier_denied_total(
                "/audio",
                requested_tier,
                authorized_tier,
            )
            logger.info(
                "llm_tier_denied",
                extra={
                    "event": "llm_tier_denied",
                    "requested_tier": requested_tier,
                    "authorized_tier": authorized_tier,
                    "api_key_id": api_key_id,
                    "corr_id": corr_id,
                },
            )
            response = JSONResponse({"detail": "llm.tier_forbidden"}, status_code=403)
            _with_outcome(response, outcome="error", detail="llm.tier_forbidden")
            response.headers.setdefault("X-Correlation-Id", corr_id)
            return response

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

        llm_tier = effective_tier(requested_tier, authorized_tier)

        ctx: AudioRequestContext = {
            "corr_id": corr_id,
            "api_key_id": api_key_id or "",
            "audio_bytes": audio_bytes,
            "mime_type": mime_type,
            "locale": locale,
            "user_external_id": user_external_id,
            "client_meta": client_meta or None,
        }

        ctx["llm_tier"] = llm_tier

        result: AudioResponseContext | PipelineError = request.app.state.audio_pipeline.process(ctx)

        if "code" in cast(Dict[str, Any], result):
            err = cast(PipelineError, result)
            status_code, detail_value = ERROR_STATUS_MAPPING.get(
                err["code"], (500, "audio.internal_error")
            )
            METRICS.inc_error("/audio")
            response = JSONResponse(
                {"detail": err.get("message")}, status_code=status_code
            )
            _with_outcome(response, outcome="error", detail=detail_value)
        else:
            res = cast(AudioResponseContext, result)
            body = {
                "session_id": res.get("session_id"),
                "corr_id": res.get("corr_id") or corr_id,
                "transcript": res["transcript"],
                "reply_text": res["reply_text"],
                "tts_url": res.get("tts_url"),
                "usage": {
                    "input_seconds": res["usage"]["input_seconds"],
                    "output_seconds": res["usage"]["output_seconds"],
                    "stt_ms": res["usage"]["stt_ms"],
                    "llm_ms": res["usage"]["llm_ms"],
                    "tts_ms": res["usage"]["tts_ms"],
                    "total_ms": res["usage"]["total_ms"],
                    "provider_stt": res["usage"]["provider_stt"],
                    "provider_llm": res["usage"]["provider_llm"],
                    "provider_tts": res["usage"]["provider_tts"],
                },
                "meta": res.get("meta"),
            }
            response = JSONResponse(body, status_code=200)
            _with_outcome(response, outcome="success")

        response.headers.setdefault("X-Correlation-Id", corr_id)
        return response

    return app


_APP: FastAPI | None = None


def get_app() -> FastAPI:
    global _APP
    if _APP is None:
        _APP = create_app()
    return _APP
