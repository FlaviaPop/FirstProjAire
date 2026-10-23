"""The platform admin area (Story 1.9): accounts, parent-child links, lockouts, audit log.

Architecture §Roles & Authorization: Django admin is limited to the Admin role and used only for
account CRUD, password resets and parent-child links (plus unlocking and reading the audit log).
Every model is registered on `platform_admin_site` only; the default `admin.site` is never routed.
"""

from collections.abc import Callable, Iterable
from functools import wraps
from typing import TYPE_CHECKING, Any, TypeVar, cast

from axes.models import AccessAttempt
from django.contrib import admin, messages
from django.contrib.admin.actions import delete_selected as django_delete_selected
from django.contrib.admin.utils import unquote
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseBase, HttpResponseRedirect
from django.shortcuts import resolve_url
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from application.accounts.link_parent import LinkExists, LinkParentCommand
from application.accounts.record_security_event import EMPTY_USERNAME, UNKNOWN_PREFIX
from infrastructure import container
from infrastructure.persistence.accounts.admin_forms import (
    LAST_ADMIN,
    ParentChildLinkForm,
    PlatformUserChangeForm,
    PlatformUserCreationForm,
    is_last_active_admin,
    leaves_no_active_admin,
)
from infrastructure.persistence.accounts.models import ParentChildLinkModel, UserModel
from infrastructure.persistence.audit.fingerprint import username_fingerprint
from infrastructure.persistence.audit.models import AuditLogModel

ViewT = TypeVar("ViewT", bound=Callable[..., HttpResponseBase])
if TYPE_CHECKING:  # django-stubs generics; the runtime classes are not subscriptable
    from django.forms import ModelForm

    UserAdminBase = UserAdmin[UserModel]
    LinkAdminBase = admin.ModelAdmin[ParentChildLinkModel]
    AttemptAdminBase = admin.ModelAdmin[AccessAttempt]
    AuditAdminBase = admin.ModelAdmin[AuditLogModel]
else:
    UserAdminBase = UserAdmin
    LinkAdminBase = AttemptAdminBase = AuditAdminBase = admin.ModelAdmin
# Apps this module doesn't own: their AppConfig names are English-only ("Axes", "Audit").
APP_NAMES = {"axes": _("Sign-in lockouts")}


class PlatformAdminSite(admin.AdminSite):
    """Admin site open to active Admin-role accounts only; everyone else never sees a form."""

    site_header = site_title = _("Learning Platform administration")
    index_title = _("Accounts and links")

    def has_permission(self, request: HttpRequest) -> bool:
        user = request.user
        return bool(user.is_active and getattr(user, "role", "") == "ADMIN")

    def admin_view(self, view: ViewT, cacheable: bool = False) -> ViewT:
        # Checked before Django's own wrapper, which would redirect to the admin login form:
        # the platform answers 403, or sends visitors to the platform sign-in (RBAC table).
        wrapped = super().admin_view(view, cacheable)

        @wraps(wrapped)
        def guarded(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
            if not self.has_permission(request):
                return self.login(request)
            return wrapped(request, *args, **kwargs)

        return cast("ViewT", guarded)

    def login(self, request: HttpRequest, extra_context: Any = None) -> HttpResponse:
        if self.has_permission(request):
            return HttpResponseRedirect(reverse("admin:index", current_app=self.name))
        if request.user.is_authenticated:
            raise PermissionDenied  # signed in but not Admin: never a second login form
        return redirect_to_login(request.get_full_path(), resolve_url("accounts:login"))

    def password_change(self, request: HttpRequest, extra_context: Any = None) -> Any:
        """The Admin's own password change, audited like a reset by another Admin."""
        with transaction.atomic():
            before = _password_hash(_actor_id(request))
            response = super().password_change(request, extra_context)
            if _password_hash(_actor_id(request)) != before:
                _audit("accounts.password_changed", request, request.user)
        return response

    def get_app_list(self, request: HttpRequest, app_label: str | None = None) -> list[Any]:
        apps = super().get_app_list(request, app_label)
        for app in apps:
            app["name"] = APP_NAMES.get(app["app_label"], app["name"])
        return apps


platform_admin_site = PlatformAdminSite(name="admin")
DELETE_SELECTED_LABEL = django_delete_selected.short_description  # type: ignore[attr-defined]


def _actor_id(request: HttpRequest) -> int:
    # Admin views only run for a signed-in Admin (PlatformAdminSite.admin_view): never None.
    return cast("int", request.user.pk)


def _password_hash(user_id: int) -> str:
    return UserModel.objects.filter(pk=user_id).values_list("password", flat=True).first() or ""


def _audit(action: str, request: HttpRequest, user: Any, fields: Iterable[str] = ()) -> None:
    container.audit_account_change().execute(
        action, _actor_id(request), user.pk, user.get_username(), fields
    )


@admin.action(permissions=["delete"], description=DELETE_SELECTED_LABEL)
def delete_selected(
    modeladmin: "UserAdminBase", request: HttpRequest, queryset: QuerySet[UserModel]
) -> Any:
    """Bulk delete, refused when it would remove every active Admin (owner decision 4).

    Named like Django's site-wide action so it replaces it for accounts only.
    """
    if leaves_no_active_admin(queryset.values_list("pk", flat=True)):
        modeladmin.message_user(request, LAST_ADMIN, messages.ERROR)
        return None
    return django_delete_selected(modeladmin, request, queryset)


@admin.register(UserModel, site=platform_admin_site)
class PlatformUserAdmin(UserAdminBase):
    """Accounts: create, edit, deactivate, delete and reset passwords - all audited."""

    form = PlatformUserChangeForm
    add_form = PlatformUserCreationForm
    actions = (delete_selected,)
    list_display = (
        "username",
        "full_name",
        "role",
        "preferred_language",
        "is_active",
        "last_login",
    )
    list_filter = ("role", "is_active", "preferred_language")
    search_fields = ("username", "full_name")
    ordering = ("username",)
    filter_horizontal = ()
    readonly_fields = ("last_login", "date_joined")
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("full_name", "date_of_birth", "preferred_language")}),
        (_("Access"), {"fields": ("role", "is_active")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "full_name",
                    "date_of_birth",
                    "role",
                    "preferred_language",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    def has_delete_permission(self, request: HttpRequest, obj: UserModel | None = None) -> bool:
        # The last active Admin can't be deleted (owner decision 4): no button, a POST gets 403.
        if obj is not None and is_last_active_admin(obj):
            return False
        return super().has_delete_permission(request, obj)

    def save_model(
        self, request: HttpRequest, obj: UserModel, form: "ModelForm[UserModel]", change: bool
    ) -> None:
        super().save_model(request, obj, form, change)  # inside the admin's transaction
        fields = form.changed_data
        _audit("accounts.updated" if change else "accounts.created", request, obj, fields)
        if change and "role" in fields:
            _audit("accounts.role_changed", request, obj, ["role"])

    def delete_model(self, request: HttpRequest, obj: UserModel) -> None:
        # Audit first: the row must reference the Admin while it can (they may delete themselves).
        _audit("accounts.deleted", request, obj)
        super().delete_model(request, obj)

    def delete_queryset(self, request: HttpRequest, queryset: QuerySet[UserModel]) -> None:
        for user in queryset:
            _audit("accounts.deleted", request, user)
        super().delete_queryset(request, queryset)

    def user_change_password(self, request: HttpRequest, id: str, form_url: str = "") -> Any:
        """Password reset by the Admin; audited only when the stored hash really changed."""
        with transaction.atomic():
            user = self.get_object(request, unquote(id))
            before = _password_hash(user.pk) if user else ""
            response = super().user_change_password(request, id, form_url)
            if user is not None and _password_hash(user.pk) != before:
                _audit("accounts.password_changed", request, user)
        return response


@admin.register(ParentChildLinkModel, site=platform_admin_site)
class ParentChildLinkAdmin(LinkAdminBase):
    """Parent-child links are created or deleted through the use cases, never edited."""

    form = ParentChildLinkForm
    list_display = ("parent", "student", "created_by", "created_at")
    list_select_related = ("parent", "student", "created_by")
    search_fields = ("parent__username", "parent__full_name", "student__username")
    ordering = ("parent__username", "student__username")

    def has_change_permission(
        self, request: HttpRequest, obj: ParentChildLinkModel | None = None
    ) -> bool:
        return False  # the change page is a read-only view

    def get_form(
        self, request: HttpRequest, obj: Any = None, change: bool = False, **kwargs: Any
    ) -> Any:
        form = cast("type[ParentChildLinkForm]", super().get_form(request, obj, change, **kwargs))
        form.actor_id = _actor_id(request)  # identity from the session only (IDOR guard)
        form.lost_race = getattr(request, "link_lost_race", False)
        return form

    def add_view(self, request: HttpRequest, form_url: str = "", extra_context: Any = None) -> Any:
        try:
            return super().add_view(request, form_url, extra_context)
        except LinkExists:
            # A concurrent request created the same link after validation: show the form again
            # with the duplicate error (200), never a 409/500 page.
            setattr(request, "link_lost_race", True)  # noqa: B010
            return super().add_view(request, form_url, extra_context)

    def save_model(
        self, request: HttpRequest, obj: ParentChildLinkModel, form: Any, change: bool
    ) -> None:
        command = LinkParentCommand(obj.parent_id, obj.student_id, actor_id=_actor_id(request))
        obj.pk = container.link_parent().execute(command)  # the admin redirect needs the id

    def delete_model(self, request: HttpRequest, obj: ParentChildLinkModel) -> None:
        container.unlink_parent().execute(obj.pk, _actor_id(request))

    def delete_queryset(
        self, request: HttpRequest, queryset: QuerySet[ParentChildLinkModel]
    ) -> None:
        for link_id in queryset.values_list("pk", flat=True):
            container.unlink_parent().execute(link_id, _actor_id(request))


def _lockout_target(username: str | None) -> tuple[int | None, str]:
    """The attempt's account id, or a label that never stores what was typed (owner decision 2)."""
    if not username:
        return None, EMPTY_USERNAME
    user_id = UserModel.objects.filter(username=username).values_list("pk", flat=True).first()
    if user_id is not None:
        return user_id, username
    return None, f"{UNKNOWN_PREFIX}{username_fingerprint(username)}"


@admin.register(AccessAttempt, site=platform_admin_site)
class AccessAttemptAdmin(AttemptAdminBase):
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

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
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

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False
