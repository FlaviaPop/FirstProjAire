"""Per-request logging context, set by `RequestIdMiddleware` and copied onto every log record."""

import logging
from contextvars import ContextVar

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[int | None] = ContextVar("user_id", default=None)
role_var: ContextVar[str | None] = ContextVar("role", default=None)


LogContext = tuple[str | None, int | None, str | None]  # (request_id, user_id, role)


class RequestContextFilter(logging.Filter):
    """Adds `request_id`, `user_id` and `role` (None outside a request or when anonymous).

    Django writes its django.request 4xx/5xx lines after the middleware chain has returned
    and the context variables were reset. Those records carry the request, so the snapshot
    `RequestIdMiddleware` keeps in `request.log_context` is used instead.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        context: LogContext = (request_id_var.get(), user_id_var.get(), role_var.get())
        if context[0] is None:
            context = getattr(getattr(record, "request", None), "log_context", context)
        record.request_id, record.user_id, record.role = context
        return True
