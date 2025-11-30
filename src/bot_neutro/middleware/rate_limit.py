import os
from typing import Callable, Iterable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

ALLOWLIST: Iterable[str] = {"/metrics", "/healthz", "/readyz"}


def _is_enabled() -> bool:
    return os.getenv("RATE_LIMIT_ENABLED", "false").lower() in {"1", "true", "yes"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Stub middleware to hook rate limiting behavior."""

    def __init__(self, app, allowlist: Iterable[str] | None = None) -> None:
        super().__init__(app)
        self.allowlist = set(allowlist or ALLOWLIST)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not _is_enabled() or request.url.path in self.allowlist:
            return await call_next(request)

        # Placeholder for future enforcement hooks
        limit_reached = False

        if limit_reached:
            response = JSONResponse(
                {"detail": "rate limit exceeded"}, status_code=429
            )
            response.headers["X-Outcome"] = "error"
            response.headers["X-Outcome-Detail"] = "rate_limit"
            correlation_id = getattr(request.state, "correlation_id", None)
            if correlation_id:
                response.headers["X-Correlation-Id"] = correlation_id
            return response

        return await call_next(request)
