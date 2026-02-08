"""
Request ID middleware for tracking requests across logs.
"""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.logger import logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Adds unique request ID to each request.
    Useful for correlating logs across multiple services.
    """

    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Log request
        logger.info(f"Request started: {request.method} {request.url.path} | ID: {request_id}")

        # Process request
        response = await call_next(request)

        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} | "
            f"Status: {response.status_code} | ID: {request_id}"
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response
