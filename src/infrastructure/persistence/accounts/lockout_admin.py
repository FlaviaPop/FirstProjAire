"""Read and clear sign-in lockouts in the platform admin."""

from typing import TYPE_CHECKING

from axes.models import AccessAttempt
from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from application.accounts.record_security_event import EMPTY_USERNAME, UNKNOWN_PREFIX
from infrastructure import container
from infrastructure.persistence.accounts.admin_site import _actor_id, platform_admin_site
from infrastructure.persistence.accounts.models import UserModel
from infrastructure.persistence.audit.fingerprint import username_fingerprint

if TYPE_CHECKING:  # django-stubs generics; the runtime classes are not subscriptable
    LockoutAdminBase = admin.ModelAdmin[AccessAttempt]
else:
    LockoutAdminBase = admin.ModelAdmin


def _lockout_target(username: str | None) -> tuple[int | None, str]:
    """The attempt's account id, or a label that never stores what was typed (owner decision 2)."""
    if not username:
        return None, EMPTY_USERNAME
    user_id = UserModel.objects.filter(username=username).values_list("pk", flat=True).first()
    if user_id is not None:
        return user_id, username
    return None, f"{UNKNOWN_PREFIX}{username_fingerprint(username)}"


@admin.register(AccessAttempt, site=platform_admin_site)
class AccessAttemptAdmin(LockoutAdminBase):
    """django-axes lockouts: deleting an attempt unlocks that username + address."""

    list_display = ("account", "ip_address", "failures_since_start", "attempt_time")
    # Searching for a known username still finds its row; results show the masked label.
    search_fields = ("username", "ip_address")
    # Never the captured GET/POST data, nor the raw typed username: both may echo a password.
    fields = ("account", "ip_address", "failures_since_start", "attempt_time")
    readonly_fields = ("account",)

    @admin.display(description=_("Username"), ordering="username")
    def account(self, obj: AccessAttempt) -> str:
        """The account's username, or "(unknown):<fingerprint>" (review v1 ISS-002)."""
        _user_id, label = _lockout_target(obj.username)
        return label

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: AccessAttempt | None = None) -> bool:
        return False

    def delete_model(self, request: HttpRequest, obj: AccessAttempt) -> None:
        super().delete_model(request, obj)
        self._audit_unlock(request, obj.username)

    def delete_queryset(self, request: HttpRequest, queryset: QuerySet[AccessAttempt]) -> None:
        usernames = list(queryset.values_list("username", flat=True))
        super().delete_queryset(request, queryset)
        for username in usernames:
            self._audit_unlock(request, username)

    def _audit_unlock(self, request: HttpRequest, username: str | None) -> None:
        user_id, label = _lockout_target(username)
        container.audit_account_change().execute(
            "auth.lockout_cleared", _actor_id(request), user_id, label
        )
