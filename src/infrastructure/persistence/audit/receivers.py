"""Translate Django auth and axes signals into `RecordSecurityEvent` commands.

Authentication auditing is best-effort by decision (Story 1.8): a transient DB failure must not
stop a child from signing in or out, so `DatabaseError` becomes an alertable ERROR log line.
Business use cases audit inside their own unit of work and fail closed instead.
"""

import logging
from typing import Any

from axes.helpers import get_client_ip_address
from axes.signals import user_locked_out
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db import DatabaseError
from django.dispatch import receiver
from django.http import HttpRequest

from application.accounts.record_security_event import SecurityEvent, SecurityEventCommand
from infrastructure import container

logger = logging.getLogger(__name__)


def _record(
    event: SecurityEvent, username: str, user_id: int | None, request: HttpRequest | None
) -> None:
    ip = get_client_ip_address(request) if request is not None else None
    try:
        container.record_security_event().execute(
            SecurityEventCommand(event, username, user_id, ip)
        )
    except DatabaseError:
        # No PII and no exception text (it may echo SQL parameters): the event name is enough.
        logger.error("audit.write_failed", extra={"audit_action": event.value})


@receiver(user_logged_in, dispatch_uid="audit.login")
def on_login(sender: Any, request: HttpRequest | None, user: Any, **kwargs: Any) -> None:
    _record(SecurityEvent.LOGIN, user.get_username(), user.pk, request)


@receiver(user_logged_out, dispatch_uid="audit.logout")
def on_logout(sender: Any, request: HttpRequest | None, user: Any, **kwargs: Any) -> None:
    if user is not None:
        _record(SecurityEvent.LOGOUT, user.get_username(), user.pk, request)


@receiver(user_login_failed, dispatch_uid="audit.login_failed")
def on_login_failed(
    sender: Any, credentials: dict[str, Any], request: HttpRequest | None = None, **kwargs: Any
) -> None:
    # Django passes cleansed credentials; only the username is ever read.
    _record(SecurityEvent.LOGIN_FAILED, str(credentials.get("username") or ""), None, request)


@receiver(user_locked_out, dispatch_uid="audit.lockout")
def on_lockout(
    sender: Any, request: HttpRequest | None, username: str | None, **kwargs: Any
) -> None:
    _record(SecurityEvent.LOCKOUT, username or "", None, request)
