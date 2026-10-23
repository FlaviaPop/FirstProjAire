"""Parent-child link administration through the application use cases."""

from typing import TYPE_CHECKING, Any, cast

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from application.accounts.link_parent import LinkExists, LinkParentCommand
from infrastructure import container
from infrastructure.persistence.accounts.admin_forms import ParentChildLinkForm
from infrastructure.persistence.accounts.admin_site import _actor_id, platform_admin_site
from infrastructure.persistence.accounts.models import ParentChildLinkModel

if TYPE_CHECKING:  # django-stubs generics; the runtime classes are not subscriptable
    ParentLinkAdminBase = admin.ModelAdmin[ParentChildLinkModel]
else:
    ParentLinkAdminBase = admin.ModelAdmin


@admin.register(ParentChildLinkModel, site=platform_admin_site)
class ParentChildLinkAdmin(ParentLinkAdminBase):
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
