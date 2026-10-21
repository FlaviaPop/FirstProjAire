import logging
import os
from pathlib import Path

from django.conf import settings
from django.db import DatabaseError, connection
from django.http import HttpRequest, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe

logger = logging.getLogger(__name__)


def _database_ok() -> bool:
    # Directory first (BUG-001): in WAL mode a read-only directory also makes the query fail,
    # and checking it afterwards would report the symptom (DB error) instead of the cause.
    db_dir = Path(str(settings.DATABASES["default"]["NAME"])).parent
    if not os.access(db_dir, os.W_OK):
        logger.error("healthz.data_dir_not_writable")
        return False
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError as exc:
        logger.error("healthz.db_unavailable", extra={"error": type(exc).__name__})
        return False
    return True


@never_cache
@require_safe
def healthz(request: HttpRequest) -> JsonResponse:
    """GET /healthz — public uptime probe; no personal data."""
    if _database_ok():
        return JsonResponse({"status": "ok", "db": "ok"})
    return JsonResponse({"status": "unavailable", "db": "error"}, status=503)
