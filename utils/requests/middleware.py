"""Middleware for Correlation IDs."""
import logging
import uuid
from contextvars import ContextVar

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from settings import APP_NAME

CORRELATION_ID_HEADER_KEY = "X-Correlation-Id"
CORRELATION_ID_CONTEXT_KEY = "correlation_id"
UUID_ZERO = str(uuid.UUID(int=0))

correlation_id_context: ContextVar[str] = ContextVar(CORRELATION_ID_CONTEXT_KEY, default=UUID_ZERO)


class CorrelationIdFilter(logging.Filter):
    """Filter to provide additional fields to log format."""

    def filter(self, record):
        record.correlation_id = correlation_id_context.get()
        record.app_name = APP_NAME
        return True


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Add a Correlation ID in headers for all requests."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        correlation_id_context.set(request.headers.get(CORRELATION_ID_HEADER_KEY, str(uuid.uuid4())))
        correlation_id = correlation_id_context.get()

        new_headers = request.headers.mutablecopy()
        new_headers[CORRELATION_ID_HEADER_KEY] = correlation_id
        request._headers = new_headers
        request.scope.update(headers=request.headers.raw)

        try:
            response = await call_next(request)
            response.headers[CORRELATION_ID_HEADER_KEY] = correlation_id
            return response

        except Exception as err:
            logging.error(f"Unhandled Exception: {type(err)} {err}", exc_info=True) # NOQA
