import os
import time
from threading import Lock
from typing import Callable, Dict, Iterable, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from bot_neutro.metrics_runtime import METRICS

ALLOWLIST: Iterable[str] = {"/metrics", "/healthz", "/readyz", "/version"}


def _is_enabled() -> bool:
    return os.getenv("RATE_LIMIT_ENABLED", "0") == "1"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Stub middleware to hook rate limiting behavior."""

    def __init__(self, app, allowlist: Iterable[str] | None = None) -> None:
        super().__init__(app)
        self.allowlist = set(allowlist or ALLOWLIST)
        self._state: Dict[Tuple[str, str], Dict[str, float | int]] = {}
        self._lock = Lock()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        if not _is_enabled() or path in self.allowlist:
            return await call_next(request)

        if path != "/audio":
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return await call_next(request)

        window_seconds = int(os.getenv("RATE_LIMIT_AUDIO_WINDOW_SECONDS", "60"))
        max_requests = int(os.getenv("RATE_LIMIT_AUDIO_MAX_REQUESTS", "60"))
        now = time.time()
        key = (path, api_key)

        with self._lock:
            entry = self._state.get(key)
            if entry is None or now - entry["window_start"] >= window_seconds:
                entry = {"window_start": now, "count": 0}
                self._state[key] = entry

            if entry["count"] >= max_requests:
                retry_after = max(0, int(window_seconds - (now - entry["window_start"])))
                response = JSONResponse(
                    {"detail": "rate limit exceeded"}, status_code=429
                )
                response.headers["X-Outcome"] = "error"
                response.headers["X-Outcome-Detail"] = "rate_limit"
                correlation_id = getattr(request.state, "correlation_id", None)
                if correlation_id:
                    response.headers["X-Correlation-Id"] = correlation_id
                response.headers["Retry-After"] = str(retry_after)
                METRICS.inc_rate_limit_hit()
                return response

            entry["count"] += 1

        return await call_next(request)
