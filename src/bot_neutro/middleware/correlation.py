import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Ensure every request carries an X-Correlation-Id header."""

    header_name = "X-Correlation-Id"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = request.headers.get(self.header_name) or str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        response = await call_next(request)
        response.headers[self.header_name] = correlation_id
        return response
