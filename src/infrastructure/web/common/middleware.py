"""Request correlation and the single DomainError → HTTP mapping (patterns §8, §9)."""

import logging
import re
import time
import uuid
from collections.abc import Callable
from typing import Any

from django.conf import settings
from django.db import DatabaseError
from django.http import HttpRequest, HttpResponse

from domain.common.errors import ConflictError, DomainError, NotFound, PolicyViolation
from infrastructure.logging.request_context import request_id_var, role_var, user_id_var
from infrastructure.web.common.errors import render_error

logger = logging.getLogger(__name__)
_VALID_ID = re.compile(r"^[A-Za-z0-9-]{8,64}$")
# Most specific first: the first matching class wins, the DomainError fallback stays last.
_STATUS_BY_ERROR: tuple[tuple[type[DomainError], int], ...] = (
    (NotFound, 404),
    (PolicyViolation, 422),
    (ConflictError, 409),
    (DomainError, 400),
)

GetResponse = Callable[[HttpRequest], HttpResponse]


class RequestIdMiddleware:
    """First middleware: assigns the request id and logs one `request.completed` line."""

    def __init__(self, get_response: GetResponse) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Only the reverse proxy's id is reused (Story 1.1 review v1 ISS-004); an invalid one is
        # replaced and never echoed (header/log injection guard).
        incoming = (
            request.headers.get("X-Request-ID", "") if settings.TRUST_INCOMING_REQUEST_ID else ""
        )
        request_id = incoming if _VALID_ID.match(incoming) else uuid.uuid4().hex
        request.request_id = request_id  # type: ignore[attr-defined]
        request.log_context = (request_id, None, None)  # type: ignore[attr-defined]
        request_id_token = request_id_var.set(request_id)
        user_id_token, role_token = user_id_var.set(None), role_var.set(None)
        started = time.perf_counter()
        try:
            response = self.get_response(request)
            response["X-Request-ID"] = request_id
            logger.info(
                "request.completed",
                extra={
                    "method": request.method,
                    "path": request.path,  # never the query string: it may carry personal data
                    "status": response.status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                },
            )
            return response
        finally:
            # Restore the previous values so nothing leaks into the next request on this thread.
            request_id_var.reset(request_id_token)
            user_id_var.reset(user_id_token)
            role_var.reset(role_token)

    def process_view(
        self, request: HttpRequest, view_func: Any, view_args: Any, view_kwargs: Any
    ) -> None:
        """Runs after AuthenticationMiddleware has attached `request.user`."""
        try:
            user = getattr(request, "user", None)
            if user is None or not user.is_authenticated:
                return
        except DatabaseError:
            # BUG-002: resolving the lazy user reads the session from the DB. Log context is
            # best-effort; the view (e.g. /healthz → 503) must decide, not this middleware (→ 500).
            return
        user_id_var.set(user.pk)
        role_var.set(user.role)
        request.log_context = (request_id_var.get(), user.pk, user.role)  # type: ignore[attr-defined]


class DomainErrorMiddleware:
    """Last middleware: maps DomainError subclasses to 404/422/409/400 in one place."""

    def __init__(self, get_response: GetResponse) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_exception(self, request: HttpRequest, exception: Exception) -> HttpResponse | None:
        if not isinstance(exception, DomainError):
            return None  # Django's handler500 + django.request ERROR logging take over
        status = next(code for err, code in _STATUS_BY_ERROR if isinstance(exception, err))
        logger.info("domain_error", extra={"code": exception.code, "status": status})
        return render_error(request, status, exception)
