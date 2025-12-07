import math
import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from bot_neutro.metrics_runtime import METRICS


class RequestLatencyMiddleware(BaseHTTPMiddleware):
    """Capture latency per request and feed the runtime histogram."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        try:
            response = await call_next(request)
            return response
        finally:
            duration_seconds = time.perf_counter() - start
            route = request.url.path or "unknown"
            if not math.isnan(duration_seconds):
                METRICS.observe_latency(route, duration_seconds)
