"""AUDIT_LOG: append-only record of security-relevant actions (architecture Security Design)."""

from typing import Any, NoReturn

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

APPEND_ONLY = "audit_log is append-only"


class _AppendOnlyQuerySet(models.QuerySet["AuditLogModel"]):
    def update(self, **kwargs: Any) -> NoReturn:
        raise PermissionError(APPEND_ONLY)

    def delete(self) -> NoReturn:
        raise PermissionError(APPEND_ONLY)


class AuditLogModel(models.Model):
    # SET_NULL keeps history when an account is deleted; actor_username preserves who it was.
    # Django's deletion collector uses `_base_manager` (a plain Manager), so that update bypasses
    # _AppendOnlyQuerySet. Do NOT set Meta.base_manager_name.
    # Story 1.9: translated labels for the read-only admin screen (no schema change).
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("actor"),
    )
    actor_username = models.CharField(_("actor username"), max_length=150)
    action = models.CharField(_("action"), max_length=64, db_index=True)
    target_type = models.CharField(_("target type"), max_length=32, blank=True)
    target_id = models.CharField(_("target id"), max_length=64, blank=True)
    metadata = models.JSONField(_("metadata"), default=dict)
    ip_address = models.GenericIPAddressField(_("IP address"), null=True)
    created_at = models.DateTimeField(_("time"), db_index=True)

    objects = _AppendOnlyQuerySet.as_manager()

    class Meta:
        db_table = "audit_log"
        verbose_name = _("audit log entry")
        verbose_name_plural = _("audit log entries")
        ordering = ("-created_at",)
        indexes = (
            models.Index(fields=["action", "created_at"], name="audit_action_created_idx"),
            models.Index(fields=["actor", "created_at"], name="audit_actor_created_idx"),
        )

    def __str__(self) -> str:
        return f"{self.action} by {self.actor_username or '-'} at {self.created_at:%Y-%m-%d %H:%M}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            raise PermissionError(APPEND_ONLY)
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise PermissionError(APPEND_ONLY)
