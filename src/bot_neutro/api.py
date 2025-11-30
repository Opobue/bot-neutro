from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from . import __version__
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

    @app.post("/audio")
    async def audio(request: Request):
        response = JSONResponse({"detail": "audio endpoint stub"}, status_code=501)
        _with_outcome(response, outcome="error")
        return response

    return app


app = create_app()
