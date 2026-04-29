"""Request / response logging middleware with 4xx normalisation.

Runs INSIDE `AuthenticateMiddleware` so that, for protected routes,
`request.state.user_id` is already populated and the access log can be
routed to the user-specific log file. Unauthenticated requests (e.g. the
exempt `/auth/login` route) fall back to the system channel.

Any 4xx response other than 400, 401, or 404 is rewritten to a generic
400 to avoid leaking server-side detail.
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from app.db.connector import SessionLocal

from app.logger_utils.log_channels import get_error_logger, get_system_logger, get_user_logger
from app.utils.util_store import authenticate

_ALLOWED_4XX: frozenset[int] = frozenset({400, 401, 403, 404})


def _resolve_logger(request: Request):
    """Pick the right loguru logger for the current request.

    Reads `request.state.user_id` (set by `AuthenticateMiddleware`) and
    also resolves the client host string used in log lines. When no
    `user_id` is present the request is treated as unauthenticated and
    routed to the system channel.

    Args:
        request: The incoming Starlette request.

    Returns:
        loguru.Logger: A logger bound to the user channel when the
            request carries an authenticated `user_id`, otherwise the
            system-channel logger.
    """
    user_id = getattr(request.state, "user_id", None)
    if user_id is not None:
        return get_user_logger(user_id)
    return get_system_logger()


class RequestResponseHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware that logs every request/response pair and normalises 4xx codes."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Log the request, dispatch downstream, normalise 4xx, then log the response.

        Args:
            request: The incoming Starlette request.
            call_next: Callable that invokes the next middleware or route
                handler in the ASGI stack.

        Returns:
            Response: The downstream response. Any 4xx status other than
                400, 401, or 404 is rewritten to a generic 400 JSON body
                `{"detail": "Bad Request"}` to avoid leaking detail.
        """
        client_host = request.client.host if request.client else "unknown"
        _resolve_logger(request).info(
            f"Request: {request.method} {request.url.path} client={client_host}"
        )



        auth_header = request.headers.get('authorization') or ''
        user_id = None
        if auth_header.lower().startswith('bearer '):
            creds = HTTPAuthorizationCredentials(
                scheme='Bearer',
                credentials=auth_header.split(' ', 1)[1],
            )
            with SessionLocal() as db:
                try:
                    user_id = authenticate(creds, db).user_id
                except Exception:
                    user_id = None
        request.state.user_id = user_id

        try:
            response = await call_next(request)
        except Exception as exc:
            get_error_logger().opt(exception=exc).error(
                f"Unhandled error: {request.method} {request.url.path} client={client_host}"
            )
            raise

        if 400 <= response.status_code < 500 and response.status_code not in _ALLOWED_4XX:
            response = JSONResponse(
                status_code=400, content={"detail": "Bad Request"}
            )

        _resolve_logger(request).info(
            f"Response: {request.method} {request.url.path} -> {response.status_code}"
        )

        return response
