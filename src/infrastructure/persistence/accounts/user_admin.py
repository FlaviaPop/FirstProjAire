"""Account administration: CRUD, last-admin protection, and audit logging."""

from typing import TYPE_CHECKING, Any

from django.contrib import admin, messages
from django.contrib.admin.actions import delete_selected as django_delete_selected
from django.contrib.admin.utils import unquote
from django.contrib.auth.admin import UserAdmin
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from infrastructure.persistence.accounts.admin_forms import (
    LAST_ADMIN,
    PlatformUserChangeForm,
    PlatformUserCreationForm,
    is_last_active_admin,
    leaves_no_active_admin,
)
from infrastructure.persistence.accounts.admin_site import (
    _audit,
    _password_hash,
    platform_admin_site,
)
from infrastructure.persistence.accounts.models import UserModel

if TYPE_CHECKING:  # django-stubs generics; the runtime classes are not subscriptable
    from django.forms import ModelForm

    UserAdminBase = UserAdmin[UserModel]
else:
    UserAdminBase = UserAdmin

DELETE_SELECTED_LABEL = django_delete_selected.short_description  # type: ignore[attr-defined]


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
