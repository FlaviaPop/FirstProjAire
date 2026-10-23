"""The platform admin site's access policy and shared audit helpers."""

from collections.abc import Callable, Iterable
from functools import wraps
from typing import Any, TypeVar, cast

from django.contrib import admin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseBase, HttpResponseRedirect
from django.shortcuts import resolve_url
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from infrastructure import container
from infrastructure.persistence.accounts.models import UserModel

ViewT = TypeVar("ViewT", bound=Callable[..., HttpResponseBase])

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


def _actor_id(request: HttpRequest) -> int:
    # Admin views only run for a signed-in Admin (PlatformAdminSite.admin_view): never None.
    return cast("int", request.user.pk)


def _password_hash(user_id: int) -> str:
    return UserModel.objects.filter(pk=user_id).values_list("password", flat=True).first() or ""


def _audit(action: str, request: HttpRequest, user: Any, fields: Iterable[str] = ()) -> None:
    container.audit_account_change().execute(
        action, _actor_id(request), user.pk, user.get_username(), fields
    )


platform_admin_site = PlatformAdminSite(name="admin")
