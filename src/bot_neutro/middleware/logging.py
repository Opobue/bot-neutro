import json
import logging
from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("bot_neutro")
logging.basicConfig(level=logging.INFO)


class JSONLoggingMiddleware(BaseHTTPMiddleware):
    """Emit structured JSON logs for inbound requests."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)

        payload = {
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "corr_id": getattr(request.state, "correlation_id", ""),
        }
        logger.info(json.dumps(payload))
        return response
