"""Read-only access to the append-only audit log in the platform admin."""

from typing import TYPE_CHECKING

from django.contrib import admin
from django.http import HttpRequest

from infrastructure.persistence.accounts.admin_site import platform_admin_site
from infrastructure.persistence.audit.models import AuditLogModel

if TYPE_CHECKING:  # django-stubs generics; the runtime classes are not subscriptable
    AuditAdminBase = admin.ModelAdmin[AuditLogModel]
else:
    AuditAdminBase = admin.ModelAdmin


@admin.register(AuditLogModel, site=platform_admin_site)
class AuditLogAdmin(AuditAdminBase):
    """The audit log, read-only: no add, change or delete (append-only by design)."""

    list_display = (
        "created_at",
        "action",
        "actor_username",
        "target_type",
        "target_id",
        "ip_address",
    )
    list_filter = ("action",)
    search_fields = ("actor_username",)
    date_hierarchy = "created_at"

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: AuditLogModel | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: AuditLogModel | None = None) -> bool:
        return False
